"""Testes de ponta a ponta do Cola Eleitoral 2026 (Streamlit AppTest)."""

from conftest import (
    DAMAGED_DATA_DIR,
    folha,
    iniciar,
    markdowns,
    pesquisar,
    selecionar_primeiro,
)

FLUXO_COMPLETO = [
    ("Deputado Federal", "1302"),
    ("Deputado Estadual", "13001"),
    ("Senador — 1ª vaga", "130"),
    ("Senador — 2ª vaga", "455"),
    ("Governador", "12"),
    ("Presidente", "13"),
]


def botao(at, rotulo):
    return next(b for b in at.button if b.label == rotulo)


def test_abre_na_montagem():
    at = iniciar()

    assert at.radio[0].value == "1. Montar cola"
    assert any("0 de 6 posições preenchidas" in s.value for s in at.success)
    assert any("Candidaturas carregadas: 10" in c.value for c in at.caption)


def test_presidente_lista_apenas_presidentes():
    """Busca por número e por nome não pode vazar o vice-presidente."""
    at = iniciar()

    pesquisar(at, "Presidente", "13")
    md = markdowns(at)
    assert "PRESIDENTE TESTE" in md
    assert "PRESIDENTE VICE" not in md
    assert "VICE-PRESIDENTE" not in md

    pesquisar(at, "Presidente", "PRESIDENTE")
    md = markdowns(at)
    assert "PRESIDENTE TESTE" in md
    assert "PRESIDENTE VICE" not in md
    assert any("1 resultado(s)" in c.value for c in at.caption)


def test_governador_nao_lista_vice():
    at = iniciar()

    pesquisar(at, "Governador", "12")
    md = markdowns(at)
    assert "GUILHERME GOVERNADOR" in md
    assert "GOVERNADOR VICE" not in md

    pesquisar(at, "Governador", "GOVERNADOR")
    md = markdowns(at)
    assert "GUILHERME GOVERNADOR" in md
    assert "GOVERNADOR VICE" not in md


def test_busca_sem_acento_mostra_nome_acentuado():
    """Normalizar a busca não pode destruir o nome exibido."""
    at = iniciar()

    pesquisar(at, "Deputado Federal", "JOAO")
    md = markdowns(at)
    assert "JOÃO DA SILVA" in md
    assert any("1 resultado(s)" in c.value for c in at.caption)

    pesquisar(at, "Deputado Estadual", "MARCIA")
    md = markdowns(at)
    assert "MÁRCIA APARECIDA" in md


def test_cartao_escapa_html_e_esconde_placeholder():
    at = iniciar()

    pesquisar(at, "Deputado Federal", "1302")
    md = markdowns(at)
    assert "ANA &amp; BIA &lt;NORTE&gt;" in md
    assert "<NORTE>" not in md
    assert "· DEFERIDO" in md

    pesquisar(at, "Deputado Federal", "1301")
    md = markdowns(at)
    assert "JOÃO DA SILVA" in md
    assert " · #NE" not in md
    assert "data:image/jpeg;base64," in md


def test_senador_repetido_bloqueia_impressao():
    at = iniciar()

    pesquisar(at, "Senador — 1ª vaga", "130")
    selecionar_primeiro(at)

    pesquisar(at, "Senador — 2ª vaga", "130")
    selecionar_primeiro(at)

    assert any("vagas do Senado" in e.value for e in at.error)

    at.radio[0].set_value("2. Revisar").run()
    assert not at.exception, at.exception

    assert any("vagas do Senado" in e.value for e in at.error)
    assert botao(at, "Continuar para impressão").disabled is True


def test_cola_completa_vai_para_impressao():
    at = iniciar()

    for cargo, consulta in FLUXO_COMPLETO:
        pesquisar(at, cargo, consulta)
        selecionar_primeiro(at)

    assert any("6 de 6 posições preenchidas" in s.value for s in at.success)

    at.radio[0].set_value("2. Revisar").run()
    assert not at.exception, at.exception

    revisao = markdowns(at)
    assert "MÁRCIA APARECIDA" in revisao
    assert "ANTÔNIO SENADOR" in revisao
    assert "data:image/jpeg;base64," in revisao

    botao_continuar = botao(at, "Continuar para impressão")
    assert botao_continuar.disabled is False

    botao_continuar.click().run()
    assert not at.exception, at.exception

    assert at.radio[0].value == "3. Imprimir"

    impressao = folha(at)
    assert impressao.count('class="print-card"') == 4
    assert impressao.count('class="print-item"') == 24
    assert impressao.count("data:image/jpeg;base64,") == 4
    assert "SÃO PAULO · 1º TURNO" in impressao
    assert "ANA &amp; BIA &lt;NORTE&gt;" in impressao
    assert "MÁRCIA APARECIDA" in impressao
    assert " · #NE" not in impressao


def test_cola_incompleta_pode_ser_impressa():
    at = iniciar()

    pesquisar(at, "Deputado Federal", "1301")
    selecionar_primeiro(at)

    at.radio[0].set_value("2. Revisar").run()
    assert not at.exception, at.exception

    assert any("cola incompleta" in i.value for i in at.info)

    botao_continuar = botao(at, "Continuar para impressão")
    assert botao_continuar.disabled is False

    botao_continuar.click().run()
    assert at.radio[0].value == "3. Imprimir"

    impressao = folha(at)
    assert impressao.count('class="print-card"') == 4
    assert impressao.count("Não preenchido") == 20


def test_aviso_quando_base_esta_sem_acentos(monkeypatch):
    monkeypatch.setenv("COLA_DATA_DIR", str(DAMAGED_DATA_DIR))

    at = iniciar()
    assert any("está sem acentos" in w.value for w in at.warning)
