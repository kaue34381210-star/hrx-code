"""Teste do adaptador HTTP do motor local, sem iniciar um modelo real."""
from unittest.mock import Mock, patch

import config
import local


def testar_chamada():
    resposta = Mock()
    resposta.status_code = 200
    resposta.json.return_value = {"choices": [{"message": {"content": "  olá  "}}]}
    with patch("local.requests.post", return_value=resposta) as post:
        texto, extra = local.chamar([{"role": "user", "content": "oi"}])
    assert (texto, extra) == ("olá", None)
    corpo = post.call_args.kwargs["json"]
    assert corpo["messages"] == [{"role": "user", "content": "oi"}]
    assert corpo["stream"] is False


def testar_disponibilidade():
    health = Mock(ok=True)
    with patch("local.requests.get", return_value=health):
        assert local.disponivel() is True


def testar_disponibilidade_url_customizada():
    health = Mock(ok=True)
    original = config.LOCAL_URL
    try:
        config.LOCAL_URL = "http://127.0.0.1:8080/chat/completions"
        with patch("local.requests.get", return_value=health) as get:
            assert local.disponivel() is True
        assert get.call_args.args[0] == "http://127.0.0.1:8080/health"
    finally:
        config.LOCAL_URL = original


if __name__ == "__main__":
    testar_chamada()
    testar_disponibilidade()
    testar_disponibilidade_url_customizada()
    print("✅ adaptador local funcionando")
