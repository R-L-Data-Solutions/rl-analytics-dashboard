import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="R&L Smart Analytics",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("R&L Smart Analytics Dashboard")
st.markdown("Transform your business data into actionable insights")

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
    # Create three columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Records",
            value=len(df),
            delta="From your dataset"
        )
    
    with col2:
        st.metric(
            label="Numeric Columns",
            value=len(df.select_dtypes(include=['int64', 'float64']).columns),
            delta="Available for analysis"
        )
    
    with col3:
        st.metric(
            label="Date Columns",
            value=len(df.select_dtypes(include=['datetime64']).columns),
            delta="For time series"
        )
    
    # Automatic visualizations
    st.header("Automatic Insights")
    
    # For numeric columns
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) > 0:
        st.subheader("Numeric Data Distribution")
        selected_numeric = st.selectbox("Select column for analysis:", numeric_cols)
        
        fig = px.histogram(df, x=selected_numeric, title=f"Distribution of {selected_numeric}")
        st.plotly_chart(fig, use_container_width=True)
        
        # Basic statistics
        st.write("Basic Statistics:")
        stats = df[selected_numeric].describe()
        st.dataframe(stats)
    
    # For categorical columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    if len(categorical_cols) > 0:
        st.subheader("Categorical Data Analysis")
        selected_cat = st.selectbox("Select categorical column:", categorical_cols)
        
        fig = px.pie(df, names=selected_cat, title=f"Distribution of {selected_cat}")
        st.plotly_chart(fig, use_container_width=True)
    
    # Correlation matrix for numeric columns
    if len(numeric_cols) > 1:
        st.subheader("Correlation Analysis")
        corr_matrix = df[numeric_cols].corr()
        fig = px.imshow(corr_matrix, title="Correlation Matrix")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Please upload a data file in the sidebar to begin analysis")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by R&L Data Solutions")
