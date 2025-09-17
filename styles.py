# In styles.py

import streamlit as st

def custom_css():
    st.markdown("""
        <style>
            /* --- Import a clean, modern font --- */
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

            /* --- LIGHT THEME (DEFAULT) VARIABLES --- */
            :root {
                --primary-color: #4A90E2;
                --background-color: #F0F2F6;
                --card-background-color: #FFFFFF;
                --text-color: #333333;
                --widget-background-color: #FFFFFF;
                --widget-text-color: #212529; /* A slightly softer black for better readability */
                --border-radius: 12px;
                --box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }

            /* --- DARK THEME VARIABLES --- */
            body[data-theme="dark"] {
                --primary-color: #50E3C2;
                --background-color: #0E1117; /* Streamlit's default dark */
                --card-background-color: #262730;
                --text-color: #FAFAFA;
                --widget-background-color: #262730; /* Dark background for widgets */
                --widget-text-color: #FAFAFA; /* White text for dark mode */
            }

            /* --- General Body Styles --- */
            body {
                font-family: 'Poppins', sans-serif;
                background-color: var(--background-color);
                color: var(--text-color);
            }

            /* --- UPDATED WIDGET STYLING (THE FIX) --- */
            
            /* This targets all text-based input fields specifically */
            .stTextInput input, .stDateInput input, .stNumberInput input, .stTextArea textarea {
                background-color: var(--widget-background-color);
                color: var(--widget-text-color) !important; /* Use !important to ensure override */
                border-radius: var(--border-radius);
                border: 1px solid transparent;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                transition: all 0.2s ease;
            }

            /* This targets the body of selectbox widgets */
            .stSelectbox > div {
                background-color: var(--widget-background-color);
                border-radius: var(--border-radius);
                border: 1px solid transparent;
            }

            /* Styling for widget labels */
            .stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label, .stTextArea label {
                color: var(--text-color) !important;
            }

            /* Focus effect for all widgets */
            .stTextInput input:focus, .stSelectbox div:focus-within, .stDateInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.25);
            }

            /* --- Other styles --- */
            .stButton > button {
                width: 100%;
                border-radius: var(--border-radius);
                border: none;
                padding: 0.75rem 1rem;
                font-weight: 600;
                color: #FFFFFF;
                background-color: var(--primary-color);
            }
        </style>
    """, unsafe_allow_html=True)