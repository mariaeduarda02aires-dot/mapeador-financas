import streamlit as st
import pandas as pd
import plotly.express as px
import io


st.set_page_config(
    page_title="Dashboard de Gestão - Microempresa",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)


MAPA_CATEGORIAS = {
    'Impostos': ['das', 'imposto de renda', 'inss', 'fgts', 'simples nacional'],
    'Custos Fixos': ['aluguel', 'pro-labore', 'salario', 'contabilidade', 'internet', 'luz', 'agua'],
    'Fornecedores/Matéria-Prima': ['fornecedor', 'compra de material', 'materia prima', 'compra mercadoria'],
    'Operacional/Marketing': ['frete', 'entrega', 'software', 'assinatura', 'ads', 'google', 'facebook', 'marketing'],
    'Custos Financeiros': ['taxa de maquina', 'juros', 'tarifa bancaria', 'emprestimo'],
    'Vendas/Faturamento': ['venda', 'recebimento', 'pix recebido', 'pagamento cliente']
}

def categorizar_transacao(descricao):
    """Verifica a descrição e retorna uma categoria com base no MAPA_CATEGORIAS."""
    descricao_lower = str(descricao).lower() 
    for categoria, palavras_chave in MAPA_CATEGORIAS.items():
        for palavra in palavras_chave:
            if palavra in descricao_lower:
                return categoria
    return 'Outros Custos' 


st.sidebar.image("https://images.unsplash.com/photo-1554224155-1696413565d3?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3wzNDQ5Njd8MHwxfHNlYXJjaHwyfHxmaW5hbmNlfGVufDB8fHx8MTcyMDczNzMyN3ww&ixlib=rb-4.0.3&q=80&w=400", use_column_width=True)
st.sidebar.title("Gestor ME/MEI 💼")
st.sidebar.markdown("Faça o upload do seu extrato bancário (.csv) para análise.")

