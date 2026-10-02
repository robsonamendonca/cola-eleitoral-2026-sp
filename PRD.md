# PRD — Cola Eleitoral 2026 SP

## 1. Visão do produto

Criar uma aplicação web simples, gratuita e mobile-first para ajudar eleitoras e eleitores do estado de São Paulo a montar e imprimir sua própria cola eleitoral para as Eleições Gerais de 2026.

O sistema permitirá:

1. Pesquisar candidatas e candidatos por nome.
2. Pesquisar candidatas e candidatos por número.
3. Selecionar os candidatos que a pessoa pretende votar.
4. Montar automaticamente a cola na mesma ordem em que os cargos aparecem na urna.
5. Validar os números conforme o cargo.
6. Permitir duas escolhas diferentes para senador.
7. Visualizar uma prévia da cola.
8. Gerar uma versão otimizada para impressão.
9. Imprimir quatro colas em uma única folha A4, ocupando aproximadamente 1/4 da folha para cada cola.
10. Permitir que o usuário preencha manualmente um número caso prefira não pesquisar o candidato.

O produto não deve recomendar, classificar, ranquear ou sugerir candidatos.

A decisão de voto pertence exclusivamente ao eleitor.

## 2. Contexto eleitoral

As Eleições Gerais de 2026 terão o primeiro turno em 4 de outubro de 2026.

Segundo o TSE, no primeiro turno serão realizadas seis escolhas, nesta ordem:

1. Deputado Federal
2. Deputado Estadual em São Paulo
3. Senador, primeira vaga
4. Senador, segunda vaga
5. Governador
6. Presidente da República

A ordem e a quantidade de dígitos são:

| Ordem | Cargo             | UF/abrangência | Dígitos |
| ----- | ----------------- | -------------- | ------: |
| 1     | Deputado Federal  | SP             |       4 |
| 2     | Deputado Estadual | SP             |       5 |
| 3     | Senador           | SP             |       3 |
| 4     | Senador           | SP             |       3 |
| 5     | Governador        | SP             |       2 |
| 6     | Presidente        | Brasil         |       2 |

O TSE confirma que a eleição de 2026 possui duas vagas para o Senado e que o eleitor poderá votar em duas candidaturas diferentes para senador.

O TSE também informa que é permitido levar uma cola em papel para a cabine de votação e consultar os números durante o voto.

## 3. Objetivo

Criar a forma mais simples possível de transformar as escolhas do eleitor em uma pequena anotação impressa.

Fluxo esperado:

Pesquisar candidato → conferir candidato → selecionar → montar cola → revisar → imprimir.

## 4. Público-alvo

Principal:

Eleitores do estado de São Paulo.

Secundário:

Familiares ou pessoas que desejam preparar sua própria cola eleitoral.

O MVP será direcionado para São Paulo, mas a arquitetura deve permitir expansão futura para outros estados.

## 5. Stack obrigatória

Python.

Streamlit.

Pandas.

Plotly.

Instalação mínima:

```bash
pip install streamlit pandas plotly
```

Imports mínimos:

```python
import streamlit as st
import pandas as pd
import plotly.express as px
```

Deploy obrigatório:

Streamlit Community Cloud, em:

https://streamlit.io/

Não utilizar:

React.

Node.js.

PHP.

MySQL.

Banco de dados externo no MVP.

Backend separado.

API própria.

## 6. Fonte oficial dos candidatos

A fonte primária dos dados deve ser o Tribunal Superior Eleitoral.

O Portal de Dados Abertos do TSE possui o conjunto oficial "Candidatos - 2026", incluindo dados de candidaturas, informações complementares, fotos, redes sociais, propostas e outros conjuntos relacionados.

Fonte:

https://dadosabertos.tse.jus.br/dataset/candidatos-2026

Também deve ser apresentada ao usuário uma referência para o DivulgaCandContas, sistema oficial do TSE para consulta das candidaturas.

## 7. Princípio fundamental dos dados

O aplicativo não deve criar dados eleitorais.

Não deve completar número de candidato com IA.

Não deve inferir número.

Não deve associar candidato a partido por aproximação.

Não deve utilizar resultados de mecanismos de busca como fonte primária.

Não deve permitir que um modelo de IA decida qual candidato corresponde a determinado número.

Toda correspondência:

nome → número → cargo → partido

deve vir da base oficial.

## 8. Atualização dos dados

