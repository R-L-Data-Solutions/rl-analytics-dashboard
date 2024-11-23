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

# Custom CSS para o logo
st.markdown("""
    <style>
    .logo-container {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1E88E5 0%, #005CAB 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .company-name {
        font-size: 3.5rem;
        font-weight: bold;
        color: white;
        margin: 0;
    }
    .tagline {
        font-size: 1.2rem;
        color: #E0E0E0;
        margin-top: 0.5rem;
    }
    .logo-symbol {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    </style>
    
    <div class="logo-container">
        <div class="logo-symbol">🔄📊</div>
        <div class="company-name">R&L Data Solutions</div>
        <div class="tagline">Transformando Dados em Resultados</div>
    </div>
""", unsafe_allow_html=True)

# Funções de Análise
def calcular_rfm(df):
    """Calcula métricas RFM (Recência, Frequência, Valor Monetário)"""
    hoje = pd.to_datetime(df['Data']).max()
    
    rfm = df.groupby('Cliente_ID').agg({
        'Data': lambda x: (hoje - pd.to_datetime(x.max())).days,  # Recência
        'Cliente_ID': 'count',  # Frequência
        'Valor': lambda x: (x * df.loc[x.index, 'Quantidade']).sum()  # Valor Monetário
    }).rename(columns={
        'Data': 'Recencia',
        'Cliente_ID': 'Frequencia',
        'Valor': 'Valor_Monetario'
    })
    
    return rfm

def analise_cesta(df):
    """Análise de produtos frequentemente comprados juntos"""
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
    """Análise de tendências temporais"""
    df['Data'] = pd.to_datetime(df['Data'])
    vendas_diarias = df.groupby('Data').agg({
        'Valor': lambda x: (x * df.loc[x.index, 'Quantidade']).sum()
    }).reset_index()
    
    # Calcular tendência
    X = np.arange(len(vendas_diarias))
    y = vendas_diarias['Valor'].values
    slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
    
    tendencia = 'crescente' if slope > 0 else 'decrescente'
    confianca = r_value ** 2
    
    return vendas_diarias, tendencia, confianca

# Title and description
st.title("R&L Smart Analytics Dashboard")
st.markdown("""
    Transform your business data into actionable insights
    
    Upload your sales data to discover:
    - Customer Segmentation (RFM Analysis)
    - Product Associations
    - Sales Trends
    - Performance Analytics
""")

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
            
            # Data info
            st.write("Dataset Info:")
            st.write(f"Rows: {df.shape[0]}")
            st.write(f"Columns: {df.shape[1]}")
            
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

# Main content
if 'df' in locals():
    # Métricas Principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_vendas = (df['Valor'] * df['Quantidade']).sum()
    num_clientes = df['Cliente_ID'].nunique()
    ticket_medio = total_vendas / len(df.groupby(['Cliente_ID', 'Data']))
    taxa_fidelidade = (df['Cliente_Fidelidade'] == True).mean() * 100
    
    with col1:
        st.metric(
            label="Total Sales",
            value=f"R$ {total_vendas:,.2f}",
            delta="Total revenue"
        )
    
    with col2:
        st.metric(
            label="Unique Customers",
            value=f"{num_clientes:,}",
            delta="Customer base"
        )
    
    with col3:
        st.metric(
            label="Average Ticket",
            value=f"R$ {ticket_medio:.2f}",
            delta="Per transaction"
        )
    
    with col4:
        st.metric(
            label="Loyalty Rate",
            value=f"{taxa_fidelidade:.1f}%",
            delta="Of customer base"
        )
    
    # RFM Analysis
    st.header("🎯 Customer Segmentation (RFM Analysis)")
    rfm = calcular_rfm(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.scatter(rfm, x='Recencia', y='Valor_Monetario', 
                        size='Frequencia', title='Customer Segments')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Segmentar clientes (usando cut ao invés de qcut para evitar bins duplicados)
        rfm['R'] = pd.cut(rfm['Recencia'], bins=3, labels=['Alta', 'Média', 'Baixa'])
        rfm['F'] = pd.cut(rfm['Frequencia'], bins=3, labels=['Baixa', 'Média', 'Alta'])
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
        fig = px.pie(rfm, names='Segmento', title='Customer Segments Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    # Product Analysis
    st.header("🛒 Product Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vendas_categoria = df.groupby('Categoria').agg({
            'Valor': lambda x: (x * df.loc[x.index, 'Quantidade']).sum()
        }).sort_values('Valor', ascending=False)
        
        fig = px.bar(vendas_categoria, title='Sales by Category')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Análise de Cesta
        pares_produtos = analise_cesta(df)
        if not pares_produtos.empty:
            st.subheader("Frequently Bought Together")
            st.dataframe(pares_produtos)
    
    # Trend Analysis
    st.header("📈 Trend Analysis")
    
    vendas_diarias, tendencia, confianca = analise_tendencias(df)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.line(vendas_diarias, x='Data', y='Valor', 
                     title='Daily Sales Evolution')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.metric(
            label="Sales Trend",
            value=tendencia.title(),
            delta=f"Confidence: {confianca:.1%}"
        )
    
    # Performance Insights
    st.header("🎯 Performance Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Performance por filial
        vendas_filial = df.groupby('Filial').agg({
            'Valor': lambda x: (x * df.loc[x.index, 'Quantidade']).sum()
        }).sort_values('Valor', ascending=True)
        
        fig = px.bar(vendas_filial, orientation='h', 
                    title='Sales by Store')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Horários de pico
        df['Hora'] = pd.to_datetime(df['Horario']).dt.hour
        vendas_hora = df.groupby('Hora').agg({
            'Valor': lambda x: (x * df.loc[x.index, 'Quantidade']).sum()
        })
        
        fig = px.line(vendas_hora, title='Sales by Hour')
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Please upload a data file in the sidebar to begin analysis")

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
