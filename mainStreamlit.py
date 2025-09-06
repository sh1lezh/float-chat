import streamlit as st
from backend_ollama import generate_sql_query, execute_sql_query

# --- Page Configuration ---
st.set_page_config(
    page_title="FloatChat 🌊",
    page_icon="🌊",
    layout="centered"
)

st.title("FloatChat 🌊")
st.caption("An AI-Powered Conversational Interface for ARGO Ocean Data")

# --- Chat Interface ---
user_question = st.text_input("Ask a question about the ARGO float data:", placeholder="e.g., Show the 5 deepest measurements")

if st.button("Get Answer", type="primary"):
    if user_question:
        with st.spinner("🤖 Thinking..."):
            try:
                # 1. Generate SQL query
                st.info("Generating SQL query...")
                sql_query = generate_sql_query(user_question)

                with st.expander("Generated SQL Query"):
                    st.code(sql_query, language="sql")

                # 2. Execute SQL query
                st.info("Executing query...")
                result_df = execute_sql_query(sql_query)

                # 3. Display results
                st.success("Here are the results:")
                st.dataframe(result_df)

            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a question.")