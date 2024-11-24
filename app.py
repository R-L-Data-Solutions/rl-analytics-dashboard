import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from scipy import stats

# Page config
st.set_page_config(
    page_title="R&L Smart Analytics",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 300px;
    max-width: 400px;
}
.logo-container {
    background: linear-gradient(90deg, #1E88E5 0%, #005CAB 100%);
    padding: 2rem;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 2rem;
}
.logo-symbol {
    font-size: 4rem;
    margin-bottom: 1rem;
    color: white;
}
.company-name {
    color: white;
    font-size: 2.5rem;
    font-weight: bold;
    margin: 0;
}
.tagline {
    color: #E0E0E0;
    font-size: 1.5rem;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# Logo and Header
st.markdown("""
<div class="logo-container">
    <div class="logo-symbol">🔄📊</div>
    <div class="company-name">R&L Data Solutions</div>
    <div class="tagline">Análise Inteligente R&L</div>
</div>
""", unsafe_allow_html=True)

# Funções de Análise
def calcular_rfm(df):
    hoje = pd.to_datetime(df['Data']).max()
    rfm = df.groupby('Cliente_ID').agg({
        'Data': lambda x: (hoje - pd.to_datetime(x.max())).days,
        'Cliente_ID': 'count',
        'Valor': lambda x: (x * df.loc[x.index, 'Quantidade']).sum()
    }).rename(columns={
        'Data': 'Recencia',
        'Cliente_ID': 'Frequencia',
        'Valor': 'Valor_Monetario'
    })
    return rfm

def analise_cesta(df):
    df_grouped = df.groupby(['Cliente_ID', 'Data'])['Produto'].agg(list).reset_index()
    pares = []
    for produtos in df_grouped['Produto']:
        if len(produtos) > 1:
            for i in range(len(produtos)):
                for j in range(i+1, len(produtos)):
                    pares.append(tuple(sorted([produtos[i], produtos[j]])))
    
    if pares:
        from collections import Counter
        return pd.DataFrame(Counter(pares).most_common(10), 
                          columns=['Par_Produtos', 'Frequencia'])
    return pd.DataFrame()

def analise_tendencias(df):
    df['Data'] = pd.to_datetime(df['Data'])
    vendas_diarias = df.groupby('Data').agg({
        'Valor': lambda x: (x * df.loc[x.index, 'Quantidade']).sum()
    }).reset_index()
    
    X = np.arange(len(vendas_diarias))
    y = vendas_diarias['Valor'].values
    slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
    
    tendencia = 'crescente' if slope > 0 else 'decrescente'
    confianca = r_value ** 2
    
    return vendas_diarias, tendencia, confianca

# Sidebar
with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success("Data loaded successfully!")
            st.write("Data Preview:")
            st.dataframe(df.head())
            
            st.write("Dataset Info:")
            st.write(f"Rows: {df.shape[0]}")
            st.write(f"Columns: {df.shape[1]}")
            
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

# Main content
if 'uploaded_file' in locals() and uploaded_file is not None:
    # Métricas Principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_vendas = (df['Valor'] * df['Quantidade']).sum()
    num_clientes = df['Cliente_ID'].nunique()
    ticket_medio = total_vendas / len(df.groupby(['Cliente_ID', 'Data']))
    taxa_fidelidade = len(df[df['Cliente_ID'].duplicated()]) / len(df) * 100
    
    with col1:
        st.metric("Total Sales", f"R$ {total_vendas:,.2f}")
    with col2:
        st.metric("Unique Customers", f"{num_clientes:,}")
    with col3:
        st.metric("Average Ticket", f"R$ {ticket_medio:.2f}")
    with col4:
        st.metric("Loyalty Rate", f"{taxa_fidelidade:.1f}%")
    
    # RFM Analysis
    st.header("🎯 Customer Segmentation (RFM Analysis)")
    rfm = calcular_rfm(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.scatter(rfm, x='Recencia', y='Valor_Monetario', 
                        size='Frequencia', title='Customer Segments')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Usando qcut com tratamento de duplicatas
        try:
            rfm['R'] = pd.qcut(rfm['Recencia'], q=3, labels=['Alta', 'Média', 'Baixa'], duplicates='drop')
        except ValueError:
            rfm['R'] = pd.cut(rfm['Recencia'], bins=3, labels=['Alta', 'Média', 'Baixa'])
            
        try:
            rfm['F'] = pd.qcut(rfm['Frequencia'], q=3, labels=['Baixa', 'Média', 'Alta'], duplicates='drop')
        except ValueError:
            rfm['F'] = pd.cut(rfm['Frequencia'], bins=3, labels=['Baixa', 'Média', 'Alta'])
            
        try:
            rfm['M'] = pd.qcut(rfm['Valor_Monetario'], q=3, labels=['Baixo', 'Médio', 'Alto'], duplicates='drop')
        except ValueError:
            rfm['M'] = pd.cut(rfm['Valor_Monetario'], bins=3, labels=['Baixo', 'Médio', 'Alto'])
        
        def segmentar_cliente(row):
            if row['R'] == 'Alta' and row['F'] == 'Alta' and row['M'] == 'Alto':
                return 'Champions'
            elif row['R'] == 'Baixa' and row['F'] == 'Baixa':
                return 'Lost'
            elif row['R'] == 'Alta' and row['M'] == 'Alto':
                return 'Loyal'
            else:
                return 'Regular'
        
        rfm['Segmento'] = rfm.apply(segmentar_cliente, axis=1)
        
        segmentos = rfm['Segmento'].value_counts()
        fig = px.pie(values=segmentos.values, names=segmentos.index,
                    title='Customer Segments Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    # Sales Trends
    st.header("📈 Sales Trends")
    vendas_diarias, tendencia, confianca = analise_tendencias(df)
    
    fig = px.line(vendas_diarias, x='Data', y='Valor',
                  title=f'Sales Evolution (Trend: {tendencia}, R² = {confianca:.2f})')
    st.plotly_chart(fig, use_container_width=True)
    
    # Product Analysis
    st.header("🛒 Product Analysis")
    produtos_populares = df.groupby('Produto')['Quantidade'].sum().sort_values(ascending=False)
    
    fig = px.bar(x=produtos_populares.head(10).index, y=produtos_populares.head(10).values,
                 title='Top 10 Products by Sales Volume')
    st.plotly_chart(fig, use_container_width=True)
    
    # Basket Analysis
    st.header("🧺 Basket Analysis")
    cesta = analise_cesta(df)
    if not cesta.empty:
        fig = px.bar(cesta, x='Frequencia', y='Par_Produtos',
                    title='Most Common Product Pairs',
                    orientation='h')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for basket analysis")

else:
    st.info("Please upload your data file to start the analysis")

# Footer
st.markdown("---")

# Seção de Contato
st.header("🤝 Interessado na Versão Premium?")
st.markdown("""
    A versão premium inclui recursos avançados como:
    - 🔮 **Previsão de Vendas** com Machine Learning
    - 🎯 **Segmentação Avançada** de Clientes
    - 📊 **Dashboards Personalizados**
    - 🔄 **Integração em Tempo Real**
    - 📱 **App Mobile**
    - 👩‍💼 **Consultoria Especializada**
    
    ### Entre em Contato:
    - 📧 Email: ronaldooliveira82@hotmail.com
    - 📱 WhatsApp: (15) 99248-4464
    
    Nossa equipe terá prazer em demonstrar todas as funcionalidades premium!
""")

st.markdown("""
    Made with ❤️ by R&L Data Solutions
    
    **Free Version Features:**
    - RFM Customer Segmentation
    - Product Association Analysis
    - Trend Detection
    - Performance Analytics
""")
