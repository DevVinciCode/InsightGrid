"""
Generates a realistic demo e-commerce SQLite database: customers, products,
orders. Run directly: `python seed.py` (creates demo.db next to this file).

Designed to demonstrate: trends, rankings, comparisons, anomalies, filtering,
joins, customer analysis, product analysis.
"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "demo.db"

CITIES = [
    ("Delhi", "Delhi"), ("Mumbai", "Maharashtra"), ("Bengaluru", "Karnataka"),
    ("Chennai", "Tamil Nadu"), ("Pune", "Maharashtra"), ("Hyderabad", "Telangana"),
    ("Kolkata", "West Bengal"), ("Jaipur", "Rajasthan"),
]
SEGMENTS = ["Consumer", "Small Business", "Enterprise"]

CATEGORIES = {
    "Electronics": [("Wireless Earbuds", 1999), ("Smartphone", 24999), ("Laptop", 54999),
                    ("Smartwatch", 4999), ("Bluetooth Speaker", 2499)],
    "Home & Kitchen": [("Air Fryer", 5999), ("Mixer Grinder", 2999), ("Non-stick Pan", 899),
                       ("Vacuum Cleaner", 8999), ("Water Purifier", 12999)],
    "Fashion": [("Running Shoes", 2999), ("Denim Jacket", 1999), ("Backpack", 1499),
                ("Sunglasses", 999), ("Wrist Watch", 3499)],
    "Books": [("Fiction Novel", 399), ("Self-Help Book", 349), ("Textbook", 899),
              ("Comic Collection", 599)],
    "Sports": [("Yoga Mat", 799), ("Dumbbell Set", 2999), ("Cricket Bat", 1899),
               ("Cycling Helmet", 1299)],
}

random.seed(42)


def build():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        segment TEXT NOT NULL,
        signup_date TEXT NOT NULL
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL
    );

    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        order_date TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        revenue REAL NOT NULL,
        profit REAL NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('completed','cancelled','returned'))
    );

    CREATE INDEX idx_orders_customer ON orders(customer_id);
    CREATE INDEX idx_orders_product ON orders(product_id);
    CREATE INDEX idx_orders_date ON orders(order_date);
    """)

    # customers
    customers = []
    for i in range(1, 201):
        city, state = random.choice(CITIES)
        signup = date(2023, 1, 1) + timedelta(days=random.randint(0, 900))
        customers.append((i, f"Customer {i}", city, state, random.choice(SEGMENTS), signup.isoformat()))
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)", customers)

    # products
    products = []
    pid = 1
    product_lookup = {}
    for cat, items in CATEGORIES.items():
        for name, price in items:
            products.append((pid, name, cat, price))
            product_lookup[pid] = (price, cat)
            pid += 1
    cur.executemany("INSERT INTO products VALUES (?,?,?,?)", products)

    # orders: 2 years of data (2024-2025), with a deliberate March dip and a
    # Nov/Dec spike so "why did revenue fall in March" / seasonality questions
    # have a real, discoverable answer.
    orders = []
    order_id = 1
    start = date(2024, 1, 1)
    end = date(2025, 12, 31)
    day = start
    while day <= end:
        base_orders_today = 8
        if day.month == 3:
            base_orders_today = int(base_orders_today * 0.5)      # March dip
        if day.month in (11, 12):
            base_orders_today = int(base_orders_today * 1.6)      # Nov/Dec spike
        n_orders = max(1, int(random.gauss(base_orders_today, 2)))

        for _ in range(n_orders):
            cust_id = random.randint(1, 200)
            pid = random.randint(1, len(products))
            price, cat = product_lookup[pid]
            qty = random.randint(1, 3)
            revenue = round(price * qty, 2)
            margin = random.uniform(0.1, 0.35)
            profit = round(revenue * margin, 2)
            status = random.choices(
                ["completed", "cancelled", "returned"], weights=[0.88, 0.07, 0.05]
            )[0]
            orders.append((order_id, cust_id, pid, day.isoformat(), qty, revenue, profit, status))
            order_id += 1
        day += timedelta(days=1)

    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with {len(customers)} customers, {len(products)} products, {len(orders)} orders.")


if __name__ == "__main__":
    build()
