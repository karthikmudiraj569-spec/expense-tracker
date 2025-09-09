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
import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# ---------------------------
# Database setup
# ---------------------------
conn = sqlite3.connect("expense.db", check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
def create_tables():
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    amount REAL,
                    date TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()

create_tables()

# ---------------------------
# Helper functions
# ---------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    return c.fetchone()

def add_expense(user_id, category, amount):
    c.execute("INSERT INTO expenses (user_id, category, amount, date) VALUES (?,?,?,DATE('now'))",
              (user_id, category, amount))
    conn.commit()

def get_expenses(user_id):
    c.execute("SELECT category, amount, date FROM expenses WHERE user_id=? ORDER BY date DESC",
              (user_id,))
    return c.fetchall()

# ---------------------------
# Streamlit App
# ---------------------------
st.title("💰 Expense Tracker with Login")

# Sidebar menu
menu = ["Login", "SignUp"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------------------
# Sign Up
# ---------------------------
if choice == "SignUp":
    st.subheader("Create a New Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        if add_user(username, password):
            st.success("Account created! ✅ Please go to Login.")
        else:
            st.error("⚠ Username already exists. Try another one.")

# ---------------------------
# Login
# ---------------------------
elif choice == "Login":
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state["user_id"] = user[0]
            st.session_state["username"] = user[1]
            st.success(f"Welcome, {st.session_state['username']}! 🎉")
        else:
            st.error("Invalid username or password")

# ---------------------------
# Expense Tracker (only if logged in)
# ---------------------------
if "user_id" in st.session_state:
    st.header("📊 Your Expense Dashboard")

    # Add expense
    with st.form("expense_form"):
        category = st.text_input("Category")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        submit = st.form_submit_button("Add Expense")
        if submit and category and amount > 0:
            add_expense(st.session_state["user_id"], category, amount)
            st.success("✅ Expense added!")

    # Show expenses
    expenses = get_expenses(st.session_state["user_id"])
    if expenses:
        df = pd.DataFrame(expenses, columns=["Category", "Amount", "Date"])
        st.subheader("📋 Your Expenses")
        st.dataframe(df)

        # Summary
        st.subheader("📈 Expense Summary")
        st.bar_chart(df.groupby("Category")["Amount"].sum())
    else:
        st.info("No expenses added yet.")

    # Logout button
    if st.button("Logout"):
        st.session_state.clear()
        st.success("You have logged out.")
