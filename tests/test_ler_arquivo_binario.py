import pytest

from hrx_code import config
from hrx_code import ferramentas


@pytest.fixture
def projeto(tmp_path, monkeypatch):
    raiz = tmp_path / "projeto"
    raiz.mkdir()
    monkeypatch.setattr(config, "REPO", str(raiz))
    return raiz


@pytest.mark.parametrize(
    ("nome", "conteudo", "tipo"),
    [
        ("imagem.dat", b"\x89PNG\r\n\x1a\nresto", "PNG"),
        ("documento.dat", b"%PDF-1.7\nresto", "PDF"),
        ("arquivo.dat", b"PK\x03\x04resto", "ZIP/container"),
        ("programa.dat", b"\x7fELFresto", "ELF"),
    ],
)
def test_reconhece_assinaturas_binarias(projeto, nome, conteudo, tipo):
    (projeto / nome).write_bytes(conteudo)

    resultado = ferramentas.ler_arquivo(nome)

    assert resultado == (
        f"ERRO: arquivo binário ({len(conteudo)} bytes, tipo detectado: {tipo}). "
        "Use ferramentas específicas se precisar do conteúdo."
    )


def test_le_texto_utf8_acentuado_normalmente(projeto):
    (projeto / "portugues.txt").write_text(
        "ação, coração, informação e café\n", encoding="utf-8"
    )

    resultado = ferramentas.ler_arquivo("portugues.txt")

    assert "1\tação, coração, informação e café" in resultado
    assert "arquivo binário" not in resultado


def test_um_unico_nul_classifica_como_binario(projeto):
    # Decisão deliberada: qualquer NUL na amostra é evidência suficiente.
    conteudo = b"texto quase normal\x00com um unico NUL"
    (projeto / "dados.bin").write_bytes(conteudo)

    resultado = ferramentas.ler_arquivo("dados.bin")

    assert resultado.startswith(
        f"ERRO: arquivo binário ({len(conteudo)} bytes, tipo detectado: BIN)"
    )


def test_controles_acima_de_trinta_por_cento_indicam_binario(projeto):
    conteudo = b"abcde\x01\x02\x03\x04"
    (projeto / "sem_extensao").write_bytes(conteudo)

    resultado = ferramentas.ler_arquivo("sem_extensao")

    assert resultado.startswith(
        f"ERRO: arquivo binário ({len(conteudo)} bytes, "
        "tipo detectado: desconhecido)"
    )
