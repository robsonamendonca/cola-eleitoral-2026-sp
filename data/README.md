# Dados

O aplicativo não exige que o CSV seja versionado neste diretório.

Por padrão, ele baixa a base oficial de candidaturas de 2026:

https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip

Se quiser trabalhar com uma cópia local, coloque:

```text
data/candidatos_2026.csv
```

O arquivo local deve conter os dados de candidaturas e, preferencialmente, as colunas oficiais do TSE.

Este diretório também pode conter as fotos oficiais, em duas pastas:

```text
data/foto_cand2026_SP_div/
data/foto_cand2026_BR_div/
```

Cada arquivo segue o padrão `F<UF><SQ_CANDIDATO>_div.jpg`, do pacote de fotos do TSE. Com as pastas presentes, a foto aparece na busca, na revisão e na folha impressa.

Cuidado ao copiar ou converter o CSV: se os nomes saírem com caracteres ilegíveis (como `ï¿½`), os acentos foram destruídos na conversão e só voltam recopiando o arquivo oficial.

Não coloque dados pessoais de eleitores neste diretório.
