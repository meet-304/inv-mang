import streamlit as st
import pandas as pd
from datetime import date, datetime
import uuid
from bq_database import (
    get_all_product_stock,
    update_product_stock,
    insert_transaction_record,
    bulk_update_product_stock,
    bulk_insert_transaction_records
)

# --- STATIC LISTS FOR DROPDOWNS ---
ITEM_NAMES = [
    "",'12"x9"W.B', '14"x11"W.B', "14''X14'' W.B", '14X14 MOON CORNER', '16"x16"W.B', '16X9 HAZEL',
    '18"X12" COLOR MIX', '18"X12" SQUARE', '18"x12"W.B', '18"X13" W.B', '18"X14" W.B.', "18''I.W.C.",
    "18''X13'' RANI W.B", "18''X13'' W.B SQUARE", "18''X14'' POLO SET", "18''X14'' RIYO WASH BASIN",
    '18X12 VITROSA', '18X14 MINI POLO', '18X14 SETU', '18X14 SWIFT', '18X14 VITROSA SET',
    '20 OP SPECIAL COLOUR MIX', '20" OP.', '20"x16"W.B', "20''X16'' POLO W.B", "20''X17'' POLO SET",
    '21 OP', '22"X16" REPOSE SET', '22"x16"W.B', '23" OP.', "23'' I.W.C.", 'ANGLO P', 'ANGLO S',
    'AQUA SET', 'BABY PAN', 'BIG STERLING  SET', 'BOX', 'C T PAN', 'CHENNEL', 'CISTERN LLC',
    'CORNER URINAL', 'COUNTER BASIN', 'CROWNY WASH BASIN', 'DELTA SET', 'DELTA WASH', 'DOLPHIN SET',
    'E.W.C - S', "E.W.C S' CONCEALED ROUND REGULAR", 'E.W.C.- P', 'ESTERN', 'EWC SQUARE CONSEALED', "Flour Mount",
    'FLORA PED', 'FLUSH TANK', 'FOOT REST', 'GENTS URINAL', 'HALF STALL', 'ITALIAN SET', 'JET SPRAY',
    'kacha big ptrap', 'kacha gents urinal', 'kacha ladies urinal', 'KACHA MAL PURCHASE',
    'kacha pedestal', 'KACHA STARGOLD PEDESTAL', 'L.L.C TANK', 'LADIES URINAL', 'LEO SET', 'M D PAN',
    'MINI STALL URINAL', 'NANO URINAL', 'ONE PIECE', 'ONE PIECE BASIN', 'ONE PIECE PTRAP',
    'ONE PIECE ROUND', 'ONE PIECE ROUND PTRAP', 'ONE PIECE SQUARE', 'ONE PIECE SQUARE PTRAP',
    'ONE PIECE STRAP', 'P TRAP S', 'PARTITION PLATE', 'PEDESTAL', 'PEDESTAL POLO', 'PEDESTAL S',
    'POLO PLAIN SET', 'POLO VITROSA', 'PRINCE WB', 'PTRAP BIG', 'PTRAP SMALL', 'RULARPAN',
    'RULARPAN SET WITH FOOTREST', 'RULARPAN WITH PTRAP', 'SEAT COVER', 'SEMI SET WASH',
    'SINK 18x12x6', 'SINK 24x18x10', 'SOAP DISH', 'SOPHIA SET', 'SQUATTING', 'STAR GOLD WASH',
    'STARGOLD PEDESTAL', 'STARGOLD SET', 'STRAPING PATI', 'SUPREME SET', 'TABLE TOP', 'VITROSA SET',
    'WALL FLUSH TANK', 'WALL HUNG', 'WALL URINAL', '21 AQUA PAN'
]

COLORS = ["", "Ivory", "Blue", "Green", "Brown", "Black", "White", "Pink", "Cofee Brown", "Aqua Green", "Blue Green", "Alpine blue", "Magenta", "Walker Yellow", "Red Brown", "Mint Green", "Black Rustick", "Magenta Rustick", "Red Brown Rustick", "Double Colour", "Mat Gray", "Cofee Brown Rustick", "Wooden"]
PACKING_OPTIONS = ["Box", "Paper", "Grass", "Open", "--- Enter Other ---"]
PRODUCT_GRADES = ["Common", "Premium", "Reject", "SUTY", "Bhangar", "--- Enter Other ---"]
TRANSACTION_TYPES = ["", "Production", "Purchase", "Sales", "Breakage"]

