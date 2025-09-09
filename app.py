import streamlit as st
import psycopg2
import os
from datetime import date
import hashlib

# ---------- DB CONNECTION ----------
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

# ---------- INIT DB ----------
def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id),
        category VARCHAR(50),
        amount NUMERIC,
        date DATE,
        description TEXT
    );
    """)
    conn.commit()

init_db()

# ---------- HELPER FUNCTIONS ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                       (username, hash_password(password)))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    if result and result[1] == hash_password(password):
        return result[0]  # return user_id
    return None

def add_expense(user_id, category, amount, exp_date, description):
    cursor.execute(
        "INSERT INTO expenses (user_id, category, amount, date, description) VALUES (%s, %s, %s, %s, %s)",
        (user_id, category, amount, exp_date, description)
    )
    conn.commit()

def get_expenses(user_id):
    cursor.execute("SELECT category, amount, date, description FROM expenses WHERE user_id = %s ORDER BY date DESC", (user_id,))
    return cursor.fetchall()

# ---------- STREAMLIT APP ----------
st.title("💰 Expense Tracker")

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

menu = ["Login", "Register"] if not st.session_state["user_id"] else ["Add Expense", "View Expenses", "Logout"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------- LOGIN ----------
if choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user_id = login_user(username, password)
        if user_id:
            st.session_state["user_id"] = user_id
            st.success(f"Welcome {username} 👋")
        else:
            st.error("Invalid username or password")

# ---------- REGISTER ----------
elif choice == "Register":
    st.subheader("Register")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    if st.button("Register"):
        if register_user(username, password):
            st.success("Account created successfully! Please login.")
        else:
            st.error("Username already exists. Try another.")

# ---------- ADD EXPENSE ----------
elif choice == "Add Expense":
    st.subheader("Add a New Expense")
    category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Other"])
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    exp_date = st.date_input("Date", value=date.today())
    description = st.text_area("Description")

    if st.button("Save Expense"):
        add_expense(st.session_state["user_id"], category, amount, exp_date, description)
        st.success("Expense added successfully ✅")

# ---------- VIEW EXPENSES ----------
elif choice == "View Expenses":
    st.subheader("Your Expenses")
    rows = get_expenses(st.session_state["user_id"])
    if rows:
        for row in rows:
            st.write(f"📌 {row[0]} - ₹{row[1]} on {row[2]} | {row[3]}")
    else:
        st.info("No expenses yet. Add some!")

# ---------- LOGOUT ----------
elif choice == "Logout":
    st.session_state["user_id"] = None
    st.success("You have been logged out.")
