from supabase import create_client, Client
import streamlit as st

# Your Supabase project details
SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = "YOUR_ANON_PUBLIC_KEY"

# Create client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Example: Sign up a user
def signup_user(email, password):
    response = supabase.auth.sign_up({"email": email, "password": password})
    return response

# Example: Log in a user
def login_user(email, password):
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    return response

# Example: Insert expense
def add_expense(user_id, category, amount):
    data = {"user_id": user_id, "category": category, "amount": amount}
    response = supabase.table("expenses").insert(data).execute()
    return response
