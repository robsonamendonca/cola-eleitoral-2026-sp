# Cola Eleitoral 2026 SP

Aplicação web simples, gratuita e neutra para montar e imprimir uma cola eleitoral pessoal para as Eleições Gerais de 2026, com foco em São Paulo.

O projeto usa:

- Python
- Streamlit
- Pandas
- Plotly

A aplicação consulta os dados oficiais de candidaturas do Tribunal Superior Eleitoral (TSE). Por padrão, o `app.py` baixa o arquivo oficial de candidaturas de 2026 diretamente do CDN do TSE, extrai as bases de São Paulo (`SP`) e do Brasil (`BR`, onde ficam as candidaturas de Presidente) e as mantém em cache durante a execução.

## Objetivo

Você escolhe as candidatas e os candidatos que pretende votar. O sistema apenas organiza os números na ordem em que aparecerão na urna.

A aplicação não:

- recomenda candidatos;
- classifica candidatos;
- cria ranking;
- atribui pontuação;
- registra o voto do usuário;
- solicita CPF ou título de eleitor;
- armazena as escolhas políticas do usuário.

## Ordem da votação em São Paulo

No primeiro turno, a ordem é:

1. Deputado Federal, 4 dígitos
2. Deputado Estadual, 5 dígitos
3. Senador, 1ª vaga, 3 dígitos
4. Senador, 2ª vaga, 3 dígitos
5. Governador, 2 dígitos
6. Presidente da República, 2 dígitos

São Paulo usa Deputado Estadual. Deputado Distrital é o cargo correspondente ao Distrito Federal.

## Estrutura

```text
cola-eleitoral-2026-sp/
├── app.py
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── README.md
├── PRD.md
├── Contexto.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   └── README.md
├── docs/
│   ├── modelo.py
│   └── cola-eleitoral-2026-atual-27-08.pdf
└── tests/
    ├── conftest.py
    ├── test_app.py
    └── fixtures/
        ├── data/
        └── danificada/
```

O CSV do TSE não é versionado no Git por padrão porque é grande e o TSE atualiza a base várias vezes ao dia.

## Instalação local

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
streamlit run app.py
```

## Deploy no Streamlit Community Cloud

1. Crie um repositório no GitHub.
2. Envie os arquivos deste projeto.
3. Entre no Streamlit Community Cloud.
4. Crie uma nova aplicação.
5. Selecione o repositório.
6. Informe `app.py` como arquivo principal.
7. Faça o deploy.

A aplicação precisa de acesso à internet para baixar a base oficial do TSE quando não existir uma cópia local.

## Fonte oficial

Dados de candidaturas:

Portal de Dados Abertos do TSE:
https://dadosabertos.tse.jus.br/dataset/candidatos-2026

Arquivo oficial utilizado pelo aplicativo:

https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip

A página do TSE informa que o conjunto de candidatos de 2026 tem como fonte os sistemas CAND, Candex e DivulgaCand e possui atualização quatro vezes ao dia.

## Base local opcional

Se você preferir não baixar a base automaticamente, coloque um arquivo CSV em:

```text
data/candidatos_2026.csv
```

O aplicativo tentará usar esse arquivo antes de baixar a base oficial.

O CSV deve conter, pelo menos:

```text
SG_UF
DS_CARGO
NR_CANDIDATO
NM_CANDIDATO
NM_URNA_CANDIDATO
SG_PARTIDO
DS_SITUACAO_CANDIDATURA
```

O CSV oficial do TSE normalmente usa `;` como separador e codificação compatível com arquivos eleitorais brasileiros. O aplicativo tenta detectar automaticamente o separador, usando UTF-8 primeiro e `latin-1` como fallback.

Se os nomes aparecerem com caracteres ilegíveis (como `ï¿½`), o arquivo foi gravado com a conversão de encoding errada e os acentos se perderam de vez. Nesse caso, recopie o CSV oficial do TSE para `data/candidatos_2026.csv`.

## Fotos dos candidatos

As fotos oficiais ficam nas pastas:

```text
data/foto_cand2026_SP_div/
data/foto_cand2026_BR_div/
```

O nome de cada arquivo segue o padrão `F<UF><SQ_CANDIDATO>_div.jpg`, do próprio pacote de fotos do TSE. Com as pastas presentes, a foto aparece nos resultados da busca, na revisão e na folha impressa. Sem elas, o aplicativo funciona normalmente, apenas sem fotos.

## Busca

A pesquisa aceita:

- nome completo;
- nome de urna;
- parte do nome;
- número do candidato.

A busca não inventa números. O número exibido precisa existir na base carregada.

## Senado

Existem duas posições:

```text
Senador — 1ª vaga
Senador — 2ª vaga
```

O mesmo candidato não pode ser selecionado nas duas vagas.

## Impressão

A impressão foi separada da tela do aplicativo: a aba **3. Imprimir** tem o
botão **Abrir pré-visualização de impressão**, que abre a folha em uma **nova
aba**, em um documento HTML isolado da interface do Streamlit e em tamanho
real (100%). É a partir dessa aba que a folha sai correta — imprimir a
partir da tela do aplicativo não gera a folha.

Cada folha contém quatro cópias iguais da cola:

```text
┌────────────────┬────────────────┐
│      COLA      │      COLA      │
│      2026      │      2026      │
├────────────────┼────────────────┤
│      COLA      │      COLA      │
│      2026      │      2026      │
└────────────────┴────────────────┘
```

Cada cartão tem aproximadamente 105 mm × 148,5 mm.

Na nova aba, use o botão **Imprimir** da própria aba (ou Ctrl+P no
Windows/Linux, Cmd+P no macOS) com a configuração:

- papel A4;
- orientação retrato;
- escala 100%, se disponível;
- margens padrão ou mínimas, conforme o navegador;
- cabeçalhos e rodapés do navegador desativados.

## Privacidade

As escolhas ficam somente no estado da sessão do Streamlit.

O aplicativo não possui banco de dados.

Não existe login.

Não existe cadastro.

Não existe envio das escolhas para uma API própria.

## Testes automatizados

Os testes usam `pytest` e o `AppTest` do próprio Streamlit, rodam contra uma
base pequena em `tests/fixtures/` (nada de rede e nada da base real) e cobrem:

- busca por nome sem acento que encontra e exibe nomes acentuados;
- filtro de cargo (presidente e governador não vazam vices, mesmo com o
  mesmo número);
- escape de HTML nos nomes (`&`, `<`, `>`);
- ocultação do placeholder `#NE` e exibição de situação real;
- bloqueio do mesmo senador nas duas vagas;
- fluxo completo das 6 posições até a revisão e a folha impressa
  (4 cartões, fotos em base64 e cabeçalho `SÃO PAULO · 1º TURNO`);
- documento da prévia em nova aba (A4 com `@page`, 4 cartões e botão
  embutido em base64) — impresso com Chrome headless, sai em 1 página só;
- aviso quando a base carregada está sem acentos (encoding errado).

Para rodar:

```bash
pip install -r requirements-dev.txt
pytest
```

Os testes apontam o app para a fixture através da variável de ambiente
`COLA_DATA_DIR` (definida em `tests/conftest.py`). Para testar o 2º turno,
basta trocar `ELECTION_CONFIG["round"]` em `app.py`.

## Testes manuais

Depois de iniciar o aplicativo:

- [ ] A página abre sem erro.
- [ ] A base de candidatos é carregada.
- [ ] Os nomes aparecem com acentos (sem caracteres ilegíveis).
- [ ] É possível pesquisar por nome.
- [ ] É possível pesquisar por número.
- [ ] Deputado Federal aceita somente candidatura correspondente ao cargo.
- [ ] Deputado Estadual aceita somente candidatura correspondente ao cargo.
- [ ] Senado mostra duas posições.
- [ ] O mesmo senador não pode ocupar as duas posições.
- [ ] Governador é filtrado corretamente.
- [ ] Presidente é filtrado corretamente, sem vice.
- [ ] A foto do candidato aparece na busca, na revisão e na folha impressa.
- [ ] A revisão mostra os seis cargos na ordem da urna.
- [ ] O botão da prévia abre em uma nova aba.
- [ ] A impressão mostra quatro cópias em uma única página A4.
- [ ] A página impressa fica em A4.
- [ ] Os botões e a interface do Streamlit não aparecem na impressão.

## Importante

A cola é uma anotação pessoal dos números escolhidos pelo próprio eleitor.

Antes de confirmar cada voto na urna, confira o número, nome, foto, cargo e sigla partidária apresentados na tela da urna.

Consulte sempre as informações oficiais do TSE.

## Licença do código

Sugestão para este projeto: MIT.

Os dados eleitorais são provenientes do TSE e devem respeitar a licença e as condições indicadas pelo próprio órgão na fonte oficial.
