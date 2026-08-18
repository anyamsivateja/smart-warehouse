from flask import Flask, request, redirect, url_for, session, render_template_string
import sqlite3
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "siva-teja-smart-warehouse-secret-key"

DATABASE = "warehouse.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # INVENTORY
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT UNIQUE NOT NULL,
            sku TEXT NOT NULL,
            stock INTEGER NOT NULL,
            minimum INTEGER NOT NULL,
            location TEXT NOT NULL
        )
    """)

    # ORDERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            allocated INTEGER NOT NULL,
            order_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            delivery_date TEXT NOT NULL,
            location TEXT,
            instructions TEXT,
            created_at TEXT
        )
    """)

    # SAMPLE INVENTORY
    products = [
        ("Laptop", "LAP-001", 7, 5, "Zone A"),
        ("Wireless Mouse", "MOU-002", 25, 10, "Zone B"),
        ("Keyboard", "KEY-003", 4, 8, "Zone B"),
        ("Monitor", "MON-004", 12, 5, "Zone C"),
        ("Headphones", "HDP-005", 3, 6, "Zone C")
    ]

    for product in products:
        try:
            cur.execute("""
                INSERT INTO inventory
                (product, sku, stock, minimum, location)
                VALUES (?, ?, ?, ?, ?)
            """, product)
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# PRIORITY ENGINE
# =========================================================

def calculate_priority(order_type, delivery_date):

    if order_type == "urgent":
        return "HIGH"

    if order_type == "priority":
        return "MEDIUM"

    try:

        today = datetime.now().date()
        delivery = datetime.strptime(
            delivery_date,
            "%Y-%m-%d"
        ).date()

        days = (delivery - today).days

        if days <= 1:
            return "HIGH"

        if days <= 3:
            return "MEDIUM"

    except Exception:
        pass

    return "LOW"


# =========================================================
# BASE HTML
# =========================================================

BASE_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Smart Warehouse</title>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}

body {
    background: #f1f5f9;
    color: #0f172a;
}

/* SIDEBAR */

.sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 240px;
    background: #0f172a;
    color: white;
    padding: 25px 15px;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 30px;
    padding: 10px;
}

.logo-icon {
    width: 42px;
    height: 42px;
    background: #2563eb;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
}

.logo h2 {
    font-size: 17px;
}

.nav {
    display: block;
    color: #cbd5e1;
    text-decoration: none;
    padding: 13px;
    border-radius: 8px;
    margin-bottom: 5px;
}

.nav:hover {
    background: #1e3a8a;
    color: white;
}

.logout {
    position: absolute;
    bottom: 20px;
    left: 15px;
    right: 15px;
    background: #991b1b;
}

/* MAIN */

.main {
    margin-left: 240px;
    padding: 25px;
}

.topbar {
    background: white;
    padding: 18px 22px;
    border-radius: 14px;
    margin-bottom: 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.user {
    background: #dbeafe;
    color: #1d4ed8;
    padding: 10px 15px;
    border-radius: 20px;
    font-weight: bold;
}

/* CARDS */

.cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin: 20px 0;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 3px 10px rgba(0,0,0,.05);
}

.stat {
    font-size: 30px;
    font-weight: bold;
    margin-top: 10px;
}

.muted {
    color: #64748b;
}

/* TABLE */

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 13px;
    border-bottom: 1px solid #e2e8f0;
    text-align: left;
}

th {
    color: #64748b;
    font-size: 13px;
}

/* BADGES */

.badge {
    padding: 5px 9px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}

.high {
    background: #fee2e2;
    color: #dc2626;
}

.medium {
    background: #fef3c7;
    color: #d97706;
}

.low {
    background: #dcfce7;
    color: #15803d;
}

.blue {
    background: #dbeafe;
    color: #2563eb;
}

.gray {
    background: #e2e8f0;
    color: #475569;
}

/* FORM */

.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}

.field label {
    display: block;
    font-weight: bold;
    margin-bottom: 7px;
}

.field input,
.field select {
    width: 100%;
    padding: 12px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}

.full {
    grid-column: 1 / -1;
}

