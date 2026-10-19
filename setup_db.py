import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path("shop.db")
SCHEMA_PATH = Path("schema.txt")
random.seed(42)

CITIES = ["Dhaka", "Chattogram", "Sylhet", "Rajshahi", "Khulna", "Barishal"]
FIRST = ["Rahim", "Karim", "Sumi", "Nadia", "Tanvir", "Mitu", "Arif", "Lima",
         "Sajib", "Rina", "Fahim", "Jui", "Hasan", "Moni", "Shuvo"]
LAST = ["Ahmed", "Hossain", "Khan", "Akter", "Islam", "Chowdhury", "Sarker"]
PRODUCTS = [
    ("Wireless Mouse", "Electronics", 850),
    ("Keyboard", "Electronics", 1500),
    ("USB Cable", "Electronics", 250),
    ("Headphones", "Electronics", 2200),
    ("Notebook", "Stationery", 120),
    ("Pen Pack", "Stationery", 80),
    ("Desk Lamp", "Home", 1100),
    ("Water Bottle", "Home", 450),
    ("Backpack", "Fashion", 1800),
    ("T-Shirt", "Fashion", 600),
]
STATUSES = ["delivered", "delivered", "delivered", "shipped", "pending", "cancelled"]

SCHEMA_SQL = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    city TEXT NOT NULL,
    signup_date TEXT NOT NULL
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL
);
"""

NOTES = {
    "customers": "Customer info. signup_date format YYYY-MM-DD.",
    "products": "Product list. price in BDT. category: Electronics, Stationery, Home, Fashion.",
    "orders": "Each order. order_date format YYYY-MM-DD. status: delivered, shipped, pending, cancelled.",
    "order_items": "Items inside an order. Line total = quantity * products.price.",
}


def build_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA_SQL)

    today = date(2026, 10, 1)
    customers = []
    for i in range(1, 51):
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        signup = today - timedelta(days=random.randint(60, 700))
        customers.append((i, name, f"user{i}@example.com",
                          random.choice(CITIES), signup.isoformat()))
    con.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)

    con.executemany(
        "INSERT INTO products (name, category, price) VALUES (?,?,?)", PRODUCTS)

    for oid in range(1, 201):
        odate = today - timedelta(days=random.randint(0, 365))
        con.execute("INSERT INTO orders VALUES (?,?,?,?)",
                    (oid, random.randint(1, 50), odate.isoformat(),
                     random.choice(STATUSES)))
        for pid in random.sample(range(1, len(PRODUCTS) + 1), random.randint(1, 3)):
            con.execute(
                "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?,?,?)",
                (oid, pid, random.randint(1, 4)))
    con.commit()
    con.close()


def build_schema_text():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    con.close()
    return "\n\n".join(
        f"-- {n}: {NOTES.get(n, '')}\n{s.strip()};" for n, s in rows) + "\n"


if __name__ == "__main__":
    build_db()
    SCHEMA_PATH.write_text(build_schema_text(), encoding="utf-8")
    con = sqlite3.connect(DB_PATH)
    print("তৈরি হয়েছে: shop.db ও schema.txt")
    for t in ["customers", "products", "orders", "order_items"]:
        print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    con.close()