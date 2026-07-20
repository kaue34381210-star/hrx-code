import pytest

from hrx_code import agente


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ('{"acao": "responder", "texto": "ok"}',
         {"acao": "responder", "texto": "ok"}),
        ('prefixo {"acao": "usar", "args": {"x": 1}} sufixo',
         {"acao": "usar", "args": {"x": 1}}),
        ('```json\n{"acao": "responder"}\n```', {"acao": "responder"}),
    ],
)
def test_extrair_json_aceita_objeto_com_texto_ao_redor(texto, esperado):
    assert agente.extrair_json(texto) == esperado


@pytest.mark.parametrize("texto", ["sem json", "prefixo {invalido} sufixo", ""])
def test_extrair_json_invalido_retorna_none(texto):
    assert agente.extrair_json(texto) is None
