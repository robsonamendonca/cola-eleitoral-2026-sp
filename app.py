import base64
import html
import io
import os
import re
import unicodedata
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

APP_TITLE = "Cola Eleitoral 2026 SP"

# Datas, estado e rodada em um único lugar (PRD §41 e §42). Para um eventual
# segundo turno, muda-se apenas "round" para 2 e só os cargos com segunda
# volta programada entram na cola.
ELECTION_CONFIG = {
    "year": 2026,
    "first_round": "2026-10-04",
    "second_round": "2026-10-25",
    "state": "SP",
    "round": 1,
}

YEAR = ELECTION_CONFIG["year"]
UF = ELECTION_CONFIG["state"]
ROUND_LABEL = f'{ELECTION_CONFIG["round"]}º turno'

TSE_DATASET_URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/"
    "consulta_cand_2026.zip"
)

# ``COLA_DATA_DIR`` permite aos testes apontarem para uma base de fixture
# pequena em vez da pasta real de dados.
DATA_DIR = Path(
    os.environ.get("COLA_DATA_DIR")
    or Path(__file__).resolve().parent / "data"
)
LOCAL_CSV = DATA_DIR / "candidatos_2026.csv"

BALLOT_ORDER = [
    {
        "key": "deputado_federal",
        "label": "Deputado Federal",
        "cargo_terms": ["DEPUTADO FEDERAL"],
        "digits": 4,
        "uf": "SP",
        "rounds": [1],
    },
    {
        "key": "deputado_estadual",
        "label": "Deputado Estadual",
        "cargo_terms": ["DEPUTADO ESTADUAL"],
        "digits": 5,
        "uf": "SP",
        "rounds": [1],
    },
    {
        "key": "senador_1",
        "label": "Senador — 1ª vaga",
        "cargo_terms": ["SENADOR"],
        "digits": 3,
        "uf": "SP",
        "rounds": [1],
    },
    {
        "key": "senador_2",
        "label": "Senador — 2ª vaga",
        "cargo_terms": ["SENADOR"],
        "digits": 3,
        "uf": "SP",
        "rounds": [1],
    },
    {
        "key": "governador",
        "label": "Governador",
        "cargo_terms": ["GOVERNADOR"],
        "digits": 2,
        "uf": "SP",
        "rounds": [1, 2],
    },
    {
        "key": "presidente",
        "label": "Presidente",
        "cargo_terms": ["PRESIDENTE"],
        "digits": 2,
        "uf": "BR",
        "rounds": [1, 2],
    },
]

# Cargos ativos na rodada configurada (PRD §41): no segundo turno só entram
# os cargos submetidos à segunda volta.
BALLOT_ORDER_ACTIVE = [
    item
    for item in BALLOT_ORDER
    if ELECTION_CONFIG["round"] in item["rounds"]
]

COLUMN_ALIASES = {
    "uf": [
        "SG_UF",
        "UF",
    ],
    "cargo": [
        "DS_CARGO",
        "CARGO",
    ],
    "numero": [
        "NR_CANDIDATO",
        "NUMERO",
        "NUMERO_CANDIDATO",
    ],
    "nome": [
        "NM_URNA_CANDIDATO",
        "NOME_URNA",
        "NOME",
        "NM_CANDIDATO",
    ],
    "nome_completo": [
        "NM_CANDIDATO",
        "NOME_COMPLETO",
        "NOME",
    ],
    "partido": [
        "SG_PARTIDO",
        "PARTIDO",
    ],
    "situacao": [
        "DS_SITUACAO_CANDIDATURA",
        "SITUACAO",
    ],
    "sq_candidato": [
        "SQ_CANDIDATO",
        "SEQUENCIAL_CANDIDATO",
    ],
}

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🗳️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
<style>
    .block-container {
        max-width: 1050px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .app-title {
        text-align: center;
        margin-bottom: 0.2rem;
    }

    .app-subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 1.5rem;
    }

    .candidate-card {
        display: flex;
        gap: 12px;
        align-items: center;
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 12px 14px;
        margin: 7px 0;
        background: #fff;
    }

    .candidate-photo {
        flex-shrink: 0;
        width: 60px;
        height: 84px;
        object-fit: cover;
        border: 1px solid #ddd;
        border-radius: 8px;
        background: #f5f5f5;
    }

    .candidate-number {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: 0.08em;
    }

    .candidate-name {
        font-size: 1rem;
        font-weight: 700;
    }

    .candidate-meta {
        color: #666;
        font-size: 0.85rem;
    }

    .selected-card {
        border: 2px solid #111;
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0 18px 0;
        background: #fafafa;
    }

    .selected-number {
        font-size: 2.2rem;
        line-height: 1;
        font-weight: 900;
        letter-spacing: 0.08em;
    }

    .selected-head {
        display: flex;
        gap: 14px;
        align-items: center;
    }

    .selected-photo {
        flex-shrink: 0;
        width: 76px;
        height: 106px;
        object-fit: cover;
        border: 1px solid #ccc;
        border-radius: 8px;
        background: #f5f5f5;
    }

    .review-row {
        display: grid;
        grid-template-columns: 32px 44px 1fr auto;
        gap: 10px;
        align-items: center;
        border-bottom: 1px solid #ddd;
        padding: 10px 0;
    }

    .review-photo {
        display: block;
        width: 44px;
        height: 61px;
        object-fit: cover;
        border: 1px solid #ddd;
        border-radius: 6px;
        background: #f5f5f5;
    }

    .review-photo-empty {
        background: #f2f2f2;
        border-style: dashed;
    }

    .review-order {
        font-weight: 800;
        color: #666;
    }

    .review-cargo {
        font-size: 0.8rem;
        text-transform: uppercase;
        color: #666;
    }

    .review-name {
        font-weight: 700;
    }

    .review-number {
        font-size: 1.5rem;
        font-weight: 900;
        letter-spacing: 0.08em;
    }

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# UTILITÁRIOS
# ============================================================

