import os

import streamlit as st

# ক্লাউডে shop.db গিটে থাকে না, তাই না থাকলে নিজেই বানাও
if not os.path.exists("shop.db") or not os.path.exists("schema.txt"):
    import setup_db

    setup_db.build_db()
    with open("schema.txt", "w", encoding="utf-8") as f:
        f.write(setup_db.build_schema_text())

from analyst import analyze

st.set_page_config(page_title="AI Data Analyst", page_icon="📊")
st.title("📊 AI Data Analyst")
st.caption("Ask questions about a shop database in plain English. Read-only: SELECT queries only.")

MAX_Q = 10
if "count" not in st.session_state:
    st.session_state.count = 0

with st.expander("Database schema"):
    with open("schema.txt", encoding="utf-8") as f:
        st.code(f.read(), language="sql")

examples = [
    "How many customers are there in each city?",
    "Total revenue by product category",
    "Top 3 best selling products by quantity",
    "Delete all orders",
]
choice = st.selectbox("Try an example", [""] + examples)
question = st.text_input("Your question", value=choice)

if st.button("Ask") and question.strip():
    if st.session_state.count >= MAX_Q:
        st.warning(f"Demo limit reached ({MAX_Q} questions per session).")
    else:
        st.session_state.count += 1
        with st.spinner("Thinking..."):
            res = analyze(question)

        if res["status"] == "ok":
            st.success(res["answer"])
            st.code(res["sql"], language="sql")
            st.dataframe([dict(zip(res["columns"], r)) for r in res["rows"]])
            if res.get("chart"):
                st.image(res["chart"])
        elif res["status"] in ("refused", "blocked"):
            st.error(f"Blocked: {res['reason']}")
            if res.get("sql"):
                st.code(res["sql"], language="sql")
        else:
            st.error(f"Failed: {res['reason']}")