Criar uma camada de carregamento de dados:

```text
data/
    candidatos_2026.csv
```

O MVP pode utilizar um CSV oficial baixado do TSE.

Criar também uma função:

```python
load_candidates()
```

Responsabilidades:

1. Carregar CSV.
2. Padronizar nomes de colunas.
3. Filtrar UF.
4. Filtrar eleição 2026.
5. Normalizar textos.
6. Normalizar números.
7. Retornar DataFrame.

Estrutura sugerida:

```python
@st.cache_data
def load_candidates():
    df = pd.read_csv(...)
    return normalize_candidates(df)
```

O uso de:

```python
@st.cache_data
```

é recomendado para evitar carregar o arquivo repetidamente.

## 9. Estrutura mínima dos dados

O sistema deve trabalhar internamente com uma estrutura semelhante a:

```text
ano
uf
cargo
numero
nome_urna
nome_completo
partido_sigla
partido_nome
situacao
foto
```

Caso o arquivo oficial possua nomes diferentes, criar um mapeamento.

Exemplo:

```python
COLUMN_MAP = {
    "NR_CANDIDATO": "numero",
    "NM_URNA_CANDIDATO": "nome_urna",
    "NM_CANDIDATO": "nome_completo",
    "SG_PARTIDO": "partido_sigla",
    "DS_CARGO": "cargo",
    "SG_UF": "uf"
}
```

Os nomes reais das colunas devem ser confirmados durante a implementação contra o arquivo oficial de 2026.

## 10. Normalização de pesquisa

Criar função:

```python
normalize_text(text)
```

A pesquisa deve:

1. Converter para string.
2. Remover espaços extras.
3. Converter para maiúsculas.
4. Remover acentos para comparação.
5. Manter o valor original para exibição.

Exemplo:

```text
João da Silva
JOAO DA SILVA
joao da silva
```

devem ser considerados equivalentes na busca.

## 11. Busca por nome

Interface:

```text
Pesquisar candidato

[ Digite o nome do candidato ]
```

Exemplo:

```text
Bolsonaro
```

O sistema deve apresentar:

```text
Nome
Número
Cargo
Partido
Situação
```

Não apresentar apenas o nome.

O eleitor deve conseguir conferir os dados antes de selecionar.

## 12. Busca por número

Interface:

```text
Pesquisar por número

[ 1234 ]
```

O sistema deve identificar automaticamente o cargo quando o número estiver associado a uma candidatura.

Exemplo:

```text
1234
```

Resultado:

```text
1234
Nome do candidato
Deputado Federal
Partido
```

Para números com quantidade de dígitos incompatível com o cargo selecionado, apresentar erro.

## 13. Busca combinada

Permitir pesquisa:

```text
Nome ou número
```

Exemplo:

```text
1234
```

ou:

```text
Maria Silva
```

O sistema deve detectar se a entrada parece ser numérica.

Pseudoalgoritmo:

```python
if query.isdigit():
    search_by_number(query)
else:
    search_by_name(query)
```

## 14. Seleção dos candidatos

A tela principal deve apresentar seis posições.

### Posição 1

```text
01
DEPUTADO FEDERAL

[ Pesquisar ]
```

### Posição 2

```text
02
DEPUTADO ESTADUAL

[ Pesquisar ]
```

### Posição 3

```text
03
SENADOR 1ª VAGA

[ Pesquisar ]
```

### Posição 4

```text
04
SENADOR 2ª VAGA

[ Pesquisar ]
```

### Posição 5

```text
05
GOVERNADOR

[ Pesquisar ]
```

### Posição 6

```text
06
PRESIDENTE

[ Pesquisar ]
```

## 15. Regra especial do Senado

O sistema deve obrigatoriamente tratar as duas vagas separadamente.

Não permitir o mesmo candidato nas duas posições.

Regra:

```python
if senador_1 == senador_2:
    st.error("Escolha duas candidaturas diferentes para senador.")
```

A situação também deve ser verificada pelo número.

Exemplo:

```text
Senador 1: 123
Senador 2: 123
```

Resultado:

```text
Erro:
As duas vagas do Senado precisam utilizar candidatos diferentes.
```

## 16. Validação dos números

Criar configuração:

```python
CARGO_CONFIG = {
    "Deputado Federal": {
        "digitos": 4
    },
    "Deputado Estadual": {
        "digitos": 5
    },
    "Senador": {
        "digitos": 3
    },
    "Governador": {
        "digitos": 2
    },
    "Presidente": {
        "digitos": 2
    }
}
```