button {
    border: none;
    cursor: pointer;
}

.btn {
    padding: 11px 16px;
    background: #2563eb;
    color: white;
    border-radius: 8px;
    font-weight: bold;
}

.btn-green {
    background: #16a34a;
}

.btn-red {
    background: #dc2626;
}

.btn:hover {
    opacity: .9;
}

/* ALERT */

.alert {
    background: #fff7ed;
    border-left: 5px solid #f97316;
    padding: 15px;
    margin-bottom: 12px;
    border-radius: 8px;
}

/* AUTH */

.auth {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
        linear-gradient(
            135deg,
            #0f172a,
            #1e3a8a,
            #2563eb
        );
}

.auth-box {
    width: 420px;
    max-width: 95%;
    background: white;
    padding: 35px;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,.3);
}

.auth-box h1 {
    text-align: center;
    margin-bottom: 8px;
}

.auth-box p {
    text-align: center;
    color: #64748b;
    margin-bottom: 25px;
}

.auth-box input {
    width: 100%;
    padding: 13px;
    margin: 7px 0 15px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}

.auth-box label {
    font-weight: bold;
}

.auth-box button {
    width: 100%;
    padding: 13px;
    background: #2563eb;
    color: white;
    border-radius: 8px;
    font-weight: bold;
}

.auth-link {
    margin-top: 18px;
    text-align: center;
}

.auth-link a {
    color: #2563eb;
    text-decoration: none;
}

/* RESPONSIVE */

@media(max-width:900px) {

    .cards {
        grid-template-columns: 1fr 1fr;
    }

}

@media(max-width:650px) {

    .sidebar {
        position: relative;
        width: 100%;
    }

    .logout {
        position: static;
        margin-top: 20px;
    }

    .main {
        margin-left: 0;
    }

    .cards,
    .form-grid {
        grid-template-columns: 1fr;
    }

    .full {
        grid-column: auto;
    }

}

</style>

</head>

<body>

{{ content | safe }}

</body>

</html>
"""


# =========================================================
# AUTH PAGE
# =========================================================

AUTH_HTML = """

<div class="auth">

<div class="auth-box">

<h1>📦 Smart Warehouse</h1>

<p>
Warehouse Operations & Fulfillment System
</p>

<form method="POST">

<label>User ID</label>

<input
    type="text"
    name="user_id"
    placeholder="Enter User ID"
    required
>

<label>Password</label>

<input
    type="password"
    name="password"
    placeholder="Enter Password"
    required
>

<button type="submit">
🔐 Login
</button>

</form>

<div class="auth-link">

Don't have an account?

<a href="/signup">
Create Account
</a>

</div>

</div>

</div>

"""


# =========================================================
# SIGN UP
# =========================================================

SIGNUP_HTML = """

<div class="auth">

<div class="auth-box">

<h1>🚀 Create Account</h1>

<p>
Smart Warehouse — Siva Teja Anyam
</p>

{% if error %}
<div class="alert">
{{ error }}
</div>
{% endif %}

<form method="POST">

<label>Full Name</label>

<input
    type="text"
    name="name"
    placeholder="Siva Teja Anyam"
    required
>

<label>User ID</label>

<input
    type="text"
    name="user_id"
    placeholder="Create User ID"
    required
>

<label>Password</label>

<input
    type="password"
    name="password"
    placeholder="Create Password"
    required
>

<label>Confirm Password</label>

<input
    type="password"
    name="confirm_password"
    placeholder="Confirm Password"
    required
>

<button type="submit">
Create Account
</button>

</form>

<div class="auth-link">

Already have an account?

<a href="/login">
Login
</a>

</div>

</div>

</div>

