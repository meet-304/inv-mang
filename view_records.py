import streamlit as st
import pandas as pd
from datetime import datetime
from bq_database import get_inventory_records

def show_view_records():
    st.markdown("### 📋 Inventory Transaction Log")
    st.info("This table shows every single inventory movement, serving as a complete audit log.")

    # Fetch records from BigQuery
    df = get_inventory_records()

    if df.empty:
        st.info("No transaction records found.")
        return

    # Convert timestamp for better filtering
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # Add filters for product_name, color, date, etc.
    with st.expander("🔎 Filter Records", expanded=True):
        ## --- MODIFIED: Added a fourth column for the new filter ---
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            product_name = st.selectbox("Product Name", ["All"] + sorted(df["product_name"].unique().tolist()))
        with col2:
            color = st.selectbox("Color", ["All"] + sorted(df["color"].unique().tolist()))
        with col3:
            entry_type = st.selectbox("Entry Type", ["All"] + sorted(df["entry_type"].unique().tolist()))
        ## --- NEW: Filter by Invoice Number ---
        with col4:
            invoice_filter = st.text_input("Filter by Invoice #")

        filtered_df = df.copy()
        if product_name != "All":
            filtered_df = filtered_df[filtered_df["product_name"] == product_name]
        if color != "All":
            filtered_df = filtered_df[filtered_df["color"] == color]
        if entry_type != "All":
            filtered_df = filtered_df[filtered_df["entry_type"] == entry_type]
        ## --- NEW: Logic to apply the invoice filter ---
        if invoice_filter:
            # Use .str.contains for partial matches, case-insensitive, and handle empty cells
            filtered_df = filtered_df[filtered_df["invoice_number"].str.contains(invoice_filter, case=False, na=False)]

    # Prepare DataFrame for Display
    if not filtered_df.empty:
        df_display = filtered_df.copy()
        df_display['transaction_date'] = df_display['transaction_date'].dt.strftime('%Y-%m-%d')
        
        ## --- MODIFIED: Added 'invoice_number' to the list of columns to show ---
        columns_to_display = [
            'transaction_date', 
            'invoice_number',
            'product_name', 
            'color', 
            'packing_option', 
            'product_grade', 
            'entry_type', 
            'quantity_change', 
            'user_name'
        ]
        
        # This makes sure the app doesn't crash if a column doesn't exist yet
        columns_to_display = [col for col in columns_to_display if col in df_display.columns]
        
        st.dataframe(df_display[columns_to_display], use_container_width=True)
    else:
        st.dataframe(filtered_df, use_container_width=True)

    st.caption(f"Total records: {len(filtered_df)}")