uploaded_file = st.sidebar.file_uploader("Carregue seu extrato aqui", type="csv")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Requisitos do CSV:**
* Colunas: `Data`, `Descricao_Transacao`, `Valor`
* **Despesas** devem ter valores **negativos** (ex: -150.00)
* **Receitas** devem ter valores **positivos** (ex: 3000.00)
""")


if uploaded_file is None:
    st.title("Dashboard de Gestão - Microempresa")
    st.info("Por favor, carregue seu extrato CSV na barra lateral à esquerda para começar a análise.")
else:
    try:
        df = pd.read_csv(uploaded_file)
        
 
        cols_necessarias = ['Data', 'Descricao_Transacao', 'Valor']
        if not all(col in df.columns for col in cols_necessarias):
            st.error(f"Erro: O arquivo CSV deve conter as colunas: {', '.join(cols_necessarias)}.")
            st.stop() 
            
        
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df.dropna(subset=cols_necessarias, inplace=True)
        df['Categoria'] = df['Descricao_Transacao'].apply(categorizar_transacao)

        
        df_receitas = df[df['Valor'] > 0]
        df_despesas = df[df['Valor'] < 0]
        
        faturamento_bruto = df_receitas['Valor'].sum()
        custos_totais = df_despesas['Valor'].sum() # Valor negativo
        lucro_liquido = faturamento_bruto + custos_totais
        total_impostos = df_despesas[df_despesas['Categoria'] == 'Impostos']['Valor'].sum()
        margem_lucro = (lucro_liquido / faturamento_bruto) * 100 if faturamento_bruto > 0 else 0
        carga_tributaria = (abs(total_impostos) / faturamento_bruto) * 100 if faturamento_bruto > 0 else 0

        st.title("Dashboard de Gestão - Microempresa")
        st.header("Resumo Financeiro (Mês)", divider='rainbow')

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Faturamento Bruto", f"R$ {faturamento_bruto:,.2f}")
        col2.metric("Custos Totais", f"R$ {custos_totais:,.2f}")
        col3.metric("Lucro Líquido", f"R$ {lucro_liquido:,.2f}", 
                    delta=f"{margem_lucro:,.1f}% Margem", 
                    delta_color=("normal" if lucro_liquido > 0 else "inverse"))
        col4.metric("Total em Impostos", f"R$ {total_impostos:,.2f}", 
                    delta=f"{carga_tributaria:,.1f}% do Faturamento", 
                    delta_color="inverse") 
        col5.metric("Nº de Transações", f"{df.shape[0]}")

        
        tab_graficos, tab_tabela = st.tabs(["📊 Análise Visual (Gráficos)", "📑 Tabela de Transações"])

        with tab_graficos:
            st.header("Análises Gráficas", divider='gray')
            
            
            df_gastos_categoria = df_despesas[df_despesas['Categoria'] != 'Vendas/Faturamento'].copy()
            df_gastos_categoria['Valor_Abs'] = df_gastos_categoria['Valor'].abs()
            df_agrupado = df_gastos_categoria.groupby('Categoria')['Valor_Abs'].sum().reset_index()
            df_agrupado = df_agrupado.sort_values(by='Valor_Abs', ascending=False) # Ordenado

            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                st.subheader("Distribuição dos Custos")
                fig_pie = px.pie(
                    df_agrupado,
                    names='Categoria',
                    values='Valor_Abs',
                    title='Custos por Categoria (Do maior para o menor)',
                    hole=0.3
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_graf2:
                st.subheader("Visão Geral (Barras Lado a Lado)")
                
                
                df_custos_barras = df_agrupado.rename(columns={'Categoria': 'Métrica', 'Valor_Abs': 'Valor'})
                
                
                df_faturamento = pd.DataFrame({
                    'Métrica': ['Faturamento Bruto'],
                    'Valor': [faturamento_bruto]
                })
                
                df_lucro = pd.DataFrame({
                    'Métrica': ['Lucro Líquido'],
                    'Valor': [lucro_liquido] # Mostra lucro positivo ou negativo
                })

                
                df_grafico_final = pd.concat([df_faturamento, df_custos_barras, df_lucro])
                
               
                fig_bar_grouped = px.bar(
                    df_grafico_final,
                    x='Métrica', # Cada Métrica (Faturamento, Aluguel, Imposto, Lucro) vira uma barra
                    y='Valor',
                    color='Métrica', # Cada barra tem sua própria cor
                    title='Componentes Financeiros (Do Maior para o Menor)',
                    labels={'Valor': 'Valor (R$)', 'Métrica': 'Componente Financeiro'}
                )
                
                
                fig_bar_grouped.update_layout(xaxis_categoryorder='total descending')

                st.plotly_chart(fig_bar_grouped, use_container_width=True)

            
            st.subheader("Evolução do Faturamento vs. Custos ao Longo do Tempo")
            df_receitas_dia = df_receitas.groupby(pd.Grouper(key='Data', freq='D'))['Valor'].sum().reset_index().rename(columns={'Valor': 'Faturamento'})
            df_despesas_dia = df_despesas.groupby(pd.Grouper(key='Data', freq='D'))['Valor'].sum().abs().reset_index().rename(columns={'Valor': 'Custos'})
            df_evolucao = pd.merge(df_receitas_dia, df_despesas_dia, on='Data', how='outer').fillna(0)
            df_evolucao_melted = df_evolucao.melt('Data', var_name='Tipo', value_name='Valor')
            
            fig_line = px.line(
                df_evolucao_melted, x='Data', y='Valor', color='Tipo',
                title='Evolução Diária: Faturamento vs. Custos', markers=True,
                color_discrete_map={'Faturamento': 'green', 'Custos': 'red'},
                labels={'Valor': 'Valor (R$)', 'Data': 'Dia', 'Tipo': 'Métrica'}
            )
            st.plotly_chart(fig_line, use_container_width=True)

        
        with tab_tabela:
            st.header("Todas as Transações Categorizadas", divider='gray')
            st.markdown("Verifique, filtre ou ordene suas transações.")
            
            categorias_filtro = st.multiselect(
                'Filtrar por Categoria:',
                options=df['Categoria'].unique(),
                default=df['Categoria'].unique()
            )
            df_filtrado = df[df['Categoria'].isin(categorias_filtro)]

            df_display = df_filtrado[['Data', 'Descricao_Transacao', 'Categoria', 'Valor']].copy()
            df_display['Valor'] = df_display['Valor'].map("R$ {:,.2f}".format)
            df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.error("Verifique se o seu CSV está no formato correto (separado por vírgulas) e tente novamente.")