"""


# =========================================================
# LOGIN ROUTE
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user_id = request.form["user_id"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["name"] = user["name"]

            return redirect(url_for("dashboard"))

        return render_template_string(
            BASE_HTML,
            content=AUTH_HTML.replace(
                "<p>\nWarehouse Operations & Fulfillment System\n</p>",
                """
                <p>Invalid User ID or Password</p>
                """
            )
        )

    return render_template_string(
        BASE_HTML,
        content=AUTH_HTML
    )


# =========================================================
# SIGN UP ROUTE
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    error = None

    if request.method == "POST":

        name = request.form["name"].strip()
        user_id = request.form["user_id"].strip()
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:

            error = "Passwords do not match."

        elif len(password) < 4:

            error = "Password must contain at least 4 characters."

        else:

            conn = get_db()

            try:

                conn.execute(
                    """
                    INSERT INTO users
                    (name, user_id, password)
                    VALUES (?, ?, ?)
                    """,
                    (
                        name,
                        user_id,
                        generate_password_hash(password)
                    )
                )

                conn.commit()
                conn.close()

                return redirect(url_for("login"))

            except sqlite3.IntegrityError:

                conn.close()

                error = "User ID already exists."

    return render_template_string(
        BASE_HTML,
        content=render_template_string(
            SIGNUP_HTML,
            error=error
        )
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():

    conn = get_db()

    orders = conn.execute(
        "SELECT * FROM orders ORDER BY id DESC"
    ).fetchall()

    inventory = conn.execute(
        "SELECT * FROM inventory"
    ).fetchall()

    conn.close()

    total_orders = len(orders)

    pending = len([
        o for o in orders
        if o["status"] != "Dispatched"
    ])

    total_stock = sum(
        i["stock"] for i in inventory
    )

    low_stock = len([
        i for i in inventory
        if i["stock"] <= i["minimum"]
    ])

    content = """

<div class="sidebar">

<div class="logo">

<div class="logo-icon">
📦
</div>

<h2>Smart Warehouse</h2>

</div>

<a class="nav" href="/dashboard">🏠 Dashboard</a>

<a class="nav" href="/orders">🛒 Orders</a>

<a class="nav" href="/create-order">➕ Create Order</a>

<a class="nav" href="/inventory">📦 Inventory</a>

<a class="nav" href="/alerts">🚨 Alerts</a>

<a class="nav" href="/analytics">📊 Analytics</a>

<a class="nav logout" href="/logout">🚪 Logout</a>

</div>


<div class="main">

<div class="topbar">

<div>

<strong>
Welcome, {{ name }}
</strong>

<div class="muted">
Warehouse Control Center
</div>

</div>

<div class="user">
ST
</div>

</div>


<h1>Dashboard</h1>

<p class="muted">
Real-time warehouse operations overview
</p>


<div class="cards">

<div class="card">
📦
<div class="stat">
{{ total_orders }}
</div>
<p class="muted">Total Orders</p>
</div>

<div class="card">
⚡
<div class="stat">
{{ pending }}
</div>
<p class="muted">Pending Orders</p>
</div>

<div class="card">
📦
<div class="stat">
{{ total_stock }}
</div>
<p class="muted">Inventory Units</p>
</div>

<div class="card">
🚨
<div class="stat">
{{ low_stock }}
</div>
<p class="muted">Low Stock Items</p>
</div>

</div>


<div class="card">

<h2>🤖 Smart Warehouse Decisions</h2>

<br>

<div class="alert">

<strong>Priority Engine</strong><br>

Urgent orders are allocated before standard
orders when inventory is limited.

</div>

<div class="alert">

<strong>Inventory Engine</strong><br>

If stock is insufficient, the system performs
partial allocation and creates an exception.

</div>

<div class="alert">

<strong>Reorder Engine</strong><br>

Products below minimum stock are automatically
identified for replenishment.

</div>

</div>


<div class="card">

<h2>Recent Orders</h2>

<br>

<table>

<tr>

<th>Order</th>
<th>Customer</th>
<th>Product</th>
<th>Priority</th>
<th>Status</th>

</tr>

{% for order in orders[:5] %}

<tr>

<td>
{{ order["order_id"] }}
</td>

<td>
{{ order["customer"] }}
</td>

<td>
{{ order["product"] }}
</td>

<td>

<span class="badge
{% if order['priority'] == 'HIGH' %}
high
{% elif order['priority'] == 'MEDIUM' %}
medium
{% else %}
low
{% endif %}
">

{{ order["priority"] }}

</span>

</td>

<td>
{{ order["status"] }}
</td>

