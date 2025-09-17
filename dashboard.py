import streamlit as st
import pandas as pd
from bq_database import get_inventory_records, get_all_product_stock

def show_dashboard():
    st.markdown("### 📊 Dashboard Overview")
    
    # Fetch live stock data from the new 'product_stock' table
    live_stock_df = get_all_product_stock()
    
    # Fetch all transaction data from the new 'inventory_transactions' table
    transactions_df = get_inventory_records()

    if live_stock_df.empty:
        st.info("No current inventory data available.")
        return

    # Calculate key metrics from the live stock and transactions
    total_current_stock = int(live_stock_df["current_quantity"].sum())
    
    # Metrics from the transaction log
    total_production = int(transactions_df[transactions_df['entry_type'] == 'Production']['quantity_change'].sum())
    total_purchase = int(transactions_df[transactions_df['entry_type'] == 'Purchase']['quantity_change'].sum())
    total_sales = int(transactions_df[transactions_df['entry_type'] == 'Sales']['quantity_change'].sum())
    total_breakage = int(transactions_df[transactions_df['entry_type'] == 'Breakage']['quantity_change'].sum())
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Production", total_production)
    col2.metric("Total Purchase", total_purchase)
    col3.metric("Total Sales", total_sales)
    col4.metric("Total Breakage", total_breakage)
    col5.metric("Total Current Stock", total_current_stock)
    
    st.subheader("Current Inventory Stock")

    # --- MODIFIED SECTION ---
    # 1. Define the list of columns you want to display
    columns_to_show = ['product_name', 'color', 'packing_option', 'product_grade', 'current_quantity']
    
    # 2. Pass the filtered DataFrame to st.dataframe
    st.dataframe(live_stock_df[columns_to_show], use_container_width=True)