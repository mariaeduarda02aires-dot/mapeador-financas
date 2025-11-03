
import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- Configuração da Página ---
st.set_page_config(
    page_title="Rastreador de Finanças",
    page_icon="💰",
    layout="wide"
)

# --- Função de Categorização ---
MAPA_CATEGORIAS = {
    'Alimentação': ['ifood', 'restaurante', 'mercado', 'supermercado', 'pao de acucar', 'padaria'],
    'Transporte': ['uber', '99', 'taxi', 'onibus', 'metro', 'gasolina', 'posto', 'estacionamento'],
    'Moradia': ['aluguel', 'condominio', 'conta de luz', 'enel', 'internet', 'vivo', 'claro', 'agua'],
    'Assinaturas': ['netflix', 'spotify', 'hbo', 'disney', 'prime video', 'youtube premium'],
    'Saúde': ['farmacia', 'droga raia', 'plano de saude', 'medico', 'consulta'],
    'Lazer': ['cinema', 'show', 'bar', 'viagem', 'livraria', 'steam'],
    'Receitas': ['salario', 'pix recebido', 'transferencia recebida', 'rendimento']
}

def categorizar_transacao(descricao):
    """Verifica a descrição e retorna uma categoria com base no MAPA_CATEGORIAS."""
    descricao_lower = descricao.lower()
    for categoria, palavras_chave in MAPA_CATEGORIAS.items():
        for palavra in palavras_chave:
            if palavra in descricao_lower:
                return categoria
    return 'Outros' # Categoria padrão se nenhuma palavra-chave for encontrada

# --- Título e Descrição ---
st.title("💰 Rastreador de Finanças Pessoais")
st.markdown("""
Use esta ferramenta para ter uma visão clara de suas finanças.
**Basta carregar seu extrato bancário em formato CSV** e a análise será gerada automaticamente.
""")

st.markdown("""
**Requisitos do CSV:**
1.  Deve conter as colunas: `Data`, `Descricao_Transacao` e `Valor`.
2.  A coluna `Valor` deve ser numérica (use `.` como separador decimal).
3.  **Despesas devem ter valores negativos** (ex: -50.25) e **Receitas devem ter valores positivos** (ex: 1200.00).
""")

# --- Upload do Arquivo ---
uploaded_file = st.file_uploader("Carregue seu extrato (CSV)", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        if not all(col in df.columns for col in ['Data', 'Descricao_Transacao', 'Valor']):
            st.error(f"Erro: O arquivo CSV deve conter as colunas 'Data', 'Descricao_Transacao' e 'Valor'. Colunas encontradas: {list(df.columns)}")
        else:
            # --- 1. Processamento e Limpeza dos Dados ---
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            df.dropna(subset=['Valor', 'Data', 'Descricao_Transacao'], inplace=True)

            # Aplica a função de categorização para criar uma nova coluna
            df['Categoria'] = df['Descricao_Transacao'].apply(categorizar_transacao)

            # --- 2. Cálculo dos KPIs (Métricas) ---
            df_receitas = df[df['Valor'] > 0]
            df_despesas = df[df['Valor'] < 0]
            
            total_receitas = df_receitas['Valor'].sum()
            total_despesas = df_despesas['Valor'].sum() # Este valor é negativo
            saldo = total_receitas + total_despesas

            st.header("Resumo Financeiro", divider='rainbow')
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Receita Total", f"R$ {total_receitas:,.2f}", "Positivo")
            col2.metric("Despesa Total", f"R$ {total_despesas:,.2f}", "Negativo")
            
            saldo_delta = "R$ 0,00"
            if saldo > 0:
                saldo_delta = f"R$ {saldo:,.2f} (Sobra)"
            elif saldo < 0:
                saldo_delta = f"R$ {saldo:,.2f} (Déficit)"
            
            col3.metric("Saldo", f"R$ {saldo:,.2f}", delta=saldo_delta, delta_color=("off" if saldo == 0 else "normal"))

            # --- 3. Gráficos Principais (Pizza e Barras) ---
            st.header("Análise Detalhada", divider='rainbow')

            df_gastos_categoria = df_despesas[df_despesas['Categoria'] != 'Receitas'].copy()
            df_gastos_categoria['Valor_Abs'] = df_gastos_categoria['Valor'].abs()
            df_agrupado = df_gastos_categoria.groupby('Categoria')['Valor_Abs'].sum().reset_index()

            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                st.subheader("Distribuição de Despesas")
                fig_pie = px.pie(
                    df_agrupado,
                    names='Categoria',
                    values='Valor_Abs',
                    title='Gastos por Categoria',
                    hole=0.3, # Transforma em "Donut"
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

            # ==========================================================
            # --- SEÇÃO DO GRÁFICO ALTERADA (CONFORME SOLICITADO) ---
            # ==========================================================
            with col_graf2:
                st.subheader("Despesa vs. Saldo")
                
                # Criamos um DataFrame com apenas as duas métricas
                df_resumo_bar = pd.DataFrame({
                    'Métrica': ['Despesa Total', 'Saldo Final'],
                    'Valor': [total_despesas, saldo] # Usamos os valores reais (despesa é negativa)
                })
                
                fig_bar = px.bar(
                    df_resumo_bar,
                    x='Métrica',
                    y='Valor',
                    title='Comparativo Despesa Total vs. Saldo Final',
                    color='Métrica', # Cores diferentes para cada barra
                    color_discrete_map={
                        'Despesa Total': 'red',
                        'Saldo Final': 'blue'
                        },
                    text='Valor' # Mostra o valor na barra
                )
                fig_bar.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)
            # ==========================================================
            # --- FIM DA SEÇÃO ALTERADA ---
            # ==========================================================

            # --- 4. GRÁFICO (Gastos ao Longo do Tempo) ---
            st.subheader("Gastos ao Longo do Tempo",)
            
            # Prepara os dados: agrupa gastos por dia
            df_despesas_dia = df_despesas.copy()
            df_despesas_dia['Valor_Abs'] = df_despesas_dia['Valor'].abs()
            # Agrupa pela data e soma os valores absolutos
            df_gastos_por_dia = df_despesas_dia.groupby('Data')['Valor_Abs'].sum().reset_index()

            fig_line = px.line(
                df_gastos_por_dia,
                x='Data',
                y='Valor_Abs',
                title='Evolução dos Gastos Diários',
                markers=True, # Adiciona marcadores para cada dia
                labels={'Valor_Abs': 'Valor Gasto (R$)', 'Data': 'Dia'} # Renomeia os eixos
            )
            fig_line.update_traces(textposition="bottom right")
            st.plotly_chart(fig_line, use_container_width=True)


            # --- 5. Tabela de Dados (Antigo passo 4) ---
            st.header("Transações Detalhadas", divider='rainbow')
            st.markdown("Veja seu extrato categorizado. Você pode ordenar clicando no cabeçalho das colunas.")
            
            df_display = df[['Data', 'Descricao_Transacao', 'Categoria', 'Valor']].copy()
            df_display['Valor'] = df_display['Valor'].map("R$ {:,.2f}".format)
            df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y') # Formata data
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.error("Verifique se o seu CSV está no formato correto (separado por vírgulas) e tente novamente.")

else:
    st.info("Aguardando o upload do seu extrato CSV... 📄")