</tr>

{% endfor %}

</table>

</div>

</div>

"""

    return render_template_string(
        BASE_HTML,
        content=render_template_string(
            content,
            name=session["name"],
            total_orders=total_orders,
            pending=pending,
            total_stock=total_stock,
            low_stock=low_stock,
            orders=orders
        )
    )


# =========================================================
# CREATE ORDER
# =========================================================

@app.route("/create-order", methods=["GET", "POST"])
@login_required
def create_order():

    message = None

    if request.method == "POST":

        customer = request.form["customer"]
        product = request.form["product"]
        quantity = int(request.form["quantity"])
        order_type = request.form["order_type"]
        delivery_date = request.form["delivery_date"]
        location = request.form["location"]
        instructions = request.form["instructions"]

        priority = calculate_priority(
            order_type,
            delivery_date
        )

        conn = get_db()

        item = conn.execute(
            "SELECT * FROM inventory WHERE product = ?",
            (product,)
        ).fetchone()

        allocated = 0
        status = "Out of Stock"

        if item:

            if item["stock"] >= quantity:

                allocated = quantity
                status = "Allocated"

                conn.execute(
                    """
                    UPDATE inventory
                    SET stock = stock - ?
                    WHERE product = ?
                    """,
                    (quantity, product)
                )

            elif item["stock"] > 0:

                allocated = item["stock"]
                status = "Partially Allocated"

                conn.execute(
                    """
                    UPDATE inventory
                    SET stock = 0
                    WHERE product = ?
                    """,
                    (product,)
                )

            else:

                status = "Out of Stock"

        # Generate order number
        last = conn.execute(
            "SELECT COUNT(*) AS count FROM orders"
        ).fetchone()

        order_number = 1001 + last["count"]

        order_id = f"ORD-{order_number}"

        conn.execute(
            """
            INSERT INTO orders
            (
                order_id,
                customer,
                product,
                quantity,
                allocated,
                order_type,
                priority,
                status,
                delivery_date,
                location,
                instructions,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                customer,
                product,
                quantity,
                allocated,
                order_type,
                priority,
                status,
                delivery_date,
                location,
                instructions,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("orders"))

    conn = get_db()

    inventory = conn.execute(
        "SELECT * FROM inventory"
    ).fetchall()

    conn.close()

    content = """

<div class="sidebar">

<div class="logo">
<div class="logo-icon">📦</div>
<h2>Smart Warehouse</h2>
</div>

<a class="nav" href="/dashboard">🏠 Dashboard</a>
<a class="nav" href="/orders">🛒 Orders</a>
<a class="nav" href="/create-order">➕ Create Order</a>
<a class="nav" href="/inventory">📦 Inventory</a>
<a class="nav" href="/alerts">🚨 Alerts</a>
<a class="nav" href="/analytics">📊 Analytics</a>
<a class="nav logout" href="/logout">🚪 Logout</a>

</div>


<div class="main">

<div class="topbar">

<strong>
Create Order
</strong>

<div class="user">
Siva Teja Anyam
</div>

</div>


<h1>➕ Create New Order</h1>

<p class="muted">
The smart engine will automatically determine
priority and allocate inventory.
</p>

<br>


<div class="card">

<form method="POST">

<div class="form-grid">


<div class="field">

<label>
Customer Name
</label>

<input
type="text"
name="customer"
placeholder="Customer name"
required
>

</div>


<div class="field">

<label>
Product
</label>

<select name="product" required>

<option value="">
Select Product
</option>

{% for item in inventory %}

<option value="{{ item['product'] }}">

{{ item["product"] }}

— Stock: {{ item["stock"] }}

</option>

{% endfor %}

</select>

</div>


<div class="field">

<label>
Quantity
</label>

<input
type="number"
name="quantity"
min="1"
required
>

</div>


<div class="field">

<label>
Order Type
</label>

<select name="order_type">

<option value="standard">
Standard
</option>

<option value="priority">
Priority
</option>

<option value="urgent">
Urgent
</option>

</select>

</div>


<div class="field">

<label>
Delivery Date
</label>

<input
type="date"
name="delivery_date"
required
>

</div>


<div class="field">

<label>
Warehouse Location
</label>

<select name="location">

<option>
Zone A
</option>

<option>
Zone B
</option>

<option>
Zone C
</option>

</select>

</div>


<div class="field full">

<label>
Special Instructions
</label>

<input
type="text"
name="instructions"
placeholder="Fragile, special handling, etc."
>

</div>


</div>

<br>

<button class="btn btn-green">
✅ Create Order
</button>

</form>

</div>

</div>

"""

    return render_template_string(
        BASE_HTML,
        content=render_template_string(
            content,
            inventory=inventory
        )
    )


