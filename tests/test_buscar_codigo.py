import pytest

from hrx_code import config
from hrx_code import ferramentas


@pytest.fixture
def projeto(tmp_path, monkeypatch):
    raiz = tmp_path / "projeto"
    raiz.mkdir()
    monkeypatch.setattr(config, "REPO", str(raiz))
    return raiz


def test_busca_inclui_duas_linhas_de_contexto(projeto):
    (projeto / "app.py").write_text(
        "um\ndois\ntres\nACHADO\ncinco\nseis\nsete\n", encoding="utf-8"
    )

    resultado = ferramentas.buscar_codigo("ACHADO", contexto=2)

    assert resultado.splitlines() == [
        "app.py-2- dois",
        "app.py-3- tres",
        "app.py:4: ACHADO",
        "app.py-5- cinco",
        "app.py-6- seis",
    ]


def test_busca_agrupa_contextos_sobrepostos_e_contiguos(projeto):
    linhas = [f"linha {numero}" for numero in range(1, 13)]
    linhas[2] = "ACHADO 3"
    linhas[7] = "ACHADO 8"
    (projeto / "app.py").write_text("\n".join(linhas), encoding="utf-8")

    resultado = ferramentas.buscar_codigo("ACHADO", contexto=2)

    assert "\n--\n" not in resultado
    assert resultado.count("app.py-5- linha 5") == 1
    assert resultado.count("app.py-6- linha 6") == 1
    assert "app.py:3: ACHADO 3" in resultado
    assert "app.py:8: ACHADO 8" in resultado


def test_busca_separa_grupos_distantes(projeto):
    linhas = [f"linha {numero}" for numero in range(1, 16)]
    linhas[1] = "ACHADO 2"
    linhas[12] = "ACHADO 13"
    (projeto / "app.py").write_text("\n".join(linhas), encoding="utf-8")

    resultado = ferramentas.buscar_codigo("ACHADO", contexto=1)

    assert resultado.count("\n--\n") == 1


def test_limite_conta_matches_e_mantem_contexto_em_multiplos_arquivos(projeto):
    (projeto / "a.txt").write_text(
        "\n".join(["ACHADO"] * 99), encoding="utf-8"
    )
    (projeto / "b.txt").write_text(
        "\n".join(["ACHADO"] * 502), encoding="utf-8"
    )

    resultado = ferramentas.buscar_codigo("ACHADO", contexto=1)
    matches_exibidos = [
        linha for linha in resultado.splitlines()
        if linha.startswith(("a.txt:", "b.txt:"))
    ]

    assert len(matches_exibidos) == 100
    assert "b.txt:1: ACHADO" in resultado
    assert "b.txt-2- ACHADO" in resultado
    assert "\n--\n" in resultado
    assert "ao menos 401 resultados omitidos" in resultado
    assert "500+ resultados no total" in resultado


@pytest.mark.parametrize("contexto", [True, False, "2", 2.0, None])
def test_busca_rejeita_contexto_que_nao_seja_inteiro(projeto, contexto):
    resultado = ferramentas.buscar_codigo("x", contexto=contexto)

    assert resultado == "ERRO: contexto deve ser um inteiro maior ou igual a 0"


def test_busca_rejeita_contexto_negativo(projeto):
    resultado = ferramentas.buscar_codigo("x", contexto=-1)

    assert resultado == "ERRO: contexto deve ser maior ou igual a 0"
