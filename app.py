import streamlit as st
import psycopg2
import os

# Connect to Supabase Postgres
def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        port=os.environ["DB_PORT"]
    )

conn = get_connection()
cursor = conn.cursor()