A validação deve verificar:

```python
len(numero) == digitos
```

Mas a validação mais importante é a existência da candidatura na base oficial.

Não considerar um número válido apenas porque possui a quantidade correta de dígitos.

## 17. Situação da candidatura

O sistema deve exibir a situação disponível na base oficial.

Exemplo:

```text
Situação: APTO
```

ou outra situação oficial existente na base.

O sistema não deve substituir a informação oficial por interpretações próprias.

## 18. Revisão antes da impressão

Criar uma tela:

```text
CONFIRA SUA COLA

01  Deputado Federal
    1234
    Nome do candidato
    PARTIDO

02  Deputado Estadual
    12345
    Nome do candidato
    PARTIDO

03  Senador
    123
    Nome do candidato
    PARTIDO

04  Senador
    456
    Nome do candidato
    PARTIDO

05  Governador
    12
    Nome do candidato
    PARTIDO

06  Presidente
    13
    Nome do candidato
    PARTIDO
```

Botões:

```text
← Voltar

🖨️ Imprimir cola
```

## 19. Cola incompleta

O sistema não deve obrigar o preenchimento de todos os cargos.

O usuário poderá imprimir uma cola parcialmente preenchida.

Exemplo:

```text
DEPUTADO FEDERAL
1234

DEPUTADO ESTADUAL
_____

SENADOR
123

SENADOR
456

GOVERNADOR
_____

PRESIDENTE
13
```

Porém, deve existir uma mensagem:

```text
Confira se todos os números que você pretende utilizar estão preenchidos antes de imprimir.
```

## 20. Layout da cola

Formato físico:

A4.

Orientação:

Retrato.

Divisão:

2 colunas × 2 linhas.

Resultado:

4 colas por folha A4.

Cada cola ocupará aproximadamente:

```text
105 mm × 148,5 mm
```

O objetivo é permitir que o usuário recorte a folha em quatro partes.

## 21. Layout individual

Cada cartão deverá conter:

```text
COLA ELEITORAL 2026

SÃO PAULO

01
DEPUTADO FEDERAL
1234

02
DEPUTADO ESTADUAL
12345

03
SENADOR
123

04
SENADOR
456

05
GOVERNADOR
12

06
PRESIDENTE
13
```

Os números devem possuir destaque visual maior que os demais textos.

Exemplo:

```text
DEPUTADO FEDERAL

1234
```

O número deve ser imediatamente identificável.

## 22. Impressão

O aplicativo deve oferecer uma página específica para impressão.

O CSS deve utilizar:

```css
@media print
```

Na impressão:

Esconder:

* menu;
* botões;
* campos;
* instruções;
* elementos do Streamlit;
* componentes de pesquisa.

Mostrar somente:

```text
4 cartões de cola eleitoral
```

## 23. Estratégia de impressão

A melhor implementação para o MVP é criar uma página HTML própria para impressão usando componentes HTML/CSS.

Estrutura:

```html
<div class="print-page">

    <div class="cola">
        ...
    </div>

    <div class="cola">
        ...
    </div>

    <div class="cola">
        ...
    </div>

    <div class="cola">
        ...
    </div>

</div>
```

CSS:

```css
.print-page {
    width: 210mm;
    height: 297mm;

    display: grid;

    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
}

.cola {
    width: 105mm;
    height: 148.5mm;
    box-sizing: border-box;
    padding: 8mm;
}
```

Adicionar uma borda pontilhada para facilitar o corte.

## 24. Página de impressão

A impressão deverá gerar quatro cópias da mesma cola.

Isso é importante.

O usuário não precisa preencher quatro vezes.

Exemplo:

```text
┌──────────────┬──────────────┐
│     COLA     │     COLA     │
│              │              │
│  2026        │  2026        │
│              │              │
├──────────────┼──────────────┤
│     COLA     │     COLA     │
│              │              │
│  2026        │  2026        │
│              │              │
└──────────────┴──────────────┘
```

## 25. Pré-visualização

Antes de imprimir, mostrar uma prévia aproximada.

A prévia deve ser visualmente semelhante ao resultado físico.

Botão:

```text
IMPRIMIR 4 COLAS
```

## 26. Informações legais e educativas

Na interface, apresentar uma pequena mensagem:

```text
A cola eleitoral é uma anotação pessoal dos números que você escolheu.
O TSE permite levar uma cola em papel para a cabine de votação.
```

Fonte oficial:

TSE.

O aplicativo não deve pedir:

* título de eleitor;
* CPF;
* data de nascimento;
* endereço;
* zona eleitoral;
* seção eleitoral;
* senha;
* dados pessoais.

## 27. Regra sobre celular

Apresentar um aviso claro:

```text
Importante:
O celular não pode ser levado para a cabine de votação.
Imprima sua cola em papel e leve somente a anotação permitida.
```

O TSE informa que celular, câmera e outros dispositivos capazes de comprometer o sigilo não podem ser levados para a cabine.

## 28. Neutralidade política

O sistema deve ser estritamente neutro.

Não criar:

```text
Melhores candidatos
Candidatos confiáveis
Candidatos recomendados
Candidatos mais preparados
Candidatos favoritos
```

Não criar ranking.

Não criar pontuação.

Não recomendar candidato.

Não ordenar candidatos por preferência política.

A única ordenação obrigatória é a ordem oficial dos cargos na urna.

## 29. Página inicial

Estrutura:

```text
COLA ELEITORAL 2026

São Paulo

Monte sua cola eleitoral em poucos passos.

1. Encontre suas candidatas e seus candidatos.
2. Confira os dados.
3. Monte sua cola.
4. Imprima em papel.

[ COMEÇAR ]
```

Depois:

```text
Eleições 2026

1º turno: 4 de outubro de 2026

Sua cola é pessoal.
O sistema não escolhe candidatos por você.
```

## 30. Interface de seleção

Utilizar Streamlit.

Exemplo conceitual:

```python
st.title("Cola Eleitoral 2026")

st.subheader("1. Deputado Federal")

query = st.text_input(
    "Pesquisar por nome ou número",
    key="deputado_federal"
)
```

Resultados:

```python
st.dataframe(
    results[
        [
            "numero",
            "nome_urna",
            "partido_sigla"
        ]
    ]
)
```

Cada resultado deve permitir seleção.

## 31. Estado da aplicação

Utilizar:

```python
st.session_state
```

Exemplo:

```python
if "selected" not in st.session_state:
    st.session_state.selected = {
        "deputado_federal": None,
        "deputado_estadual": None,
        "senador_1": None,
        "senador_2": None,
        "governador": None,
        "presidente": None
    }
```

Não utilizar banco de dados no MVP.

## 32. Privacidade

Nenhuma escolha deve ser enviada para servidor externo.

As escolhas devem permanecer apenas na sessão do navegador enquanto o usuário estiver utilizando o aplicativo.

Não armazenar:

```text
IP
CPF
Título eleitoral
Nome do eleitor
Escolhas políticas
```

Não criar analytics individual de voto.

## 33. Dados de candidatos

Não persistir escolhas pessoais.

O CSV de candidatos pode ser armazenado no próprio projeto.

Estrutura:

```text
cola-eleitoral/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   └── candidatos_2026.csv
│
├── src/
│   ├── data.py
│   ├── search.py
│   ├── validation.py
│   └── print_layout.py
│
└── assets/
    └── style.css
```

Para um MVP ainda mais simples, pode começar com:

```text
app.py
requirements.txt
data/
    candidatos_2026.csv
```

## 34. Requirements

Arquivo:

```text
requirements.txt
```

Conteúdo mínimo:

```text
streamlit
pandas
plotly
```

O Plotly deve permanecer disponível mesmo que o MVP inicial não precise de gráficos.

## 35. Uso do Plotly

O produto principal não necessita de gráficos.

Entretanto, deixar preparado um painel administrativo ou informativo futuro.

Possíveis métricas:

```text
Candidaturas carregadas
Candidaturas por cargo
Candidaturas por partido
```

Não mostrar:

```text
Candidato mais escolhido pelos usuários
Candidato mais pesquisado
Candidato mais selecionado
```

Esses dados poderiam criar um efeito de influência sobre a decisão eleitoral.

## 36. Tratamento de erro

### CSV inexistente

Mostrar:

```text
Não foi possível carregar a base oficial de candidatos.
Verifique a configuração dos dados de 2026.
```

### CSV vazio

Mostrar:

```text
A base de candidaturas está vazia.
```

### Nenhum candidato encontrado

Mostrar:

```text
Nenhuma candidatura encontrada.

Confira o nome ou número informado.
```

### Mais de um candidato encontrado

Mostrar os resultados para escolha.

Nunca selecionar automaticamente.

## 37. Segurança contra erro de digitação

Nunca transformar:

```text
123
```

em:

```text
0123
```

automaticamente para um candidato.

Apenas normalizar quando isso for tecnicamente necessário para comparação, mantendo o número oficial original para exibição.

## 38. Verificação antes da impressão

Criar função:

```python
validate_ballot(selected_candidates)
```

Retornar:

```python
{
    "valid": True,
    "errors": []
}
```

ou:

```python
{
    "valid": False,
    "errors": [
        "Escolha duas candidaturas diferentes para senador."
    ]
}
```

## 39. Checklist de validação

Antes de permitir a impressão:

```text
✓ Deputado Federal
✓ Deputado Estadual
✓ Senador 1
✓ Senador 2
✓ Governador
✓ Presidente
```

Itens vazios não necessariamente impedem a impressão, mas devem ser claramente destacados.

## 40. Confirmação final

Antes da impressão:

```text
Confira sua cola

Atenção:
Antes de confirmar seu voto na urna, confira na tela:
número
nome
foto
cargo
sigla partidária

Você é responsável pela escolha realizada na urna.
```

O TSE orienta o eleitor a conferir as informações apresentadas pela urna antes de confirmar o voto.

## 41. Segundo turno

O MVP deve deixar preparado suporte para segundo turno.

No segundo turno, a aplicação deverá gerar somente os cargos que efetivamente forem submetidos a segundo turno.

Para 2026, o calendário prevê eventual segundo turno para presidente e governador em 25 de outubro.

A arquitetura não deve assumir que sempre haverá segundo turno.

## 42. Configuração eleitoral

Não espalhar datas e cargos pelo código.

Criar:

```python
ELECTION_CONFIG = {
    "year": 2026,
    "first_round": "2026-10-04",
    "state": "SP"
}
```

E:

```python
BALLOT_ORDER = [
    {
        "key": "deputado_federal",
        "label": "Deputado Federal",
        "digits": 4
    },
    {
        "key": "deputado_estadual",
        "label": "Deputado Estadual",
        "digits": 5
    },
    {
        "key": "senador_1",
        "label": "Senador — 1ª vaga",
        "digits": 3
    },
    {
        "key": "senador_2",
        "label": "Senador — 2ª vaga",
        "digits": 3
    },
    {
        "key": "governador",
        "label": "Governador",
        "digits": 2
    },
    {
        "key": "presidente",
        "label": "Presidente",
        "digits": 2
    }
]
```

## 43. Arquitetura

Arquitetura lógica:

```text
                ┌──────────────────────┐
                │     Streamlit UI     │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Candidate Search     │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Candidate DataFrame  │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Selection / State    │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Validation           │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Print Layout         │
                └──────────────────────┘
```

## 44. Responsabilidades

### app.py

Interface Streamlit.

### data.py

Carregamento e normalização dos dados.

### search.py

Pesquisa por nome e número.

### validation.py

Validação das escolhas.

### print_layout.py

HTML/CSS da cola.

## 45. Critérios de aceite do MVP

### CA01

O sistema inicia com:

```bash
streamlit run app.py
```

sem erros.

### CA02

O sistema carrega os candidatos de São Paulo.

### CA03

É possível pesquisar por nome.

### CA04

É possível pesquisar por número.

### CA05

O resultado apresenta nome, número, cargo e partido.

### CA06

É possível selecionar uma candidatura.

### CA07

É possível selecionar duas candidaturas para senador.

### CA08

O sistema impede o mesmo senador nas duas vagas.

### CA09

A ordem da cola é:

```text
Deputado Federal
Deputado Estadual
Senador
Senador
Governador
Presidente
```

### CA10

A cola apresenta os números com destaque.

### CA11

A cola pode ser impressa.

### CA12

A página de impressão possui quatro colas em uma folha A4.

### CA13

Os quatro cartões apresentam exatamente a mesma seleção.

### CA14

A impressão não mostra a interface do Streamlit.

### CA15

O sistema funciona em desktop.

### CA16

O sistema funciona em smartphone para montagem da cola.

### CA17

Nenhuma candidatura é recomendada pelo sistema.

### CA18

Nenhuma escolha eleitoral pessoal é armazenada.

