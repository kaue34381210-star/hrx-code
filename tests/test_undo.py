import json
import os
import stat
from unittest.mock import Mock

import pytest

from hrx_code import agente
from hrx_code import config
from hrx_code import ferramentas
from hrx_code import permissao
from hrx_code import undo


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    repo = tmp_path / "projeto"
    dados = tmp_path / "dados"
    repo.mkdir()
    monkeypatch.setattr(config, "REPO", str(repo))
    monkeypatch.setattr(config, "DADOS", str(dados))
    permissao.usar(None)
    yield repo, dados
    permissao.usar(None)


def _autorizar(politica, ferramenta, caminho=None):
    args = {"caminho": caminho} if caminho else {}
    comando = permissao.comando_de(ferramenta, args)
    politica.liberar(comando)
    return comando


def _escrever(politica, caminho, conteudo):
    _autorizar(politica, "escrever_arquivo", caminho)
    return ferramentas.escrever_arquivo(caminho, conteudo)


def _desfazer(politica, caminho=None):
    _autorizar(politica, "desfazer_ultima", caminho)
    return undo.desfazer_ultima(caminho)


def _registros(dados):
    return json.loads((dados / "undo" / "operacoes.json").read_text("utf-8"))


def test_snapshot_binario_preserva_original_e_undo_restaura_byte_a_byte(ambiente):
    repo, dados = ambiente
    arquivo = repo / "binario.dat"
    original = b"\x00\xff\x80texto\r\n"
    arquivo.write_bytes(original)
    arquivo.chmod(0o640)
    politica = permissao.Politica()
    permissao.usar(politica)

    assert _escrever(politica, "binario.dat", "novo").startswith("OK:")
    registro = _registros(dados)[0]
    snapshot = dados / "undo" / registro["snapshot"]

    assert snapshot.read_bytes() == original
    assert registro["hash_antes"] and registro["hash_depois"]
    assert registro["caminho"] == str(arquivo.resolve())
    assert registro["ferramenta"] == "escrever_arquivo"
    assert stat.S_IMODE((dados / "undo").stat().st_mode) == 0o700
    assert stat.S_IMODE(snapshot.stat().st_mode) == 0o600
    assert stat.S_IMODE((dados / "undo" / "operacoes.json").stat().st_mode) == 0o600

    assert "restaurado" in _desfazer(politica)
    assert arquivo.read_bytes() == original
    assert stat.S_IMODE(arquivo.stat().st_mode) == 0o640


def test_undo_de_arquivo_criado_remove_e_nao_pode_repetir(ambiente):
    repo, _ = ambiente
    politica = permissao.Politica()
    permissao.usar(politica)

    _escrever(politica, "novo.txt", "conteúdo")
    assert "removido" in _desfazer(politica)
    assert not (repo / "novo.txt").exists()

    repetido = _desfazer(politica)
    assert "nenhuma operação disponível" in repetido


@pytest.mark.parametrize("ferramenta", ["editar_arquivo", "aplicar_patch"])
def test_edicao_e_patch_tambem_entram_no_historico(ambiente, ferramenta):
    repo, dados = ambiente
    arquivo = repo / "alvo.txt"
    arquivo.write_text("antes\n", encoding="utf-8")
    politica = permissao.Politica()
    permissao.usar(politica)
    _autorizar(politica, ferramenta, "alvo.txt")
    if ferramenta == "editar_arquivo":
        resultado = ferramentas.editar_arquivo("alvo.txt", "antes", "depois")
    else:
        resultado = ferramentas.aplicar_patch(
            "alvo.txt", "@@ -1 +1 @@\n-antes\n+depois\n"
        )

    assert resultado.startswith("OK:")
    assert _registros(dados)[0]["ferramenta"] == ferramenta
    assert "restaurado" in _desfazer(politica, "alvo.txt")
    assert arquivo.read_text(encoding="utf-8") == "antes\n"


def test_caminho_opcional_seleciona_a_operacao_mais_recente_daquele_arquivo(
        ambiente):
    repo, _ = ambiente
    politica = permissao.Politica()
    permissao.usar(politica)
    _escrever(politica, "a.txt", "a")
    _escrever(politica, "b.txt", "b")

    assert "a.txt" in _desfazer(politica, "a.txt")
    assert not (repo / "a.txt").exists()
    assert (repo / "b.txt").exists()


@pytest.mark.parametrize("mudanca", ["alterar", "remover"])
def test_conflito_externo_nao_consumido(ambiente, mudanca):
    repo, dados = ambiente
    arquivo = repo / "alvo.txt"
    arquivo.write_text("antes", encoding="utf-8")
    politica = permissao.Politica()
    permissao.usar(politica)
    _escrever(politica, "alvo.txt", "depois")
    if mudanca == "alterar":
        arquivo.write_text("externo", encoding="utf-8")
    else:
        arquivo.unlink()

    resultado = _desfazer(politica)

    assert "conflito de undo" in resultado
    assert _registros(dados)[0]["desfeito"] is False
    assert "alvo.txt" in undo.listar_undo()


