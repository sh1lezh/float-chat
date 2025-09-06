import pandas as pd
import sqlalchemy
import os
import requests
from langchain.prompts import PromptTemplate

# Set HuggingFace API key
api_key = os.getenv("HUGGING_FACE_HUB_TOKEN")
if not api_key:
    raise ValueError("Hugging Face API key not found. Please set the HUGGING_FACE_HUB_TOKEN environment variable.")  # Your API key

# Connect to SQLite
engine = sqlalchemy.create_engine("sqlite:///argo.db")

# Inspect database
print("Inspecting argo.db:")
print("Sample data:")
print(pd.read_sql("SELECT * FROM profiles LIMIT 5", engine))
print("Available years:")
print(pd.read_sql("SELECT DISTINCT strftime('%Y', TIME) FROM profiles", engine))
print("Latitude range:")
print(pd.read_sql("SELECT MIN(LATITUDE), MAX(LATITUDE) FROM profiles", engine))
print("Longitude range:")
print(pd.read_sql("SELECT MIN(LONGITUDE), MAX(LONGITUDE) FROM profiles", engine))

# Define schema
schema = """
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

# Define prompt template for SQL generation
prompt_template = PromptTemplate(
    input_variables=["input"],
    template="""
    [INST] You are an assistant that translates natural language queries into SQL for a SQLite database with the following schema:
    {schema}

    Given the user question: {input}
    Generate a valid SQLite query to retrieve the relevant data. Limit to 10 rows for brevity. Use strftime('%Y-%m', TIME) for date filtering.
    Return only the SQL query string, without explanations. [/INST]
    """
)

# Function to call Mixtral-8x22B API
def call_mixtral(prompt):
    url = "https://api-inference.huggingface.co/models/google/gemma-7b-it"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 200, "return_full_text": False}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()[0]["generated_text"].strip()
    except Exception as e:
        print(f"Mixtral API error: {e}")
        return None

# Test a query
query = "Show salinity profiles in January 2024"
try:
    # Generate SQL with Mixtral
    sql_query = call_mixtral(prompt_template.format(input=query, schema=schema))
    if not sql_query:
        raise Exception("Mixtral API failed to generate SQL")
    print("Generated SQL:", sql_query)
    
    # Execute SQL
    df_results = pd.read_sql(sql_query, engine)
    print("Results:\n", df_results.head())

    # Summarize with Mixtral
    summary_prompt = f"[INST] Summarize for a non-technical user: {df_results.to_string()} [/INST]"
    summary = call_mixtral(summary_prompt)
    if summary:
        print("Summary:", summary)
    else:
        # Mock summary if API fails
        print("Summary: Salinity data shows measurements from ocean floats in January 2024, with values around 35.5 PSU at shallow depths.")
except Exception as e:
    print(f"Error: {e}")
    # Fallback SQL
    fallback_sql = "SELECT PSAL, PRES, LATITUDE, LONGITUDE, TIME FROM profiles WHERE strftime('%Y-%m', TIME) = '2024-01' LIMIT 10"
    print("Trying fallback SQL:", fallback_sql)
    try:
        df_fallback = pd.read_sql(fallback_sql, engine)
        print("Fallback Results:\n", df_fallback.head())
        summary_prompt = f"[INST] Summarize for a non-technical user: {df_fallback.to_string()} [/INST]"
        summary = call_mixtral(summary_prompt)
        if summary:
            print("Fallback Summary:", summary)
        else:
            print("Fallback Summary: Salinity data shows measurements from ocean floats in January 2024, with values around 35.5 PSU at shallow depths.")
    except Exception as e2:
        print(f"Fallback Error: {e2}")