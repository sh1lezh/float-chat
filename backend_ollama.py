import pandas as pd
import sqlalchemy
import ollama
import re

# --- Configuration ---
DB_PATH = "sqlite:///argo.db"
MODEL_NAME = 'phi3:3.8b-mini-4k-instruct-q4_K_M'
SCHEMA = """
Table: profiles
Columns:
- float_id (text): Float identifier
- PRES (float): Pressure/depth in dbar
- TEMP (float): Temperature in Celsius
- PSAL (float): Salinity in PSU
- LATITUDE (float): Latitude in degrees
- LONGITUDE (float): Longitude in degrees
- TIME (datetime): Measurement time
- profile_id (integer): Profile index
"""

def generate_sql_query(user_question: str) -> str:
    """
    Generates an SQL query from a user's question using the local LLM.
    """
    prompt = f"""
    You are an expert SQLite data analyst. Based on the database schema below, write a single, valid SQLite query to answer the user's question.
    
    **Schema:**
    ```
    {SCHEMA}
    ```

    **User Question:**
    "{user_question}"

    Return **only** the SQL query and nothing else. Do not use markdown formatting.
    """
    
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{'role': 'user', 'content': prompt}],
        options={'temperature': 0.0}
    )
    
    generated_sql = response['message']['content'].strip()
    return re.sub(r"```sql\n|```", "", generated_sql).strip()

def execute_sql_query(query: str) -> pd.DataFrame:
    """
    Executes an SQL query and returns the result as a pandas DataFrame.
    """
    engine = sqlalchemy.create_engine(DB_PATH)
    result_df = pd.read_sql(query, engine)
    return result_df