def test_falha_de_escrita_reverte_e_nao_publica_transacao(ambiente, monkeypatch):
    repo, _ = ambiente
    arquivo = repo / "alvo.txt"
    arquivo.write_bytes(b"original")
    politica = permissao.Politica()
    permissao.usar(politica)
    _autorizar(politica, "escrever_arquivo", "alvo.txt")
    monkeypatch.setattr(
        undo, "confirmar_transacao", Mock(side_effect=OSError("log indisponível"))
    )

    with pytest.raises(OSError, match="log indisponível"):
        ferramentas.escrever_arquivo("alvo.txt", "alterado")

    assert arquivo.read_bytes() == b"original"
    assert undo.listar_undo() == "(nenhuma operação disponível para desfazer)"


def test_arquivo_maior_que_orcamento_recusa_mutacao(ambiente, monkeypatch):
    repo, _ = ambiente
    arquivo = repo / "grande.txt"
    arquivo.write_bytes(b"1234")
    monkeypatch.setattr(undo, "MAX_BYTES", 3)
    politica = permissao.Politica()
    permissao.usar(politica)
    _autorizar(politica, "escrever_arquivo", "grande.txt")

    with pytest.raises(undo.UndoError, match="mutação recusada"):
        ferramentas.escrever_arquivo("grande.txt", "x")

    assert arquivo.read_bytes() == b"1234"
    assert undo.listar_undo() == "(nenhuma operação disponível para desfazer)"


def test_rotacao_mantem_as_50_operacoes_mais_recentes(ambiente):
    _, dados = ambiente
    politica = permissao.Politica()
    permissao.usar(politica)
    for numero in range(60):
        _escrever(politica, "alvo.txt", str(numero))

    registros = _registros(dados)

    assert len(registros) == 50
    assert len(list((dados / "undo").glob("*.bin"))) == 50


def test_undo_e_sempre_vermelho_inclusive_auto_e_sempre_permitir(ambiente):
    politica = permissao.Politica(modo="auto")
    args = {"caminho": "alvo.txt"}
    comando = permissao.comando_de("desfazer_ultima", args)
    politica.liberar_sempre(comando)

    nivel, motivo = politica.classificar(
        comando, ferramenta="desfazer_ultima", args=args
    )

    assert nivel == "vermelho"
    assert "nunca é rebaixável" in motivo


def test_undo_exige_autorizacao_de_uso_unico(ambiente):
    repo, _ = ambiente
    politica = permissao.Politica()
    permissao.usar(politica)
    _escrever(politica, "novo.txt", "x")

    negado = undo.desfazer_ultima()
    permitido = _desfazer(politica)
    reutilizado = undo.desfazer_ultima()

    assert "não passou" in negado
    assert permitido.startswith("OK:")
    assert "não passou" in reutilizado
    assert not (repo / "novo.txt").exists()


def test_comando_repl_undo_usa_gate_e_trinco(ambiente, monkeypatch, capsys):
    repo, _ = ambiente
    politica = permissao.Politica(modo="auto")
    permissao.usar(politica)
    _escrever(politica, "novo.txt", "x")
    perguntar = Mock(return_value="sim")
    monkeypatch.setattr(agente, "_perguntar", perguntar)

    consumido = agente._comando_especial(
        None, None, politica, [], "/undo novo.txt"
    )

    assert consumido is True
    assert not (repo / "novo.txt").exists()
    assert perguntar.call_count == 1
    assert "ALTO RISCO" in capsys.readouterr().out


def test_comando_repl_undo_respeita_dry_run(ambiente, monkeypatch):
    politica = permissao.Politica(dry_run=True)
    executar = Mock(side_effect=AssertionError("undo executado em dry-run"))
    monkeypatch.setattr(ferramentas, "executar", executar)

    assert agente._comando_especial(None, None, politica, [], "/undo") is True
    executar.assert_not_called()


def test_buscar_docs_nunca_indexa_backups_de_undo(ambiente):
    _, dados = ambiente
    (dados / "undo").mkdir(parents=True)
    (dados / "undo" / "segredo.json").write_text(
        '{"token": "agulhasecreta"}', encoding="utf-8"
    )
    (dados / "nota.md").write_text("agulhapublica", encoding="utf-8")

    assert "agulhapublica" in ferramentas.buscar_docs("agulhapublica")
    assert "Nada encontrado" in ferramentas.buscar_docs("agulhasecreta")
