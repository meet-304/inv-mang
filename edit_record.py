import streamlit as st
from datetime import datetime
from bq_database import insert_transaction_record, update_product_stock, get_all_product_stock
import uuid

def show_edit_record():
    st.markdown("### 📝 Add a Correction Transaction")
    st.info("To maintain an accurate history, you should add a 'Correction' transaction instead of editing or deleting past records.")

    # Fetch all unique products and their attributes to populate the dropdowns
    stock_df = get_all_product_stock()

    if stock_df.empty:
        st.warning("No products in stock. Please add a transaction first.")
        return

    # Create unique lists for the dropdowns
    product_list = [""] + sorted(stock_df['product_name'].unique().tolist())
    
    with st.form("correction_form"):
        entered_by = st.text_input("Name of Person Entering Record*", value=st.session_state.get('user'), key="entered_by", help="Who is adding this record?")

        st.subheader("Correction Details")
        

        selected_product = st.selectbox("Select Product Name*", options=product_list)   
        product_specific_df = stock_df[stock_df['product_name'] == selected_product]
        color_list = [""] + sorted(product_specific_df['color'].unique().tolist())
        packing_list = [""] + sorted(product_specific_df['packing_option'].unique().tolist())
        grade_list = [""] + sorted(product_specific_df['product_grade'].unique().tolist())
        selected_color = st.selectbox("Select Color*", options=color_list)
        selected_packing = st.selectbox("Select Packing Option*", options=packing_list)
        selected_grade = st.selectbox("Select Product Grade*", options=grade_list)
            
        st.write("---")
            
        correction_type = st.radio("Correction Type", ["Add Stock", "Subtract Stock"])
        quantity = st.number_input("Quantity to Adjust", min_value=1, step=1)

        submitted = st.form_submit_button("Add Correction Transaction")
        
        if submitted:
            # Check if all selections have been made
            if not all([entered_by, selected_product, selected_color, selected_packing, selected_grade]):
                st.error("Please fill in all details to identify the item.")
            else:
                if correction_type == "Add Stock":
                    quantity_adjustment = quantity
                    entry_type = "Correction - Add"
                else:
                    quantity_adjustment = -quantity
                    entry_type = "Correction - Subtract"
                
                transaction_record = {
                    'transaction_id': str(uuid.uuid4()),
                    'transaction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'product_name': selected_product,
                    'color': selected_color,
                    'packing_option': selected_packing,
                    'product_grade': selected_grade,
                    'entry_type': entry_type,
                    'quantity_change': quantity,
                    'user_name': entered_by
                }
                
                try:
                    stock_errors = update_product_stock(selected_product, selected_color, selected_packing, selected_grade, quantity_adjustment)
                    if stock_errors:
                        raise Exception(stock_errors)
                    
                    transaction_errors = insert_transaction_record(transaction_record)
                    if transaction_errors:
                        raise Exception(f"Failed to log transaction: {transaction_errors}")
                        
                    st.success("✅ Correction transaction successfully added!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")