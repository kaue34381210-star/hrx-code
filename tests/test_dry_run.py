import json
from unittest.mock import Mock

from hrx_code import agente
from hrx_code import ferramentas
from hrx_code import permissao


def _motor_com_acoes(acoes):
    respostas = iter(acoes)

    def chamar(_mensagens):
        return json.dumps(next(respostas), ensure_ascii=False)

    return chamar


def test_dry_run_nao_aprova_nem_executa_ferramenta_sensivel(monkeypatch):
    executar = Mock(side_effect=AssertionError("ferramenta sensível foi executada"))
    aprovar = Mock(side_effect=AssertionError("dry-run pediu aprovação"))
    monkeypatch.setattr(ferramentas, "executar", executar)
    monkeypatch.setattr(agente, "_aprovar_comando", aprovar)
    motor = _motor_com_acoes([
        {
            "pensamento": "testar",
            "ferramenta": "rodar_comando",
            "args": {"comando": "echo ok"},
        },
        {"pensamento": "finalizar", "resposta": "Simulação concluída."},
    ])
    historico = []

    resposta = agente.rodar(
        motor,
        permissao.Politica(modo="auto", dry_run=True),
        historico,
        "simule o comando",
    )

    assert resposta == "Simulação concluída."
    executar.assert_not_called()
    aprovar.assert_not_called()
    assert "DRY-RUN:" in historico[-2]["content"]
    assert "não foi executada" in historico[-2]["content"]


def test_dry_run_mantem_ferramentas_de_leitura_ativas(monkeypatch):
    executar = Mock(return_value="arquivo.py")
    monkeypatch.setattr(ferramentas, "executar", executar)
    motor = _motor_com_acoes([
        {
            "pensamento": "listar",
            "ferramenta": "listar_diretorio",
            "args": {"caminho": "."},
        },
        {"pensamento": "finalizar", "resposta": "Leitura concluída."},
    ])

    resposta = agente.rodar(
        motor,
        permissao.Politica(dry_run=True),
        [],
        "liste os arquivos",
    )

    assert resposta == "Leitura concluída."
    executar.assert_called_once_with("listar_diretorio", {"caminho": "."})


def test_comando_especial_alterna_dry_run(capsys):
    politica = permissao.Politica()

    assert agente._comando_especial(None, None, politica, [], "/dry-run on") is True
    assert politica.dry_run is True
    assert agente._comando_especial(None, None, politica, [], "/simular off") is True
    assert politica.dry_run is False

    saida = capsys.readouterr().out
    assert "dry-run ativado" in saida
    assert "dry-run desativado" in saida
