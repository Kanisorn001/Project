import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(page_title="Gold Price Forecasting Tool", page_icon="💰", layout="wide")

# Sidebar - Title and file uploader
st.sidebar.title("Gold Price Forecasting Tool")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

# Main page title
st.title("Gold Price Forecasting Tool")

# Load data
df = None
default_data = False
if uploaded_file is not None:
    # Use the uploaded file
    df = pd.read_csv(uploaded_file)
else:
    # If no file uploaded, try to load the default dataset
    try:
        df = pd.read_csv("gold_and_macro_data_final.csv")
        default_data = True
    except FileNotFoundError:
        df = None

# If data is available, display tabs
if df is not None:
    # Notify user of data source
    if default_data:
        st.sidebar.info("Using example dataset (gold_and_macro_data_final.csv).")
    else:
        st.sidebar.success(f"Uploaded file `{uploaded_file.name}` successfully!")
    # Preprocess data (convert Date column to datetime, if present)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.sort_values('Date')
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Data Preview", "Summary Statistics", "Visualizations", "Forecast"])
    with tab1:
        st.subheader("Data Preview")
        st.write("Showing the first 5 rows of the dataset:")
        st.dataframe(df.head())
    with tab2:
        st.subheader("Summary Statistics")
        # Display dataset dimensions
        num_rows, num_cols = df.shape
        st.write(f"**Dataset dimensions:** {num_rows} rows, {num_cols} columns")
        # Compute summary stats for numeric columns
        numeric_df = df.select_dtypes(include='number')
        if not numeric_df.empty:
            means = numeric_df.mean().round(2)
            medians = numeric_df.median().round(2)
            missing = numeric_df.isna().sum()
            summary_df = pd.DataFrame({
                'Mean': means,
                'Median': medians,
                'Missing Values': missing
            })
            st.table(summary_df)
        else:
            st.write("No numeric columns found in the dataset.")
    with tab3:
        st.subheader("Visualizations")
        # Line chart of Gold Price over time
        if 'Date' in df.columns and 'Gold_Price_USD' in df.columns:
            fig_line = px.line(df, x='Date', y='Gold_Price_USD', title="Gold Price Over Time")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.write("Unable to plot Gold Price over time (Date or Gold_Price_USD column is missing).")
        # Correlation heatmap for numeric features
        numeric_df = df.select_dtypes(include='number')
        if not numeric_df.empty:
            corr = numeric_df.corr()
            fig_corr = px.imshow(
                corr, text_auto=True, color_continuous_scale="RdBu", zmin=-1, zmax=1,
                title="Correlation Heatmap"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.write("Unable to display correlation heatmap (no numeric data).")
    with tab4:
        st.subheader("Forecast")
        st.info("Forecasting functionality is not implemented yet. Stay tuned for future updates!")
else:
    # No data available
    st.info("Please upload a CSV file from the sidebar to proceed.")