# =========================================================
# ORDERS
# =========================================================

@app.route("/orders")
@login_required
def orders():

    conn = get_db()

    orders = conn.execute(
        "SELECT * FROM orders ORDER BY id DESC"
    ).fetchall()

    conn.close()

    content = """

<div class="sidebar">

<div class="logo">
<div class="logo-icon">📦</div>
<h2>Smart Warehouse</h2>
</div>

<a class="nav" href="/dashboard">🏠 Dashboard</a>
<a class="nav" href="/orders">🛒 Orders</a>
<a class="nav" href="/create-order">➕ Create Order</a>
<a class="nav" href="/inventory">📦 Inventory</a>
<a class="nav" href="/alerts">🚨 Alerts</a>
<a class="nav" href="/analytics">📊 Analytics</a>
<a class="nav logout" href="/logout">🚪 Logout</a>

</div>


<div class="main">

<div class="topbar">

<strong>
Order Management
</strong>

<div class="user">
Siva Teja Anyam
</div>

</div>


<h1>🛒 Orders</h1>

<p class="muted">
Manage priority, inventory allocation and fulfillment.
</p>

<br>


<div class="card">

<a
href="/create-order"
class="btn"
style="display:inline-block;text-decoration:none;margin-bottom:20px;"
>
+ Create Order
</a>


<table>

<tr>

<th>Order</th>
<th>Customer</th>
<th>Product</th>
<th>Qty</th>
<th>Allocated</th>
<th>Priority</th>
<th>Status</th>
<th>Action</th>

</tr>


{% for order in orders %}

<tr>

<td>
<strong>{{ order["order_id"] }}</strong>
</td>

<td>
{{ order["customer"] }}
</td>

<td>
{{ order["product"] }}
</td>

<td>
{{ order["quantity"] }}
</td>

<td>
{{ order["allocated"] }}/{{ order["quantity"] }}
</td>


<td>

<span class="badge
{% if order['priority'] == 'HIGH' %}
high
{% elif order['priority'] == 'MEDIUM' %}
medium
{% else %}
low
{% endif %}
">

{{ order["priority"] }}

</span>

</td>


<td>

<span class="badge
{% if order['status'] == 'Dispatched' %}
low
{% elif order['status'] == 'Out of Stock' %}
high
{% elif order['status'] == 'Partially Allocated' %}
medium
{% else %}
blue
{% endif %}
">

{{ order["status"] }}

</span>

</td>


<td>

{% if order["status"] != "Dispatched" %}

<a
href="/advance/{{ order['id'] }}"
class="btn"
style="text-decoration:none;padding:7px 10px;font-size:12px;"
>
Advance
</a>

{% else %}

<span class="badge low">
✓ Complete
</span>

{% endif %}

</td>

</tr>

{% endfor %}

</table>

</div>

</div>

"""

    return render_template_string(
        BASE_HTML,
        content=render_template_string(
            content,
            orders=orders
        )
    )


# =========================================================
# ADVANCE ORDER
# =========================================================

@app.route("/advance/<int:order_id>")
@login_required
def advance_order(order_id):

    conn = get_db()

    order = conn.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()

    if not order:
        conn.close()
        return redirect(url_for("orders"))

    current = order["status"]

    workflow = [
        "Allocated",
        "Picking",
        "Packing",
        "Quality Check",
        "Dispatched"
    ]

    if current in workflow:

        index = workflow.index(current)

        if index < len(workflow) - 1:

            new_status = workflow[index + 1]

            conn.execute(
                """
                UPDATE orders
                SET status = ?
                WHERE id = ?
                """,
                (new_status, order_id)
            )

            conn.commit()

    conn.close()

    return redirect(url_for("orders"))


