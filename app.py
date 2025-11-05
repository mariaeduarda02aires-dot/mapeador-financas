
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA E SIDEBAR ---
# Usamos 'wide' para ocupar a tela toda e 'sidebar' para o upload
st.set_page_config(
    page_title="Dashboard de Gestão - Microempresa",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. NOVAS CATEGORIAS (LÓGICA DE NEGÓCIO) ---
# Substituímos as categorias pessoais por categorias empresariais
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
    descricao_lower = str(descricao).lower() # Garante que a descrição seja string
    for categoria, palavras_chave in MAPA_CATEGORIAS.items():
        for palavra in palavras_chave:
            if palavra in descricao_lower:
                return categoria
    return 'Outros Custos' # Categoria padrão para despesas não identificadas

# --- 3. MELHORIA DE UI: SIDEBAR PARA UPLOAD ---
# Movemos o upload da tela principal para a barra lateral
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


# --- 4. TELA PRINCIPAL (LÓGICA DO DASHBOARD) ---

# Se o arquivo não for enviado, a tela principal fica limpa
if uploaded_file is None:
    st.title("Dashboard de Gestão - Microempresa")
    st.info("Por favor, carregue seu extrato CSV na barra lateral à esquerda para começar a análise.")
else:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Verificação das colunas
        cols_necessarias = ['Data', 'Descricao_Transacao', 'Valor']
        if not all(col in df.columns for col in cols_necessarias):
            st.error(f"Erro: O arquivo CSV deve conter as colunas: {', '.join(cols_necessarias)}.")
            st.stop() # Para a execução se as colunas estiverem erradas
            
        # --- 4.1 Limpeza e Processamento ---
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df.dropna(subset=cols_necessarias, inplace=True)
        df['Categoria'] = df['Descricao_Transacao'].apply(categorizar_transacao)

        # --- 4.2 NOVOS KPIs (Métricas de Negócio) ---
        df_receitas = df[df['Valor'] > 0]
        df_despesas = df[df['Valor'] < 0]
        
        faturamento_bruto = df_receitas['Valor'].sum()
        custos_totais = df_despesas['Valor'].sum() # Valor negativo
        lucro_liquido = faturamento_bruto + custos_totais
        
        # KPI Específico de Impostos
        total_impostos = df_despesas[df_despesas['Categoria'] == 'Impostos']['Valor'].sum()
        
        # KPIs Percentuais (mais profissionais)
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
        
        # Destaque para Impostos
        col4.metric("Total em Impostos", f"R$ {total_impostos:,.2f}", 
                    delta=f"{carga_tributaria:,.1f}% do Faturamento", 
                    delta_color="inverse") # Vermelho para custo
        
        col5.metric("Nº de Transações", f"{df.shape[0]}")


        # --- 4.3 MELHORIA DE UI: ABAS (TABS) ---
        # Organizamos os gráficos e a tabela em abas para limpar a interface
        
        tab_graficos, tab_tabela = st.tabs(["📊 Análise Visual (Gráficos)", "📑 Tabela de Transações"])

        with tab_graficos:
            st.header("Análises Gráficas", divider='gray')
            
            # --- Preparação dos Dados para Gráficos ---
            df_gastos_categoria = df_despesas[df_despesas['Categoria'] != 'Vendas/Faturamento'].copy()
            df_gastos_categoria['Valor_Abs'] = df_gastos_categoria['Valor'].abs()
            df_agrupado = df_gastos_categoria.groupby('Categoria')['Valor_Abs'].sum().reset_index()
            df_agrupado = df_agrupado.sort_values(by='Valor_Abs', ascending=False) # Ordenado (didático)

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
                st.subheader("Fluxo de Caixa (Cascata)")
                df_despesas_waterfall = df_agrupado.copy()
                df_despesas_waterfall['Valor'] = -df_despesas_waterfall['Valor_Abs'] # Converte para negativo

                x_labels = ["Faturamento"] + df_despesas_waterfall['Categoria'].tolist() + ["Lucro Líquido"]
                y_values = [faturamento_bruto] + df_despesas_waterfall['Valor'].tolist() + [lucro_liquido]
                measures = ["absolute"] + ["relative"] * len(df_despesas_waterfall) + ["total"]
                
                fig_waterfall = go.Figure(go.Waterfall(
                    name="Fluxo de Caixa", orientation="v", measure=measures,
                    x=x_labels, y=y_values,
                    text=[f"R$ {v:,.2f}" for v in y_values],
                    textposition="auto",
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    decreasing={"marker": {"color": "#d62728"}}, # Custos
                    totals={"marker": {"color": "#2ca02c"}}      # Faturamento e Lucro
                ))
                fig_waterfall.update_layout(title="Faturamento ➔ Custos ➔ Lucro Líquido")
                st.plotly_chart(fig_waterfall, use_container_width=True)

            # --- Gráfico de Linha (Melhorado) ---
            st.subheader("Evolução do Faturamento vs. Custos ao Longo do Tempo")
            
            # Agrupa faturamento por dia
            df_receitas_dia = df_receitas.groupby(pd.Grouper(key='Data', freq='D'))['Valor'].sum().reset_index()
            df_receitas_dia = df_receitas_dia.rename(columns={'Valor': 'Faturamento'})

            # Agrupa custos por dia
            df_despesas_dia = df_despesas.groupby(pd.Grouper(key='Data', freq='D'))['Valor'].sum().abs().reset_index()
            df_despesas_dia = df_despesas_dia.rename(columns={'Valor': 'Custos'})
            
            # Junta os dois dataframes
            df_evolucao = pd.merge(df_receitas_dia, df_despesas_dia, on='Data', how='outer').fillna(0)
            
            # "Derrete" (melt) o dataframe para o formato ideal do Plotly
            df_evolucao_melted = df_evolucao.melt('Data', var_name='Tipo', value_name='Valor')

            fig_line = px.line(
                df_evolucao_melted,
                x='Data',
                y='Valor',
                color='Tipo', # Cria duas linhas (Faturamento e Custos)
                title='Evolução Diária: Faturamento vs. Custos',
                markers=True,
                color_discrete_map={'Faturamento': 'green', 'Custos': 'red'},
                labels={'Valor': 'Valor (R$)', 'Data': 'Dia', 'Tipo': 'Métrica'}
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with tab_tabela:
            st.header("Todas as Transações Categorizadas", divider='gray')
            st.markdown("Verifique, filtre ou ordene suas transações.")
            
            # Filtro interativo de Categoria
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

    # Captura de erro (caso o CSV esteja corrompido)
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.error("Verifique se o seu CSV está no formato correto (separado por vírgulas) e tente novamente.")




