import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from bq_database import get_inventory_records, get_all_product_stock
from datetime import datetime, timedelta

def show_analytics():
    st.markdown("### 📈 Advanced Analytics")
    
    # --- CHANGE 1: Initialize the slider's value in session_state ---
    # This sets the default value only once per session.
    if 'low_stock_threshold' not in st.session_state:
        st.session_state.low_stock_threshold = 20

    # Load data from BigQuery
    transactions_df = get_inventory_records()
    live_stock_df = get_all_product_stock()

    if live_stock_df.empty or transactions_df.empty:
        st.info("Insufficient data for analytics. Please add transactions.")
        return

    # --- Data Preprocessing ---
    transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
    transactions_df['quantity_change'] = pd.to_numeric(transactions_df['quantity_change'])
    live_stock_df['current_quantity'] = pd.to_numeric(live_stock_df['current_quantity'])

    # --- Page Filters ---
    with st.expander("Filter Options", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            min_date = transactions_df['transaction_date'].min().date()
            max_date = datetime.now().date()
            start_date, end_date = st.date_input(
                "Select Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        
        with col2:
            product_list = ["All"] + sorted(transactions_df['product_name'].unique().tolist())
            selected_products = st.multiselect("Select Products", product_list, default=["All"])

    # --- Filtering Logic ---
    start_datetime = pd.to_datetime(start_date).tz_localize('UTC')
    end_datetime = (pd.to_datetime(end_date) + timedelta(days=1)).tz_localize('UTC')

    filtered_transactions = transactions_df[
        (transactions_df['transaction_date'] >= start_datetime) & 
        (transactions_df['transaction_date'] < end_datetime)
    ]
    
    if "All" not in selected_products and selected_products:
        filtered_transactions = filtered_transactions[filtered_transactions['product_name'].isin(selected_products)]
        filtered_stock = live_stock_df[live_stock_df['product_name'].isin(selected_products)]
    else:
        filtered_stock = live_stock_df.copy()

    if filtered_transactions.empty:
        st.warning("No transaction data found for the selected filters.")
        return

    # --- KPI Section ---
    st.markdown("#### Key Performance Indicators (KPIs)")
    
    sales_df = filtered_transactions[filtered_transactions['entry_type'] == 'Sales']
    total_sales_quantity = sales_df['quantity_change'].sum()
    
    production_df = filtered_transactions[filtered_transactions['entry_type'] == 'Production']
    
    avg_stock_quantity = filtered_stock['current_quantity'].mean()
    stock_turnover = (total_sales_quantity / avg_stock_quantity) if avg_stock_quantity else 0
    best_seller = sales_df.groupby('product_name')['quantity_change'].sum().idxmax() if not sales_df.empty else "N/A"

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales (Units)", f"{total_sales_quantity:,.0f}")
    col2.metric("Stock Turnover Rate", f"{stock_turnover:.2f}")
    col3.metric("Best Selling Product", best_seller)
    
    st.write("---")

    # --- Detailed Chart Tabs ---
    tab1, tab2, tab3 = st.tabs(["📊 Performance Analysis", "🌊 Inventory Flow (In/Out)", "🎨 Stock Distribution"])

    with tab1:
        st.subheader("Product Performance")
        top_5_selling = sales_df.groupby('product_name')['quantity_change'].sum().nlargest(5).reset_index()
        fig_top_selling = px.bar(
            top_5_selling, x='product_name', y='quantity_change', 
            title="Top 5 Best-Selling Products", labels={'product_name': 'Product', 'quantity_change': 'Units Sold'}
        )
        st.plotly_chart(fig_top_selling, use_container_width=True)
        
        slowest_5_moving = filtered_stock.nlargest(5, 'current_quantity')
        fig_slowest_moving = px.bar(
            slowest_5_moving, x='product_name', y='current_quantity', 
            title="Top 5 Slowest-Moving Products (Highest Stock)", labels={'product_name': 'Product', 'current_quantity': 'Units in Stock'}
        )
        st.plotly_chart(fig_slowest_moving, use_container_width=True)

    with tab2:
        st.subheader("Inventory Inflow vs. Outflow Over Time")
        inflow = filtered_transactions[filtered_transactions['entry_type'].isin(['Production', 'Purchase'])].set_index('transaction_date').resample('D')['quantity_change'].sum()
        outflow = filtered_transactions[filtered_transactions['entry_type'].isin(['Sales', 'Breakage'])].set_index('transaction_date').resample('D')['quantity_change'].sum()

        fig_flow = go.Figure()
        fig_flow.add_trace(go.Bar(x=inflow.index, y=inflow, name='Inflow', marker_color='green'))
        fig_flow.add_trace(go.Bar(x=outflow.index, y=outflow, name='Outflow', marker_color='red'))
        fig_flow.update_layout(barmode='group', title='Daily Inventory Flow', xaxis_title='Date', yaxis_title='Quantity')
        st.plotly_chart(fig_flow, use_container_width=True)
        
    with tab3:
        st.subheader("Current Stock Distribution")
        fig_dist = px.pie(
            filtered_stock,
            values='current_quantity',
            names='product_name',
            title="Stock Distribution by Product"
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    # --- Low Stock Alerts ---
    st.write("---")
    st.markdown("### ⚠️ Low Stock Alerts")

    # --- CHANGE 2: Use the 'key' to link the slider to session_state ---
    st.slider(
        "Low Stock Threshold", 
        min_value=0, 
        max_value=100, 
        key='low_stock_threshold'
    )
    
    # The filter now reads the value from st.session_state
    low_stock_items = filtered_stock[filtered_stock['current_quantity'] <= st.session_state.low_stock_threshold]
    
    if not low_stock_items.empty:
        st.warning(f"⚠️ {len(low_stock_items)} items are running low on stock!")
        st.dataframe(low_stock_items[['product_name', 'color', 'current_quantity']], use_container_width=True)
    else:
        st.success("✅ All items have sufficient stock levels!")