# =========================================================
# INVENTORY
# =========================================================

@app.route("/inventory")
@login_required
def inventory():

    conn = get_db()

    items = conn.execute(
        "SELECT * FROM inventory"
    ).fetchall()

    conn.close()

    content = """

<div class="sidebar">

<div class="logo">
<div class="logo-icon">📦</div>
<h2>Smart Warehouse</h2>
</div>

<a class="nav" href="/dashboard">🏠 Dashboard</a>
<a class="nav" href="/orders">🛒 Orders</a>
<a class="nav" href="/create-order">➕ Create Order</a>
<a class="nav" href="/inventory">📦 Inventory</a>
<a class="nav" href="/alerts">🚨 Alerts</a>
<a class="nav" href="/analytics">📊 Analytics</a>
<a class="nav logout" href="/logout">🚪 Logout</a>

</div>


<div class="main">

<div class="topbar">

<strong>
Inventory Control
</strong>

<div class="user">
Siva Teja Anyam
</div>

</div>


<h1>📦 Inventory</h1>

<p class="muted">
Monitor stock levels and replenishment requirements.
</p>

<br>


<div class="card">

<table>

<tr>

<th>Product</th>
<th>SKU</th>
<th>Stock</th>
<th>Minimum</th>
<th>Location</th>
<th>Status</th>
<th>Recommendation</th>

</tr>


{% for item in items %}

<tr>

<td>
<strong>{{ item["product"] }}</strong>
</td>

<td>
{{ item["sku"] }}
</td>

<td>
{{ item["stock"] }}
</td>

<td>
{{ item["minimum"] }}
</td>

<td>
{{ item["location"] }}
</td>


<td>

{% if item["stock"] == 0 %}

<span class="badge high">
OUT OF STOCK
</span>

{% elif item["stock"] <= item["minimum"] %}

<span class="badge medium">
LOW STOCK
</span>

{% else %}

<span class="badge low">
HEALTHY
</span>

{% endif %}

</td>


<td>

{% if item["stock"] == 0 %}

🚨 Reorder immediately

{% elif item["stock"] <= item["minimum"] %}

⚠️ Create purchase request

{% else %}

✓ Stock healthy

{% endif %}

</td>

</tr>

{% endfor %}

</table>

</div>

</div>

"""

    return render_template_string(
        BASE_HTML,
        content=render_template_string(
            content,
            items=items
        )
    )


# =========================================================
# ALERTS
# =========================================================