## 46. Critérios de qualidade

Interface:

Simples.

Rápida.

Mobile-first.

Poucos elementos.

Botões grandes.

Números facilmente legíveis.

Impressão prioritária.

A aplicação deve conseguir ser compreendida sem tutorial.

## 47. MVP fora do escopo

Não implementar inicialmente:

Login.

Cadastro.

Banco de dados.

Comentários sobre candidatos.

Avaliação de candidatos.

Ranking.

Comparação política.

Inteligência artificial para recomendar voto.

Feed de notícias.

Rede social.

Comentários de usuários.

Sistema de votação.

Armazenamento de escolhas.

Publicidade.

Monetização.

## 48. Evolução futura

Depois do MVP, poderão ser adicionados:

1. Outros estados.
2. Atualização automática dos dados oficiais.
3. Página específica para cada UF.
4. Segundo turno.
5. QR Code apontando para fonte oficial.
6. Link direto para DivulgaCandContas.
7. Exportação PDF.
8. PWA.
9. Compartilhamento da configuração da cola sem armazenar dados no servidor.
10. Página educativa sobre cada cargo.
11. Integração com dados oficiais de propostas e contas, sempre mantendo separação entre informação e recomendação.

## 49. Requisito importante sobre fonte dos dados

O aplicativo deve informar claramente:

```text
Dados de candidaturas:
Tribunal Superior Eleitoral — Eleições 2026.

Este aplicativo apenas organiza as informações para facilitar a montagem de uma cola eleitoral pessoal.
```

O TSE disponibiliza oficialmente os dados de candidaturas de 2026 e o DivulgaCandContas para consulta das informações eleitorais.

## 50. Resultado esperado

Ao terminar o MVP, o usuário deverá conseguir fazer:

```text
1. Abrir o site.

2. Selecionar São Paulo.

3. Pesquisar:
   Deputado Federal.

4. Escolher seu candidato.

5. Pesquisar:
   Deputado Estadual.

6. Escolher seu candidato.

7. Escolher Senador 1.

8. Escolher Senador 2.

9. Escolher Governador.

10. Escolher Presidente.

11. Conferir a cola.

12. Clicar em:
    IMPRIMIR.

13. Receber uma folha A4 com:

    ┌─────────────┬─────────────┐
    │     COLA    │     COLA    │
    │    2026     │    2026     │
    ├─────────────┼─────────────┤
    │     COLA    │     COLA    │
    │    2026     │    2026     │
    └─────────────┴─────────────┘

14. Recortar uma das quatro colas.

15. Levar a anotação de papel para a cabine.
```

## 51. Definição de pronto

O projeto será considerado pronto quando:

```text
[ ] Código executa no Streamlit
[ ] requirements.txt funciona
[ ] Dados oficiais 2026 carregam
[ ] SP está configurado
[ ] Busca por nome funciona
[ ] Busca por número funciona
[ ] Seleção funciona
[ ] Dois senadores funcionam
[ ] Validação funciona
[ ] Prévia funciona
[ ] Impressão funciona
[ ] Quatro colas aparecem em uma A4
[ ] Layout mobile funciona
[ ] Fonte TSE está indicada
[ ] Nenhum ranking/recomendação existe
[ ] Não há armazenamento das escolhas
[ ] Deploy funciona no Streamlit Community Cloud
[ ] README explica instalação e deploy
```

## 52. README mínimo

O repositório deverá explicar:

```text
# Cola Eleitoral 2026 SP

Aplicação gratuita para montagem e impressão de uma cola eleitoral
pessoal para as Eleições Gerais de 2026.

## Tecnologias

Python
Streamlit
Pandas
Plotly

## Fonte dos dados

Tribunal Superior Eleitoral

## Execução local

pip install -r requirements.txt

streamlit run app.py

## Deploy

Streamlit Community Cloud

## Importante

O sistema não recomenda candidatos.

Ele apenas organiza os números escolhidos pelo próprio eleitor.

Consulte sempre as informações apresentadas pela urna antes de confirmar o voto.
```

## 53. Observação sobre a proposta

A aplicação deve ser posicionada como uma ferramenta de organização pessoal da votação, não como uma plataforma de campanha ou orientação eleitoral.

A funcionalidade central é:

```text
"Você escolhe.
O sistema organiza.
Você confere.
Você imprime."
```

Isso mantém o produto simples, útil e tecnicamente seguro.
