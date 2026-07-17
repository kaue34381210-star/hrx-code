import os

import pytest

from hrx_code import config
from hrx_code import ferramentas


@pytest.fixture
def projeto(tmp_path, monkeypatch):
    raiz = tmp_path / "projeto"
    dados = tmp_path / "dados"
    raiz.mkdir()
    dados.mkdir()
    monkeypatch.setattr(config, "REPO", str(raiz))
    monkeypatch.setattr(config, "DADOS", str(dados))
    return raiz, dados


def _arquivo(raiz, caminho, conteudo="MARCADOR\n"):
    arquivo = raiz / caminho
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(conteudo, encoding="utf-8")


def test_lista_e_busca_respeitam_gitignore_com_negacao(projeto):
    raiz, _ = projeto
    (raiz / ".gitignore").write_text(
        "*.log\n!keep.log\ndist/\n.env\n", encoding="utf-8"
    )
    _arquivo(raiz, "app.py")
    _arquivo(raiz, "debug.log")
    _arquivo(raiz, "keep.log")
    _arquivo(raiz, ".env")
    _arquivo(raiz, "dist/bundle.js")

    arvore = ferramentas.listar_diretorio(".", recursivo=True)
    busca = ferramentas.buscar_codigo("MARCADOR")

    assert "app.py" in arvore
    assert "keep.log" in arvore
    assert "debug.log" not in arvore
    assert ".env" not in arvore
    assert "dist/" not in arvore
    assert "app.py:1" in busca
    assert "keep.log:1" in busca
    assert "debug.log" not in busca
    assert "bundle.js" not in busca


def test_respeitar_gitignore_false_inclui_ignorados_mas_nao_internals(projeto):
    raiz, _ = projeto
    (raiz / ".gitignore").write_text(
        "*.log\ndist/\n.env\n", encoding="utf-8"
    )
    _arquivo(raiz, "debug.log")
    _arquivo(raiz, ".env")
    _arquivo(raiz, "dist/bundle.js")
    _arquivo(raiz, ".git/config")
    _arquivo(raiz, "node_modules/pacote/index.js")

    arvore = ferramentas.listar_diretorio(
        ".", recursivo=True, respeitar_gitignore=False
    )
    busca = ferramentas.buscar_codigo(
        "MARCADOR", respeitar_gitignore=False
    )

    assert "debug.log" in arvore
    assert ".env" in arvore
    assert "dist/" in arvore
    assert "bundle.js" in arvore
    assert ".git/" not in arvore
    assert "node_modules/" not in arvore
    assert "debug.log:1" in busca
    assert "dist/bundle.js:1" in busca
    assert ".git/config" not in busca
    assert "node_modules" not in busca


def test_sem_gitignore_mantem_fallback_desligavel(projeto):
    raiz, _ = projeto
    _arquivo(raiz, "src/app.py")
    _arquivo(raiz, "build/gerado.py")
    _arquivo(raiz, "dist/bundle.js")

    padrao = ferramentas.listar_diretorio(".", recursivo=True)
    completo = ferramentas.listar_diretorio(
        ".", recursivo=True, respeitar_gitignore=False
    )

    assert "src/" in padrao
    assert "build/" not in padrao
    assert "dist/" not in padrao
    assert "build/" in completo
    assert "dist/" in completo


def test_cache_invalida_ao_editar_gitignore(projeto):
    raiz, _ = projeto
    regras = raiz / ".gitignore"
    regras.write_text("*.log\n", encoding="utf-8")
    _arquivo(raiz, "debug.log")
    _arquivo(raiz, "dados.tmp")
    assert "debug.log" not in ferramentas.listar_diretorio(".")
    assert "dados.tmp" in ferramentas.listar_diretorio(".")

    regras.write_text("*.tmp\n", encoding="utf-8")
    stat = regras.stat()
    os.utime(regras, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1))

    resultado = ferramentas.listar_diretorio(".")
    assert "debug.log" in resultado
    assert "dados.tmp" not in resultado


def test_hrxignore_privado_complementa_gitignore(projeto):
    raiz, dados = projeto
    (raiz / ".gitignore").write_text("*.log\n", encoding="utf-8")
    (dados / ".hrxignore").write_text("secreto.txt\n", encoding="utf-8")
    _arquivo(raiz, "debug.log")
    _arquivo(raiz, "secreto.txt")
    _arquivo(raiz, "publico.txt")

    resultado = ferramentas.listar_diretorio(".")

    assert "debug.log" not in resultado
    assert "secreto.txt" not in resultado
    assert "publico.txt" in resultado


@pytest.mark.parametrize("valor", [None, 0, 1, "false", []])
def test_ferramentas_validam_respeitar_gitignore(projeto, valor):
    erro_lista = ferramentas.listar_diretorio(
        ".", respeitar_gitignore=valor
    )
    erro_busca = ferramentas.buscar_codigo(
        "x", respeitar_gitignore=valor
    )

    esperado = "ERRO: respeitar_gitignore deve ser booleano (true ou false)"
    assert erro_lista == esperado
    assert erro_busca == esperado