# Helper function to create a combobox-like widget
def combobox(label, options, key, help_text=""):
    other_option = "--- Enter Other ---"
    
    # Add "Other" option if not already present
    options_with_other = options if other_option in options else options + [other_option]
    
    selection = st.selectbox(label, options=options_with_other, key=f"{key}_select", help=help_text)
    
    if selection == other_option:
        return st.text_input(f"Enter Custom {label}", key=f"{key}_text")
    return selection

def show_add_record():
    st.markdown("### ➕ Add New Inventory Transaction")
    entry_mode = st.radio("Select Entry Mode", ["Single Transaction", "Bulk Transactions"], horizontal=True)
    if entry_mode == "Single Transaction":
        render_single_transaction_form()
    else:
        render_bulk_transaction_form()

def render_single_transaction_form():
    st.subheader("Single Transaction Entry")
    restriction = st.session_state.get('allowed_transaction')
    
    allowed_options = TRANSACTION_TYPES
    if restriction and restriction != 'all': allowed_options = restriction.split(',')
    
    is_locked = len(allowed_options) == 1
    if is_locked:
        st.info(f"Entry Mode: You are authorized to add **{allowed_options[0]}** records only.")
        transaction_type = allowed_options[0]
    else:
        # --- MOVED OUTSIDE FORM ---
        transaction_type = st.selectbox("Transaction Type*", options=allowed_options)

    with st.form("add_single_record_form", clear_on_submit=True):
        entered_by = st.text_input("Name of Person Entering Record*", value=st.session_state.get('user', ''))
        col1, col2 = st.columns(2)
        
        with col1:
            record_date = st.date_input("Date", value=date.today(), max_value=date.today())
            product_name = combobox("Product Name*", ITEM_NAMES, "single_product")
            color = combobox("Color", COLORS, "single_color")
            packing_option = combobox("Packing Option", PACKING_OPTIONS, "single_packing")
            product_grade = combobox("Product Grade", PRODUCT_GRADES, "single_grade")
        
        with col2:
            quantity = st.number_input("Quantity*", min_value=1, value=1, step=1)
            invoice_number = ""
            # --- THIS NOW WORKS CORRECTLY ---
            if transaction_type in ["Sales", "Purchase"]:
                invoice_number = st.text_input("Invoice Number (6 chars)", max_chars=6)
        
        remarks = st.text_area("Remarks")

        submitted = st.form_submit_button("Add Record")
        if submitted:
            if not all([product_name, transaction_type, entered_by]):
                st.error("Please fill in all required fields.")
                return
            
            adjustment = -quantity if transaction_type in ["Sales", "Breakage"] else quantity
            record = {
                'transaction_id': str(uuid.uuid4()), 'transaction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'product_name': product_name, 'color': color, 'packing_option': packing_option,
                'product_grade': product_grade, 'entry_type': transaction_type, 'quantity_change': quantity,
                'user_name': entered_by, 'invoice_number': invoice_number, 'remarks': remarks
            }
            try:
                stock_errors = update_product_stock(product_name, color, packing_option, product_grade, adjustment)
                if stock_errors: raise Exception(stock_errors)
                transaction_errors = insert_transaction_record(record)
                if transaction_errors: raise Exception(f"Stock updated, but log failed: {transaction_errors}")
                st.success("✅ Record added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")