def normalize_text(value: object) -> str:
    """Normaliza texto para comparação sem destruir o valor exibido."""
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def clean_number(value: object) -> str:
    """Converte número de candidato para texto preservando zeros à esquerda."""
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]

    digits = re.sub(r"\D", "", text)
    return digits


def find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    normalized = {
        normalize_text(column).replace(" ", "_"): column
        for column in df.columns
    }

    for alias in aliases:
        key = normalize_text(alias).replace(" ", "_")
        if key in normalized:
            return normalized[key]

    return None


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Converte as colunas do TSE para um modelo interno estável."""
    df = df.copy()

    rename_map = {}

    for target, aliases in COLUMN_ALIASES.items():
        source = find_column(df, aliases)
        if source:
            rename_map[source] = target

    df = df.rename(columns=rename_map)

    required = ["uf", "cargo", "numero", "nome", "partido"]

    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(
            "Colunas obrigatórias não encontradas: "
            + ", ".join(missing)
        )

    for column in [
        "uf",
        "cargo",
        "numero",
        "nome",
        "nome_completo",
        "partido",
        "situacao",
        "sq_candidato",
    ]:
        if column not in df.columns:
            df[column] = ""

    df["uf"] = df["uf"].fillna("").astype(str).str.strip().str.upper()
    df["cargo"] = df["cargo"].fillna("").astype(str).str.strip()
    df["numero"] = df["numero"].map(clean_number)
    df["nome"] = df["nome"].fillna("").astype(str).str.strip()
    df["nome_completo"] = df["nome_completo"].fillna("").astype(str).str.strip()
    df["partido"] = df["partido"].fillna("").astype(str).str.strip()
    df["situacao"] = df["situacao"].fillna("").astype(str).str.strip()

    df["cargo_norm"] = df["cargo"].map(normalize_text)
    df["nome_norm"] = df["nome"].map(normalize_text)
    df["nome_completo_norm"] = df["nome_completo"].map(normalize_text)
    df["partido_norm"] = df["partido"].map(normalize_text)

    df = df[df["numero"].str.len() > 0].copy()

    # Evita duplicações acidentais da mesma candidatura.
    duplicate_keys = ["uf", "cargo", "numero", "nome", "partido"]
    df = df.drop_duplicates(subset=duplicate_keys, keep="first")

    return df.reset_index(drop=True)


def read_csv_bytes(raw: bytes) -> pd.DataFrame:
    """Lê CSV oficial/local tentando os formatos mais comuns do TSE.

    O UTF-8 precisa ser testado antes do latin-1: o latin-1 decodifica
    qualquer byte e nunca falha, então tentá-lo primeiro fazia um CSV UTF-8
    ser lido com os acentos trocados (``Ã§`` no lugar de ``ç``).
    """
    attempts = [
        {"sep": ";", "encoding": "utf-8-sig"},
        {"sep": ";", "encoding": "latin-1"},
        {"sep": ",", "encoding": "utf-8-sig"},
        {"sep": ",", "encoding": "latin-1"},
    ]

    last_error = None

    for options in attempts:
        try:
            frame = pd.read_csv(
                io.BytesIO(raw),
                dtype=str,
                low_memory=False,
                **options,
            )

            if len(frame.columns) > 1:
                return normalize_dataframe(frame)

        except Exception as exc:
            last_error = exc

    raise ValueError(
        f"Não foi possível interpretar o CSV. Erro: {last_error}"
    )


def read_local_csv(path: Path) -> pd.DataFrame:
    return read_csv_bytes(path.read_bytes())


def download_tse_zip() -> bytes:
    request = Request(
        TSE_DATASET_URL,
        headers={
            "User-Agent": (
                "ColaEleitoral2026SP/1.0 "
                "(aplicacao educacional; fonte TSE)"
            )
        },
    )

    with urlopen(request, timeout=60) as response:
        return response.read()


def select_csv_names(names: list[str], ufs: list[str]) -> dict[str, str]:
    """Seleciona no ZIP do TSE o CSV oficial de cada UF informada."""
    selection: dict[str, str] = {}

    for uf in ufs:
        suffix = f"_{uf}.csv".lower()

        for name in sorted(names):
            lowered = name.lower()

            if not lowered.endswith(".csv"):
                continue

            filename = Path(lowered).name

            if filename.startswith(
                f"consulta_cand_{YEAR}_{uf}".lower()
            ) or filename.endswith(suffix):
                selection[uf] = name
                break

    return selection


def extract_csvs(zip_bytes: bytes, ufs: list[str]) -> list[bytes]:
    """Extrai o CSV oficial de cada UF do ZIP do TSE.

    Precisa incluir ``BR``, senão as candidaturas de Presidente
    (``SG_UF = BR``) não entram na base e a busca fica vazia.
    """
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = archive.namelist()
        selection = select_csv_names(names, ufs)

        missing = [uf for uf in ufs if uf not in selection]

        if missing:
            raise FileNotFoundError(
                "O ZIP do TSE foi baixado, mas o CSV de "
                + ", ".join(missing)
                + " não foi encontrado."
                + f" Arquivos encontrados: {len(names)}"
            )

        return [archive.read(selection[uf]) for uf in ufs]


def load_candidates_from_tse() -> pd.DataFrame:
    """Baixa a base oficial do TSE com SP (estaduais) e BR (presidente)."""
    raw_zip = download_tse_zip()
    chunks = [
        read_csv_bytes(raw)
        for raw in extract_csvs(raw_zip, ["SP", "BR"])
    ]

    return pd.concat(chunks, ignore_index=True)


def data_fingerprint() -> tuple:
    """Identifica a base atual para invalidar o cache quando ela mudar.

    Sem isso, uma alteração em ``data/candidatos_2026.csv`` só era percebida
    após 15 minutos e a busca continuava sem os presidentes até lá.
    """
    if not LOCAL_CSV.exists():
        return ("tse", TSE_DATASET_URL)

    stat = LOCAL_CSV.stat()
    return ("local", str(LOCAL_CSV), stat.st_mtime_ns, stat.st_size)


@st.cache_data(ttl=900, show_spinner=False)
def load_candidates(fingerprint: tuple) -> tuple[pd.DataFrame, str]:
    """
    Carrega a base local, se existir. Caso contrário, baixa o arquivo oficial
    do TSE (SP + BR). O cache expira em 15 minutos ou quando a base muda.

    ``fingerprint`` participa apenas da chave do cache do Streamlit.
    """
    if LOCAL_CSV.exists():
        frame = read_local_csv(LOCAL_CSV)
        return frame, "arquivo local"

    frame = load_candidates_from_tse()
    return frame, "TSE"


def base_danificada(frame: pd.DataFrame) -> bool:
    """Detecta nomes com os acentos destruídos na base carregada.

    Um CSV gravado com conversão de encoding errada troca cada letra
    acentuada por ``�`` e o dado original se perde: só recopiando o
    arquivo oficial do TSE.
    """
    if "nome" not in frame.columns:
        return False

    nomes = frame["nome"].fillna("").astype(str)

    return bool(
        nomes.str.contains("\ufffd", regex=False).any()
        or nomes.str.contains("\u00ef\u00bf\u00bd", regex=False).any()
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_photo_index(directory: str) -> dict[str, str]:
    """Mapeia o sequencial do candidato para a foto oficial do TSE.

    As fotos vêm no pacote ``foto_cand2026_<UF>_div`` no padrão
    ``F<UF><SQ_CANDIDATO>_div.jpg``.

    ``directory`` participa da chave do cache: sem ele, um diretório de
    fixture de teste reaproveitaria o índice do diretório real.
    """
    index: dict[str, str] = {}

    base = Path(directory)

    if not base.is_dir():
        return index

    for photo_folder in sorted(base.glob("foto_cand*_div")):
        if not photo_folder.is_dir():
            continue

        for photo in sorted(photo_folder.glob("*.jpg")):
            # FSP250002530091_div.jpg -> 250002530091
            sequence = photo.stem[3:-4]

            if sequence.isdigit():
                index.setdefault(sequence, str(photo))

    return index


@st.cache_data(ttl=3600, show_spinner=False)
def photo_data_uri(sequence: str, directory: str) -> str:
    """Retorna a foto do candidato como data URI para usar em ``<img>``.

    Caminho local não funciona no navegador nem na folha impressa, então a
    imagem é embutida em base64.
    """
    if not sequence:
        return ""

    photo = load_photo_index(directory).get(sequence)

    if not photo:
        return ""

    encoded = base64.b64encode(Path(photo).read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def photo_tag(candidate: dict, css_class: str, placeholder: str = "") -> str:
    """Bloco ``<img>`` da foto; ``placeholder`` quando não há foto.

    O placeholder serve às grades fixas (revisão e impressão), onde a
    ausência da imagem desalinharia as demais colunas.
    """
    if candidate.get("foto"):
        return (
            f'<img class="{css_class}" src="{candidate["foto"]}" '
            'alt="Foto do candidato">'
        )

    return placeholder


def esc(value: object) -> str:
    """Escapa texto do TSE antes de entrar em HTML.

    Hoje nenhum campo da base contém ``<``, ``>`` ou ``&``, mas o escape é
    barato e evita injeção de HTML se o TSE mudar a formatar algum nome.
    """
    return html.escape(str(value), quote=True)


def cargo_matches(cargo: object, config: dict) -> bool:
    """Compara o cargo de forma estrita, sem misturar cargos parecidos.

    A comparação por contenção (``"PRESIDENTE" in cargo``) aceitava também
    ``VICE-PRESIDENTE`` e ``VICE-GOVERNADOR``. Como os vices são ordenados
    antes do presidente, a busca de presidente listava os vices no lugar dos
    presidentes.
    """
    normalized = normalize_text(cargo)

    for term in config["cargo_terms"]:
        normalized_term = normalize_text(term)

        # Igualdade exata ou rótulo mais longo iniciando pelo termo,
        # como "PRESIDENTE DA REPÚBLICA". O prefixo evita tratar
        # "VICE-PRESIDENTE" como "PRESIDENTE".
        if normalized == normalized_term or normalized.startswith(
            normalized_term
        ):
            return True

    return False


def filter_for_position(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    if config["uf"] == "BR":
        candidates = df.copy()
    else:
        candidates = df[df["uf"].eq(config["uf"])].copy()

    mask = candidates["cargo"].map(
        lambda cargo: cargo_matches(cargo, config)
    )

    candidates = candidates[mask].copy()

    # Remove candidaturas que não possuem o tamanho esperado.
    candidates = candidates[
        candidates["numero"].str.len().eq(config["digits"])
    ].copy()

    return candidates


def search_candidates(
    df: pd.DataFrame,
    config: dict,
    query: str,
) -> pd.DataFrame:
    candidates = filter_for_position(df, config)

    query = query.strip()

    if not query:
        return candidates.head(0)

    if query.isdigit():
        result = candidates[
            candidates["numero"].eq(clean_number(query))
        ].copy()
    else:
        normalized_query = normalize_text(query)

        result = candidates[
            candidates["nome_norm"].str.contains(
                normalized_query,
                regex=False,
                na=False,
            )
            | candidates["nome_completo_norm"].str.contains(
                normalized_query,
                regex=False,
                na=False,
            )
        ].copy()

    sort_columns = ["nome", "numero"]

    existing = [
        column for column in sort_columns
        if column in result.columns
    ]

    return result.sort_values(existing).head(50)


def candidate_id(row: pd.Series) -> str:
    sequence = str(row.get("sq_candidato", "")).strip()

    if sequence:
        return sequence

    return "|".join(
        [
            str(row.get("uf", "")),
            str(row.get("cargo", "")),
            str(row.get("numero", "")),
            str(row.get("nome", "")),
        ]
    )


def candidate_to_dict(row: pd.Series) -> dict:
    sequence = str(row.get("sq_candidato", "")).strip()

    return {
        "id": candidate_id(row),
        "numero": str(row["numero"]),
        "nome": str(row["nome"]),
        "nome_completo": str(row.get("nome_completo", "")),
        "cargo": str(row["cargo"]),
        "partido": str(row["partido"]),
        "situacao": str(row.get("situacao", "")),
        "foto": photo_data_uri(sequence, str(DATA_DIR)),
    }


def selected_candidate(key: str) -> dict | None:
    return st.session_state.selected.get(key)


def validate_selection() -> list[str]:
    errors = []

    senator_1 = selected_candidate("senador_1")
    senator_2 = selected_candidate("senador_2")

    if senator_1 and senator_2:
        if senator_1["id"] == senator_2["id"]:
            errors.append(
                "As duas vagas do Senado precisam ter candidatos diferentes."
            )

    return errors


def count_selected() -> int:
    return sum(
        1
        for key in st.session_state.selected
        if st.session_state.selected[key] is not None
    )


def reset_selection() -> None:
    st.session_state.selected = {
        item["key"]: None
        for item in BALLOT_ORDER_ACTIVE
    }


def candidate_html(candidate: dict) -> str:
    # Valores placeholder do TSE ("#NE", "#NULO") não informam nada.
    situacao = str(candidate.get("situacao") or "").strip()
    situation = (
        f" · {situacao}"
        if situacao.lstrip("#").upper() not in {"", "NE", "NULO", "NULA"}
        else ""
    )

    # Sem indentação e sem linhas em branco: o Markdown só trata o conteúdo
    # como HTML se a primeira linha começar na coluna 0 e o bloco não tiver
    # linha vazia no meio.
    lines = ['<div class="candidate-card">']
    photo = photo_tag(candidate, "candidate-photo")

    if photo:
        lines.append(photo)

    lines.append(
        "<div>"
        f'<div class="candidate-number">{esc(candidate["numero"])}</div>'
        f'<div class="candidate-name">{esc(candidate["nome"])}</div>'
        f'<div class="candidate-meta">{esc(candidate["partido"])} · '
        f'{esc(candidate["cargo"])}{esc(situation)}</div>'
        "</div>"
    )
    lines.append("</div>")

    return "\n".join(lines)


def render_selected_card(config: dict, candidate: dict) -> None:
    photo = photo_tag(candidate, "selected-photo")
    lines = ['<div class="selected-card">']

    if photo:
        lines.append('<div class="selected-head">')
        lines.append(photo)

    lines.extend(
        [
            "<div>",
            f"<div>{esc(config['label'])}</div>",
            f'<div class="selected-number">{esc(candidate["numero"])}</div>',
            f'<div><strong>{esc(candidate["nome"])}</strong></div>',
            f'<div>{esc(candidate["partido"])}</div>',
            "</div>",
        ]
    )

    if photo:
        lines.append("</div>")

    lines.append("</div>")

    st.markdown("\n".join(lines), unsafe_allow_html=True)


def render_review(selected: dict) -> None:
    for index, config in enumerate(BALLOT_ORDER_ACTIVE, start=1):
        candidate = selected.get(config["key"]) or {}

        if candidate:
            name = candidate["nome"]
            number = candidate["numero"]
            party = candidate["partido"]
        else:
            name = "Não preenchido"
            number = "_____"
            party = ""

        photo = photo_tag(
            candidate,
            "review-photo",
            placeholder=(
                '<div class="review-photo review-photo-empty"></div>'
            ),
        )

        lines = [
            '<div class="review-row">',
            f'<div class="review-order">{index:02d}</div>',
            photo,
            "<div>",
            f'<div class="review-cargo">{esc(config["label"])}</div>',
            f'<div class="review-name">{esc(name)}</div>',
            f'<div class="candidate-meta">{esc(party)}</div>',
            "</div>",
            f'<div class="review-number">{esc(number)}</div>',
            "</div>",
        ]

        st.markdown("\n".join(lines), unsafe_allow_html=True)


def build_print_card(selected: dict) -> str:
    items = []

    for config in BALLOT_ORDER_ACTIVE:
        candidate = selected.get(config["key"]) or {}

        if candidate:
            number = candidate["numero"]
            name = candidate["nome"]
            party = candidate["partido"]
        else:
            number = "_____"
            name = "Não preenchido"
            party = ""

        # O slot da foto fica sempre no lugar, mesmo sem foto, para as
        # colunas dos seis cargos continuarem alinhadas.
        photo = photo_tag(candidate, "print-item-photo")

        items.append(
            "\n".join(
                [
                    '<div class="print-item">',
                    (
                        '<div class="print-item-photo-slot">'
                        f"{photo}</div>"
                    ),
                    "<div>",
                    f'<div class="print-item-cargo">{esc(config["label"])}</div>',
                    f'<div class="print-item-name">{esc(name)}</div>',
                    f'<div class="print-item-party">{esc(party)}</div>',
                    "</div>",
                    f'<div class="print-item-number">{esc(number)}</div>',
                    "</div>",
                ]
            )
        )

    # join sem linhas em branco: uma linha em branco faria o Markdown
    # encerrar o bloco HTML e imprimir as tags literalmente.
    items_html = "\n".join(items)

    return f"""
    <div class="print-card">
        <div class="print-card-title">COLA ELEITORAL {ELECTION_CONFIG['year']}</div>
        <div class="print-card-subtitle">SÃO PAULO · {ROUND_LABEL.upper()}</div>
        {items_html}
        <div class="print-footer">
            Confira na urna o número, nome, foto, cargo e sigla partidária
            antes de confirmar seu voto.
        </div>
    </div>
    """.strip()


# CSS do documento de pré-visualização: a folha mora num HTML novo, aberto
# em outra aba, sem nenhum elemento do Streamlit em volta — é isso que
# garante a folha exatamente na página inteira, em 100%.
PRINT_CSS = """
    @page { size: A4 portrait; margin: 0; }

    * { box-sizing: border-box; }

    html, body { margin: 0; padding: 0; }

    body {
        background: #eceff1;
        color: #111;
        font-family: "Source Sans Pro", "Segoe UI", sans-serif;
    }

    .preview-bar {
        position: sticky;
        top: 0;
        z-index: 5;
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        padding: 10px 16px;
        background: #1e1e1e;
    }

    .preview-bar button {
        border: 0;
        border-radius: 8px;
        padding: 9px 18px;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
    }

    .preview-print { background: #ff4b4b; color: #fff; }

    .preview-close { background: #555; color: #fff; }

    .preview-hint {
        font-size: 12.5px;
        color: #ddd;
    }

    .print-sheet {
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-template-rows: 1fr 1fr;
        width: 210mm;
        height: 297mm;
        margin: 12mm auto;
        background: #fff;
        box-shadow: 0 3px 16px rgba(0, 0, 0, 0.3);
        overflow: hidden;
    }

    .print-card {
        width: 105mm;
        height: 148.5mm;
        box-sizing: border-box;
        border: 0.4mm dashed #888;
        padding: 7mm;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        background: white;
        color: #111;
    }

    .print-card-title {
        font-size: 12pt;
        font-weight: 900;
        text-align: center;
        margin-bottom: 1mm;
    }

    .print-card-subtitle {
        font-size: 7.5pt;
        text-align: center;
        color: #555;
        margin-bottom: 4mm;
    }

    .print-item {
        display: grid;
        grid-template-columns: 9mm 1fr auto;
        gap: 3mm;
        align-items: center;
        border-bottom: 0.25mm solid #ddd;
        padding: 2.4mm 0;
    }

    .print-item-photo-slot {
        width: 9mm;
    }

    .print-item-photo {
        display: block;
        height: 11mm;
        width: auto;
        object-fit: cover;
        border: 0.2mm solid #ccc;
        background: #eee;
    }

    .print-item-cargo {
        font-size: 7pt;
        text-transform: uppercase;
        font-weight: 700;
        color: #555;
    }

    .print-item-name {
        font-size: 7.3pt;
        font-weight: 700;
        max-width: 55mm;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .print-item-party {
        font-size: 6.5pt;
        color: #555;
    }

    .print-item-number {
        font-size: 18pt;
        font-weight: 900;
        letter-spacing: 0.05em;
    }

    .print-footer {
        margin-top: auto;
        font-size: 5.8pt;
        line-height: 1.25;
        color: #555;
        padding-top: 3mm;
    }

    @media print {
        body { background: #fff; overflow: hidden; }

        .preview-bar { display: none !important; }

        .print-sheet {
            margin: 0 !important;
            box-shadow: none !important;
        }

        .print-card { break-inside: avoid; }
    }
"""

PREVIEW_BUTTON_HTML = """
<div>
  <button id="cola-preview-btn" style="
      display: inline-block;
      background: #ff4b4b;
      color: #fff;
      border: 0;
      border-radius: 10px;
      padding: 12px 22px;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  ">Abrir pré-visualização de impressão (aba nova, 100%)</button>
</div>
<script>
  // O documento inteiro vem em base64: nenhum caractere especial consegue
  // quebrar este bloco de script.
  const COLA_DOC_B64 = "__COLA_DOC__";

  function colaAbrirPreview() {
    const bytes = Uint8Array.from(atob(COLA_DOC_B64), (c) => c.charCodeAt(0));
    const documento = new TextDecoder("utf-8").decode(bytes);
    const url = URL.createObjectURL(
      new Blob([documento], { type: "text/html;charset=utf-8" })
    );
    const win = window.open(url, "_blank");

    if (!win) {
      alert(
        "O navegador bloqueou a nova aba. Permita pop-ups para este site e tente de novo."
      );
    }

    setTimeout(() => URL.revokeObjectURL(url), 120000);
  }

  document
    .getElementById("cola-preview-btn")
    .addEventListener("click", colaAbrirPreview);
</script>
"""


def build_preview_document(selected: dict) -> str:
    """Documento HTML autônomo da folha, para abrir em outra aba."""
    card = build_print_card(selected)
    sheet = "\n".join([card] * 4)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="pt-BR">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>Cola Eleitoral {YEAR} — impressão</title>\n"
        f"<style>{PRINT_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="preview-bar">\n'
        '<button class="preview-print" onclick="window.print()">'
        "Imprimir</button>\n"
        '<button class="preview-close" onclick="window.close()">'
        "Fechar aba</button>\n"
        '<span class="preview-hint">'
        "A4 retrato · escala 100% · margens padrão ou mínimas · "
        "cabeçalhos e rodapés desativados.\n"
        "</span>\n"
        "</div>\n"
        f'<div class="print-sheet">\n{sheet}\n</div>\n'
        "</body>\n"
        "</html>\n"
    )


def render_print_area(selected: dict) -> None:
    """Exibe o botão que abre a folha num documento novo em outra aba.

    O preview fica isolado da interface do Streamlit: sem chrome, sem
    layout deslocado e exatamente 100%, então a folha sai em uma página só.
    """
    payload = base64.b64encode(
        build_preview_document(selected).encode("utf-8")
    ).decode("ascii")

    st.html(
        PREVIEW_BUTTON_HTML.replace("__COLA_DOC__", payload),
        unsafe_allow_javascript=True,
    )


# ============================================================
# ESTADO
# ============================================================

if "selected" not in st.session_state:
    reset_selection()

if "page" not in st.session_state:
    st.session_state.page = "1. Montar cola"

if st.session_state.page not in [
    "1. Montar cola",
    "2. Revisar",
    "3. Imprimir",
]:
    st.session_state.page = "1. Montar cola"

# O índice muda a cada navegação programática: a chave do rádio precisa ser
# nova para que o widget releia ``index`` (o estado do widget antigo venceria).
if "nav_epoch" not in st.session_state:
    st.session_state.nav_epoch = 0


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown(
    '<h1 class="app-title">🗳️ Cola Eleitoral 2026</h1>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="app-subtitle">São Paulo · Monte sua cola pessoal para o '
    f'{ROUND_LABEL}</div>',
    unsafe_allow_html=True,
)

st.info(
    "Você escolhe. O sistema apenas organiza os números na ordem da urna. "
    "Não há recomendação ou ranking de candidatos."
)


# ============================================================
# CARREGAMENTO
# ============================================================

try:
    with st.spinner("Carregando dados oficiais de candidaturas..."):
        candidates_df, data_source = load_candidates(data_fingerprint())

except Exception as exc:
    st.error("Não foi possível carregar a base de candidaturas.")
    st.code(str(exc))

    st.markdown(
        f"""
        **Fonte oficial do TSE**

        {TSE_DATASET_URL}

        Você também pode baixar o ZIP do TSE, extrair o CSV de SP e colocá-lo
        como:

        `data/candidatos_2026.csv`
        """
    )

    st.stop()


if base_danificada(candidates_df):
    st.warning(
        "A base carregada está sem acentos (caracteres ilegíveis como "
        "ï¿½). O arquivo `data/candidatos_2026.csv` foi gravado com a "
        "conversão de encoding errada e o texto original não pode ser "
        "recuperado: recopie o CSV oficial do TSE "
        "(consulta_cand_2026_SP.csv e consulta_cand_2026_BR.csv)."
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("Sobre")

    st.write(
        "Ferramenta para organização pessoal dos números escolhidos "
        "para a votação de 2026."
    )

    st.caption(f"Fonte carregada: {data_source}")
    st.caption(f"Candidaturas carregadas: {len(candidates_df):,}".replace(",", "."))

    st.divider()

    st.link_button(
        "Dados oficiais do TSE",
        "https://dadosabertos.tse.jus.br/dataset/candidatos-2026",
    )

    st.link_button(
        "DivulgaCandContas",
        "https://divulgacandcontas.tse.jus.br/",
    )

    if st.button("Limpar minha cola", use_container_width=True):
        reset_selection()
        st.rerun()


# ============================================================
# NAVEGAÇÃO
# ============================================================

PAGES = ["1. Montar cola", "2. Revisar", "3. Imprimir"]

# st.tabs não aceita troca de aba por código, então a navegação é um rádio
# horizontal: o botão "Continuar para impressão" consegue abrir a aba 3.
page = st.radio(
    "Etapas",
    PAGES,
    index=PAGES.index(st.session_state.page),
    key=f"nav_{st.session_state.nav_epoch}",
    horizontal=True,
    label_visibility="collapsed",
)

if page != st.session_state.page:
    st.session_state.page = page


# ============================================================
# TAB 1 — MONTAGEM
# ============================================================

if page == "1. Montar cola":
    st.subheader("Escolha suas candidaturas")

    st.caption(
        "Pesquise pelo nome ou número. O sistema mostra somente candidaturas "
        "compatíveis com o cargo selecionado."
    )

    for position_index, config in enumerate(BALLOT_ORDER_ACTIVE, start=1):
        st.markdown(
            f"### {position_index}. {config['label']}"
        )

        current = selected_candidate(config["key"])

        if current:
            render_selected_card(config, current)

            if st.button(
                f"Trocar {config['label']}",
                key=f"change_{config['key']}",
            ):
                st.session_state[f"editing_{config['key']}"] = True
                st.rerun()

        editing = (
            st.session_state.get(f"editing_{config['key']}", False)
            or current is None
        )

        if editing:
            query = st.text_input(
                f"Pesquisar {config['label']} por nome ou número",
                key=f"query_{config['key']}",
                placeholder="Ex.: Maria Silva ou 1234",
            )

            if query.strip():
                results = search_candidates(
                    candidates_df,
                    config,
                    query,
                )

                if results.empty:
                    st.warning(
                        "Nenhuma candidatura encontrada para essa pesquisa."
                    )
                else:
                    st.caption(
                        f"{len(results)} resultado(s) encontrado(s). "
                        "Selecione a candidatura correta."
                    )

                    for result_index, (_, row) in enumerate(
                        results.iterrows()
                    ):
                        candidate = candidate_to_dict(row)

                        col_info, col_button = st.columns(
                            [5, 1],
                            vertical_alignment="center",
                        )

                        with col_info:
                            st.markdown(
                                candidate_html(candidate),
                                unsafe_allow_html=True,
                            )

                        with col_button:
                            if st.button(
                                "Selecionar",
                                key=(
                                    f"select_{config['key']}_"
                                    f"{candidate['id']}_{result_index}"
                                ),
                            ):
                                st.session_state.selected[
                                    config["key"]
                                ] = candidate

                                st.session_state[
                                    f"editing_{config['key']}"
                                ] = False

                                st.rerun()

        st.divider()

    senator_1 = selected_candidate("senador_1")
    senator_2 = selected_candidate("senador_2")

    if senator_1 and senator_2 and senator_1["id"] == senator_2["id"]:
        st.error(
            "As duas vagas do Senado precisam ser preenchidas com "
            "candidatos diferentes."
        )

    st.success(
        f"{count_selected()} de {len(BALLOT_ORDER_ACTIVE)} posições preenchidas."
    )


# ============================================================
# TAB 2 — REVISÃO
# ============================================================

if page == "2. Revisar":
    st.subheader("Confira sua cola")

    errors = validate_selection()

    if errors:
        for error in errors:
            st.error(error)

    render_review(st.session_state.selected)

    st.warning(
        "Antes de confirmar cada voto na urna, confira na tela o número, "
        "nome, foto, cargo e sigla partidária."
    )

    filled = count_selected()

    if filled < len(BALLOT_ORDER_ACTIVE):
        st.info(
            f"Você preencheu {filled} de {len(BALLOT_ORDER_ACTIVE)} posições. "
            "É possível imprimir uma cola incompleta."
        )

    if st.button(
        "Continuar para impressão",
        type="primary",
        use_container_width=True,
        disabled=bool(errors),
    ):
        st.session_state.page = "3. Imprimir"
        st.session_state.nav_epoch += 1
        st.rerun()


# ============================================================
# TAB 3 — IMPRESSÃO
# ============================================================

if page == "3. Imprimir":
    st.subheader("Prévia para impressão")

    errors = validate_selection()

    if errors:
        for error in errors:
            st.error(error)

        st.stop()

    st.markdown(
        """
        A folha tem quatro cópias iguais da cola em A4 retrato.

        O botão abaixo abre a prévia em uma **nova aba**, fora da interface
        do aplicativo e em tamanho real (100%) — é a partir dessa aba que
        a folha sai correta, em uma página só.
        """
    )

    render_print_area(st.session_state.selected)

    st.markdown("---")

    st.markdown(
        """
        **Configuração recomendada (dentro da nova aba)**

        - Papel: A4
        - Orientação: Retrato
        - Escala: 100%
        - Margens: padrão ou mínimas
        - Cabeçalhos e rodapés: desativados

        Use o botão **Imprimir** da própria aba, ou Ctrl+P no Windows/Linux
        ou Cmd+P no macOS. No celular, use a opção de impressão do navegador
        **dentro da nova aba** — imprimir a partir da tela do aplicativo não
        gera a folha correta.
        """
    )


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "Dados de candidaturas: Tribunal Superior Eleitoral (TSE). "
    "Esta aplicação apenas organiza as escolhas feitas pelo usuário."
)

st.caption(
    "Consulte sempre as informações apresentadas pela urna antes de "
    "confirmar o voto."
)