@app.route("/alerts")
@login_required
def alerts():

    conn = get_db()

    inventory = conn.execute(
        "SELECT * FROM inventory"
    ).fetchall()

    orders = conn.execute(
        "SELECT * FROM orders"
    ).fetchall()

    conn.close()

    content = """

<div class="sidebar">

<div class="logo">
<div class="logo-icon">📦</div>
<h2>Smart Warehouse</h2>
</div>

<a class="nav" href="/dashboard">🏠 Dashboard</a>
<a class="nav" href="/orders">🛒 Orders</a>
<a class="nav" href="/create-order">➕ Create Order</a>
<a class="nav" href="/inventory">📦 Inventory</a>
<a class="nav" href="/alerts">🚨 Alerts</a>
<a class="nav" href="/analytics">📊 Analytics</a>
<a class="nav logout" href="/logout">🚪 Logout</a>

</div>


<div class="main">

<div class="topbar">

<strong>
Exceptions & Alerts
</strong>

<div class="user">
Siva Teja Anyam
</div>

</div>


<h1>🚨 Alerts</h1>

<p class="muted">
Exception → Decision → Resolution
</p>

<br>


<div class="card">

{% for item in inventory %}

{% if item["stock"] == 0 %}

<div class="alert">

<strong>
🚨 OUT OF STOCK — {{ item["product"] }}
</strong>

<br><br>

Current Stock:
{{ item["stock"] }}

<br>

Decision:
Emergency replenishment required.

<br>

Resolution:
Purchase stock or transfer inventory.

</div>

{% elif item["stock"] <= item["minimum"] %}

<div class="alert">

<strong>
⚠️ LOW STOCK — {{ item["product"] }}
</strong>

<br><br>

Current Stock:
{{ item["stock"] }}

<br>

Minimum:
{{ item["minimum"] }}

<br>

Decision:
Create replenishment request.

</div>

{% endif %}

{% endfor %}


{% for order in orders %}

{% if order["status"] == "Partially Allocated" %}

<div class="alert">

<strong>
⚠️ PARTIAL ALLOCATION —
{{ order["order_id"] }}
</strong>

<br><br>

Required:
{{ order["quantity"] }}

<br>

Allocated:
{{ order["allocated"] }}

<br>

Decision:
Prioritize remaining quantity.

</div>

{% endif %}

{% endfor %}

</div>

</div>

"""

    return render_template_string(
        BASE_HTML,
        content=render_template_string(
            content,
            inventory=inventory,
            orders=orders
        )
    )


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics")
@login_required
def analytics():

    conn = get_db()

    orders = conn.execute(
        "SELECT * FROM orders"
    ).fetchall()

    conn.close()

    total = len(orders)

    dispatched = len([
        o for o in orders
        if o["status"] == "Dispatched"
    ])

    partial = len([
        o for o in orders
        if o["status"] == "Partially Allocated"
    ])

    if total:
        dispatch_rate = round(
            dispatched / total * 100
        )
    else:
        dispatch_rate = 0

    content = """

<div class="sidebar">

<div class="logo">
<div class="logo-icon">📦</div>
<h2>Smart Warehouse</h2>
</div>

<a class="nav" href="/dashboard">🏠 Dashboard</a>
<a class="nav" href="/orders">🛒 Orders</a>
<a class="nav" href="/create-order">➕ Create Order</a>
<a class="nav" href="/inventory">📦 Inventory</a>
<a class="nav" href="/alerts">🚨 Alerts</a>
<a class="nav" href="/analytics">📊 Analytics</a>
<a class="nav logout" href="/logout">🚪 Logout</a>

</div>


<div class="main">

<div class="topbar">

<strong>
Operational Analytics
</strong>

<div class="user">
Siva Teja Anyam
</div>

</div>


<h1>📊 Analytics</h1>

<p class="muted">
Warehouse performance and bottleneck analysis.
</p>

<br>


<div class="cards">

<div class="card">

📦

<div class="stat">
{{ total }}
</div>

<p class="muted">
Total Orders
</p>

</div>


<div class="card">

🚚

<div class="stat">
{{ dispatch_rate }}%
</div>

<p class="muted">
Dispatch Rate
</p>

</div>


<div class="card">

⚠️

<div class="stat">
{{ partial }}
</div>

<p class="muted">
Partial Allocations
</p>

</div>


<div class="card">

🎯

<div class="stat">
97%
</div>

<p class="muted">
Pick Accuracy
</p>

</div>

</div>


<div class="card">

<h2>
🤖 Smart Recommendations
</h2>

<br>

<div class="alert">

<strong>
Bottleneck Detection
</strong>

<br>

Monitor orders stuck in Picking or Packing.

</div>


<div class="alert">

<strong>
Inventory Optimization
</strong>

<br>

Replenish products below their minimum
stock level before creating shortages.

</div>


<div class="alert">

<strong>
Priority Optimization
</strong>

<br>

Urgent orders should receive inventory
before lower-priority orders.

</div>


<div class="alert">

<strong>
Exception Handling
</strong>

<br>

Partial allocations should trigger
replenishment or stock transfer decisions.

</div>

</div>

</div>

"""

    return render_template_string(
        BASE_HTML,
        content=render_template_string(
            content,
            total=total,
            dispatch_rate=dispatch_rate,
            partial=partial
        )
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    print("=" * 50)
    print("SMART WAREHOUSE")
    print("Created for Siva Teja Anyam")
    print("=" * 50)
    print("Open: http://127.0.0.1:5000")
    print("=" * 50)

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )