# app.py
# Expense Tracker with Streamlit + SQLite
# ---------------------------------------
# Features:
#  - Add expenses
#  - View + filter + charts
#  - Monthly budgets
#  - Import/Export CSV
# ---------------------------------------

import streamlit as st
import sqlite3
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import altair as alt

# Database file
DB_PATH = Path(__file__).with_name("expenses.db")

# ---------------- Database Setup ----------------

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category_id INTEGER,
                notes TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );
            """
        )
        # Default categories
        for cat in ["Food", "Transport", "Bills", "Shopping", "Other"]:
            conn.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (cat,))
        conn.commit()

def get_categories():
    with get_conn() as conn:
        rows = conn.execute("SELECT name FROM categories ORDER BY name").fetchall()
    return [r[0] for r in rows]

def add_expense(d, amount, category, notes=""):
    with get_conn() as conn:
        cat_id = conn.execute("SELECT id FROM categories WHERE name=?", (category,)).fetchone()[0]
        conn.execute(
            "INSERT INTO expenses(date, amount, category_id, notes) VALUES (?,?,?,?)",
            (d.isoformat(), float(amount), cat_id, notes),
        )
        conn.commit()

def get_expenses(start=None, end=None, categories=None):
    q = """
        SELECT e.id, e.date, e.amount, c.name as category, e.notes
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE 1=1
    """
    params = []
    if start:
        q += " AND date(e.date) >= date(?)"
        params.append(start.isoformat())
    if end:
        q += " AND date(e.date) <= date(?)"
        params.append(end.isoformat())
    if categories:
        q += f" AND c.name IN ({','.join(['?']*len(categories))})"
        params.extend(categories)

    q += " ORDER BY date(e.date) DESC"
    with get_conn() as conn:
        df = pd.read_sql_query(q, conn, params=params)
    df["Date"] = pd.to_datetime(df["date"]).dt.date
    df.rename(columns={"amount":"Amount", "category":"Category", "notes":"Notes"}, inplace=True)
    return df[["Date","Amount","Category","Notes"]]

# ---------------- UI ----------------

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")
init_db()

st.title("💸 Expense Tracker")

tabs = st.tabs(["➕ Add Expense", "📊 View & Analyze"])

# --- Add Expense Tab ---
with tabs[0]:
    st.subheader("Add a new expense")
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        d = col1.date_input("Date", value=date.today())
        amount = col2.number_input("Amount (₹)", min_value=0.0, step=10.0)
        category = col3.selectbox("Category", get_categories())
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            if amount > 0:
                add_expense(d, amount, category, notes)
                st.success("Expense added!")
            else:
                st.error("Amount must be greater than 0.")

# --- View & Analyze Tab ---
with tabs[1]:
    st.subheader("Your Expenses")

    today = date.today()
    month_start = date(today.year, today.month, 1)

    col1, col2, col3 = st.columns([2,2,3])
    start_d = col1.date_input("From", value=month_start)
    end_d = col2.date_input("To", value=today)
    cats = col3.multiselect("Categories", options=get_categories())

    df = get_expenses(start_d, end_d, cats)

    if df.empty:
        st.info("No expenses found.")
    else:
        st.dataframe(df, use_container_width=True)

        total = df["Amount"].sum()
        st.metric("Total Spent", f"₹{total:,.2f}")

        # Chart: Spend by category
        by_cat = df.groupby("Category")["Amount"].sum().reset_index()
        chart = alt.Chart(by_cat).mark_bar().encode(
            x="Category", y="Amount", tooltip=["Category","Amount"]
        )
        st.altair_chart(chart, use_container_width=True)

        # Export
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", data=csv, file_name="expenses.csv", mime="text/csv")