def render_bulk_transaction_form():
    st.subheader("Bulk Transactions Entry")
    restriction = st.session_state.get('allowed_transaction')
    
    allowed_options = TRANSACTION_TYPES
    if restriction and restriction != 'all': allowed_options = restriction.split(',')
            
    is_locked = len(allowed_options) == 1
    if is_locked:
        st.info(f"Entry Mode: You are authorized to add **{allowed_options[0]}** records only.")
        entry_type = allowed_options[0]
    else:
        # --- MOVED OUTSIDE FORM ---
        entry_type = st.selectbox("Transaction Type* (Applies to all)", options=allowed_options)

    with st.form("bulk_add_form_dynamic_rows", clear_on_submit=True):
        # --- THIS NOW WORKS CORRECTLY ---
        if entry_type in ["Sales", "Purchase"]:
            invoice_number = st.text_input("Invoice Number (6 chars, applies to all)", max_chars=6)
        else:
            invoice_number = ""

        entered_by = st.text_input("Name of Person Entering Record*", value=st.session_state.get('user', ''))
        remarks = st.text_area("Remarks (applies to all records in this batch)")
        st.write("---")
        
        if 'bulk_rows' not in st.session_state: st.session_state.bulk_rows = 1
        def add_row(): st.session_state.bulk_rows += 1
        def remove_row():
            if st.session_state.bulk_rows > 1: st.session_state.bulk_rows -= 1

        for i in range(st.session_state.bulk_rows):
            st.markdown(f"**Product Row {i + 1}**")
            cols = st.columns(5)
            other_option = "--- Enter Other ---"
            
            # This logic creates the combobox functionality for each row
            product_selection = cols[0].selectbox("Product Name", options=ITEM_NAMES + [other_option], key=f"product_{i}")
            if product_selection == other_option: cols[0].text_input("Enter Custom Product", key=f"product_other_{i}")
            
            color_selection = cols[1].selectbox("Color", options=COLORS + [other_option], key=f"color_{i}")
            if color_selection == other_option: cols[1].text_input("Enter Custom Color", key=f"color_other_{i}")
            
            packing_selection = cols[2].selectbox("Packing Option", options=PACKING_OPTIONS, key=f"packing_{i}")
            if packing_selection == other_option: cols[2].text_input("Enter Custom Packing", key=f"packing_other_{i}")
            
            grade_selection = cols[3].selectbox("Product Grade", options=PRODUCT_GRADES, key=f"grade_{i}")
            if grade_selection == other_option: cols[3].text_input("Enter Custom Grade", key=f"grade_other_{i}")

            cols[4].number_input("Quantity", min_value=1, value=1, key=f"quantity_{i}")
            st.markdown("<hr style='margin-top:0.5rem; margin-bottom:1rem;'>", unsafe_allow_html=True)
        
        b_col1, b_col2, _ = st.columns([2,3,5])
        b_col1.form_submit_button("➕ Add Row", on_click=add_row)
        b_col2.form_submit_button("➖ Remove Last Row", on_click=remove_row)
        st.write("---")
        submitted = st.form_submit_button("Submit All Records")

        if submitted:
            if not entry_type or not entered_by:
                st.error("Please select a transaction type and enter your name.")
                return

            records_to_create, stock_updates = [], []
            adj_multiplier = -1 if entry_type in ["Sales", "Breakage"] else 1
            
            for i in range(st.session_state.bulk_rows):
                def get_value(base_key):
                    selection = st.session_state.get(f"{base_key}_{i}", "")
                    if selection == other_option:
                        return st.session_state.get(f"{base_key}_other_{i}", "")
                    return selection

                product_name = get_value("product")
                if not product_name: continue
                
                color = get_value("color")
                packing = get_value("packing")
                grade = get_value("grade")
                quantity = st.session_state[f"quantity_{i}"]
                
                records_to_create.append({
                    'transaction_id': str(uuid.uuid4()), 'transaction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'product_name': product_name, 'color': color, 'packing_option': packing,
                    'product_grade': grade, 'entry_type': entry_type, 'quantity_change': quantity,
                    'user_name': entered_by, 'invoice_number': invoice_number, 'remarks': remarks
                })
                stock_updates.append({
                    'product_name': product_name, 'color': color, 'packing_option': packing,
                    'product_grade': grade, 'adjustment': quantity * adj_multiplier
                })

            if not records_to_create:
                st.warning("No valid records to submit.")
                return
            
            try:
                stock_errors = bulk_update_product_stock(stock_updates)
                if stock_errors: raise Exception(stock_errors)
                transaction_errors = bulk_insert_transaction_records(records_to_create)
                if transaction_errors: raise Exception(f"Stock updated, but log failed: {transaction_errors}")
                
                st.session_state.bulk_rows = 1
                st.success(f"✅ Successfully added {len(records_to_create)} records!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.write("### Preview of Records that Failed:")
                st.dataframe(pd.DataFrame(records_to_create))
                st.error(f"❌ An error occurred: {e}")