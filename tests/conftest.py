"""Configuração comum dos testes.

Todos os testes rodam contra a base pequena de ``tests/fixtures`` — nada de
rede e nada da base real. O app lê ``COLA_DATA_DIR`` na hora de executar o
script, então basta apontar a variável antes de cada teste.
"""

import base64
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

FIXTURE_DATA_DIR = Path(__file__).resolve().parent / "fixtures" / "data"
DAMAGED_DATA_DIR = Path(__file__).resolve().parent / "fixtures" / "danificada"
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(autouse=True)
def cola_data_dir(monkeypatch):
    """Faz o app carregar a fixture em vez da base real."""
    monkeypatch.setenv("COLA_DATA_DIR", str(FIXTURE_DATA_DIR))


def iniciar() -> AppTest:
    """Executa o app inteiro e falha se algo explodir."""
    at = AppTest.from_file(str(APP_PATH), default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    return at


def pesquisar(at: AppTest, cargo: str, consulta: str) -> AppTest:
    """Digita uma consulta no campo de busca de um cargo."""
    rotulo = f"Pesquisar {cargo} por nome ou número"
    campo = next(w for w in at.text_input if w.label == rotulo)
    campo.set_value(consulta).run()
    assert not at.exception, at.exception
    return at


def selecionar_primeiro(at: AppTest) -> AppTest:
    """Clica no primeiro resultado de busca."""
    botoes = [b for b in at.button if b.label == "Selecionar"]
    assert botoes, "nenhum resultado de busca para selecionar"
    botoes[0].click().run()
    assert not at.exception, at.exception
    return at


def _valor(elemento) -> str:
    valor = getattr(elemento, "value", elemento)
    return valor if isinstance(valor, str) else str(valor)


def _blocos(at: AppTest, tipo: str) -> list[str]:
    try:
        return [_valor(b) for b in at.get(tipo)]
    except (KeyError, ValueError, AttributeError):
        return []


def markdowns(at: AppTest) -> str:
    """Todo o HTML emitido por ``st.markdown`` (resultados e revisão)."""
    return "\n".join(_valor(m) for m in at.markdown)


def html_bruto(at: AppTest) -> str:
    """Todo o conteúdo de ``st.html`` (botão da prévia de impressão)."""
    return "\n".join(_blocos(at, "html"))


# A folha de impressão viaja para a aba nova em base64 dentro de um script.
_DOC_B64_PATTERN = re.compile(r'const COLA_DOC_B64 = "([A-Za-z0-9+/=]+)"')


def folha(at: AppTest) -> str:
    """O documento HTML da folha que a aba nova vai imprimir."""
    for bloco in _blocos(at, "html"):
        match = _DOC_B64_PATTERN.search(_valor(bloco))

        if match:
            return base64.b64decode(match.group(1)).decode("utf-8")

    return markdowns(at)
