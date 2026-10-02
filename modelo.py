# Passo a passo do projeto
# Passo 1: Criar a tela do sistema
# Passo 2: Criar o formulário de cadastro
# Passo 3: Salvar a venda na base de dados
# Passo 4: Mostrar a base de dados na tela
# Passo 5: Criar o dashboard com os gráficos

# pip install streamlit pandas plotly
import streamlit as st
import pandas as pd
import plotly.express as px

# Passo 1: Criar a tela do sistema
st.write("# Sistema de Vendas")

tabela = pd.read_csv("vendas.csv")

# Passo 2: Criar o formulário de cadastro
st.sidebar.write("## Cadastrar venda")
data = st.sidebar.date_input("Data")
vendedor = st.sidebar.selectbox("Vendedor", ["Ana", "Bruno", "Carla"])
produto = st.sidebar.selectbox("Produto", ["Notebook", "Celular", "Fone"])
quantidade = st.sidebar.number_input("Quantidade", step=1)
valor = st.sidebar.number_input("Valor")
botao = st.sidebar.button("Cadastrar venda")

# Passo 3: Salvar a venda na base de dados
if botao:
    nova_venda = [data, vendedor, produto, quantidade, valor]
    tabela.loc[len(tabela)] = nova_venda
    tabela.to_csv("vendas.csv", index=False)
    st.success("Venda cadastrada!")

# Passo 4: Mostrar a base de dados na tela
st.write("## Vendas cadastradas")
st.dataframe(tabela)

# Passo 5: Criar o dashboard
st.write("## Dashboard")
soma = tabela["valor"].sum()
st.metric("Faturamento total", f"R${soma}")

grafico = px.bar(tabela, x="vendedor", y="valor", color="produto")
st.plotly_chart(grafico)

grafico2 = px.pie(tabela, names="produto", values="valor")
st.plotly_chart(grafico2)
