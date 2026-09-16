from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import sqlite3
import os
import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
STORE_PHONE = "918178085392"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    conn = sqlite3.connect('hardware.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # Products table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            size_mm TEXT,
            size_inch TEXT,
            gauge TEXT,
            weight TEXT,
            packing TEXT,
            retail_price REAL NOT NULL,
            wholesale_price REAL,
            unit TEXT,
            stock TEXT DEFAULT 'In Stock',
            image_path TEXT
        )
    ''')
    # Orders table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE,
            customer_name TEXT,
            customer_phone TEXT,
            customer_address TEXT,
            product_name TEXT,
            product_specs TEXT,
            quantity INTEGER,
            rate REAL,
            total_amount REAL,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------- MODERN HTML TEMPLATES -----------------

BASE_HEADER = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Arfa Trading - Wholesale & Retail Hardware</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #0f172a;
            --accent: #2563eb;
            --secondary: #f59e0b;
            --success: #10b981;
            --danger: #ef4444;
            --bg: #f8fafc;
            --surface: #ffffff;
            --text-dark: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background: var(--bg); color: var(--text-dark); padding-bottom: 75px; -webkit-tap-highlight-color: transparent; }

        /* Top Navbar */
        .top-nav { background: var(--primary); color: white; padding: 14px 18px; position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
        .nav-wrap { display: flex; justify-content: space-between; align-items: center; max-width: 800px; margin: auto; }
        .logo-area { display: flex; align-items: center; gap: 8px; }
        .logo-badge { background: linear-gradient(135deg, #f59e0b, #d97706); width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 18px; color: #fff; }
        .logo-title { font-size: 19px; font-weight: 800; letter-spacing: -0.5px; }
        .logo-sub { font-size: 10px; color: #94a3b8; letter-spacing: 0.5px; text-transform: uppercase; }

        /* Search Section */
        .search-container { max-width: 800px; margin: 14px auto 8px auto; padding: 0 16px; }
        .search-bar { background: var(--surface); display: flex; align-items: center; padding: 6px 14px; border-radius: 12px; border: 1.5px solid var(--border); box-shadow: 0 2px 6px rgba(0,0,0,0.03); }
        .search-bar input { border: none; outline: none; width: 100%; font-size: 14px; padding: 6px; color: var(--text-dark); }
        .search-bar button { background: var(--accent); color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; }

        /* Bottom Fixed Bar */
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: var(--surface); border-top: 1px solid var(--border); display: flex; justify-content: space-around; padding: 10px 0; z-index: 100; box-shadow: 0 -3px 15px rgba(0,0,0,0.05); }
        .bottom-nav a { text-decoration: none; color: var(--text-muted); font-size: 11px; font-weight: 600; display: flex; flex-direction: column; align-items: center; gap: 3px; }
        .bottom-nav a.active { color: var(--accent); }
    </style>
"""

STORE_TEMPLATE = BASE_HEADER + """
    <style>
        .catalog { max-width: 800px; margin: auto; padding: 12px 16px; }
        .item-card { background: var(--surface); border-radius: 14px; padding: 14px; margin-bottom: 16px; display: flex; gap: 14px; border: 1px solid var(--border); box-shadow: 0 3px 8px rgba(0,0,0,0.03); transition: 0.2s ease; }
        .item-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.07); }
        
        .img-box { width: 115px; min-width: 115px; height: 115px; border-radius: 10px; overflow: hidden; background: #f1f5f9; display: flex; align-items: center; justify-content: center; }
        .img-box img { width: 100%; height: 100%; object-fit: cover; }

        .details-box { flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
        .category-chip { font-size: 10px; font-weight: 700; color: var(--accent); text-transform: uppercase; background: #eff6ff; padding: 2px 7px; border-radius: 4px; display: inline-block; width: fit-content; margin-bottom: 4px; }
        .item-name { font-size: 16px; font-weight: 700; color: var(--text-dark); margin-bottom: 5px; }

        .spec-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
        .tag { background: #f8fafc; border: 1px solid #cbd5e1; font-size: 11px; font-weight: 600; color: #475569; padding: 2px 6px; border-radius: 4px; }

        .price-section { display: flex; align-items: baseline; gap: 6px; }
        .main-rate { font-size: 18px; font-weight: 800; color: #16a34a; }
        .unit-label { font-size: 12px; color: var(--text-muted); }
        .ws-rate { font-size: 11px; color: #ea580c; font-weight: 600; }

        .btn-order-now { background: linear-gradient(135deg, #f59e0b, #d97706); color: white; border: none; padding: 9px 14px; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer; width: 100%; margin-top: 8px; box-shadow: 0 2px 6px rgba(245,158,11,0.3); }

        /* Order Modal */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15,23,42,0.6); backdrop-filter: blur(4px); align-items: center; justify-content: center; z-index: 1000; }
        .modal-body { background: white; width: 92%; max-width: 380px; border-radius: 16px; padding: 20px; max-height: 90vh; overflow-y: auto; }
        .modal-title { font-size: 18px; font-weight: 800; color: var(--primary); margin-bottom: 4px; }
        .field { margin-bottom: 12px; }
        .field label { display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; }
        .field input, .field textarea { width: 100%; padding: 10px 12px; border: 1.5px solid var(--border); border-radius: 8px; font-size: 14px; outline: none; }
        .field input:focus, .field textarea:focus { border-color: var(--accent); }
    </style>
</head>
<body>

<header class="top-nav">
    <div class="nav-wrap">
        <div class="logo-area">
            <div class="logo-badge">A</div>
            <div>
                <div class="logo-title">Arfa Trading</div>
                <div class="logo-sub">Hardware & Industrial Store</div>
            </div>
        </div>
        <a href="/admin" style="color: #f8fafc; text-decoration: none; font-size: 12px; font-weight: 600; background: rgba(255,255,255,0.12); padding: 5px 10px; border-radius: 6px;">Admin Panel</a>
    </div>
</header>

<div class="search-container">
    <form method="GET" action="/" class="search-bar">
        <input type="text" name="q" placeholder="Search: 16mm, Aldrop, Kabja, 8 Inch..." value="{{ query or '' }}">
        <button type="submit">Search</button>
    </form>
</div>

<div class="catalog">
    {% if not items %}
    <div style="text-align:center; padding: 40px 10px; color: var(--text-muted);">
        <p style="font-size: 16px; font-weight: 600;">Koi Saman Nahi Mila</p>
        <p style="font-size: 12px; margin-top: 4px;">Naya item add karne ke liye Admin par jayein.</p>
    </div>
    {% endif %}

    {% for item in items %}
    <div class="item-card">
        <div class="img-box">
            {% if item.image_path %}
            <img src="/{{ item.image_path }}" alt="{{ item.name }}">
            {% else %}
            <span style="font-size: 12px; color: #94a3b8; font-weight: 600;">Hardware</span>
            {% endif %}
        </div>
        <div class="details-box">
            <div>
                <span class="category-chip">{{ item.category or 'Hardware' }}</span>
                <div class="item-name">{{ item.name }}</div>
                <div class="spec-tags">
                    {% if item.size_mm %}<span class="tag">📏 {{ item.size_mm }}</span>{% endif %}
                    {% if item.size_inch %}<span class="tag">📐 {{ item.size_inch }}</span>{% endif %}
                    {% if item.gauge %}<span class="tag">⚙️ {{ item.gauge }}</span>{% endif %}
                    {% if item.weight %}<span class="tag">⚖️ {{ item.weight }}</span>{% endif %}
                    {% if item.packing %}<span class="tag">📦 {{ item.packing }}</span>{% endif %}
                </div>
            </div>

            <div>
                <div class="price-section">
                    <span class="main-rate">₹{{ item.retail_price }}</span>
                    <span class="unit-label">/ {{ item.unit }}</span>
                    {% if item.wholesale_price %}
                    <span class="ws-rate">(WS: ₹{{ item.wholesale_price }})</span>
                    {% endif %}
                </div>
                <button class="btn-order-now" onclick="openOrderModal('{{ item.name }}', {{ item.retail_price }}, '{{ item.size_mm or '' }} {{ item.size_inch or '' }}', '{{ item.unit }}')">⚡ Abhi Order Karein</button>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

<!-- Modal Form -->
<div id="orderModal" class="modal">
    <div class="modal-body">
        <h3 id="mTitle" class="modal-title">Order Product</h3>
        <p id="mRate" style="color: #16a34a; font-weight: 700; margin-bottom: 12px; font-size: 14px;"></p>
        
        <form method="POST" action="/place-order" id="orderForm">
            <input type="hidden" name="product_name" id="fName">
            <input type="hidden" name="rate" id="fRate">
            <input type="hidden" name="specs" id="fSpecs">
            <input type="hidden" name="unit" id="fUnit">

            <div class="field">
                <label>Aapka Naam *</label>
                <input type="text" name="customer_name" required placeholder="Poora naam likhein">
            </div>
            <div class="field">
                <label>Mobile Number *</label>
                <input type="tel" name="customer_phone" required placeholder="Calling / WhatsApp number">
            </div>
            <div class="field">
                <label>Kitna Quantity / Packet Chahiye *</label>
                <input type="number" name="quantity" id="fQty" value="1" min="1" required oninput="calculateTotal()">
            </div>
            <div class="field">
                <label>Dukaan / Ghar Ka Pata (Address) *</label>
                <textarea name="customer_address" rows="2" required placeholder="Gali, shahar, pin code"></textarea>
            </div>

            <div style="background:#f1f5f9; padding: 10px; border-radius: 8px; margin-bottom: 12px; font-weight: 700; font-size: 14px;">
                Total Estimated Bill: <span id="mTotal" style="color:#16a34a;">₹0</span>
            </div>

            <button type="submit" class="btn-order-now" style="width: 100%; padding: 12px; font-size: 15px;">✓ Confirm & Send WhatsApp</button>
            <button type="button" onclick="closeModal()" style="width: 100%; background: transparent; border: none; color: var(--text-muted); font-size: 13px; font-weight: 600; margin-top: 10px; cursor: pointer;">Wapas Cancel Karein</button>
        </form>
    </div>
</div>

<nav class="bottom-nav">
    <a href="/" class="active"><span>🏠</span><span>Store</span></a>
    <a href="/my-orders"><span>📦</span><span>Orders List</span></a>
    <a href="/admin"><span>⚙️</span><span>Admin</span></a>
</nav>

<script>
let currentRate = 0;

function openOrderModal(name, rate, specs, unit) {
    currentRate = rate;
    document.getElementById('fName').value = name;
    document.getElementById('fRate').value = rate;
    document.getElementById('fSpecs').value = specs;
    document.getElementById('fUnit').value = unit;

    document.getElementById('mTitle').innerText = name;
    document.getElementById('mRate').innerText = 'Rate: ₹' + rate + ' / ' + unit + ' (' + specs + ')';
    calculateTotal();
    document.getElementById('orderModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('orderModal').style.display = 'none';
}

function calculateTotal() {
    const qty = document.getElementById('fQty').value || 1;
    const tot = currentRate * qty;
    document.getElementById('mTotal').innerText = '₹' + tot;
}
</script>

</body>
</html>
"""

ORDERS_LIST_TEMPLATE = BASE_HEADER + """
    <style>
        .wrap { max-width: 800px; margin: auto; padding: 16px; }
        .order-card { background: white; border-radius: 12px; padding: 14px; margin-bottom: 12px; border: 1px solid var(--border); box-shadow: 0 2px 6px rgba(0,0,0,0.04); }
        .order-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 8px; }
        .status-badge { font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; }
        .status-Pending { background: #fef3c7; color: #b45309; }
        .status-Delivered { background: #dcfce7; color: #15803d; }
        .status-Cancelled { background: #fee2e2; color: #b91c1c; }
        .btn-cancel { background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer; text-decoration: none; }
    </style>
</head>
<body>

<header class="top-nav">
    <div class="nav-wrap">
        <div class="logo-title">Aapke Orders</div>
        <a href="/" style="color:white; text-decoration:none; font-size:13px; font-weight:600;">← Store</a>
    </div>
</header>

<div class="wrap">
    {% if not orders %}
    <p style="text-align:center; color:#64748b; margin-top: 40px;">Abhi koi order nahi hai.</p>
    {% endif %}

    {% for o in orders %}
    <div class="order-card">
        <div class="order-header">
            <div>
                <strong style="font-size:14px; color:#0f172a;">#{{ o.order_code }}</strong>
                <div style="font-size:11px; color:#64748b;">{{ o.created_at }}</div>
            </div>
            <span class="status-badge status-{{ o.status }}">{{ o.status }}</span>
        </div>

        <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 4px;">{{ o.product_name }}</div>
        <div style="font-size: 12px; color: #475569; margin-bottom: 8px;">Qty: <b>{{ o.quantity }}</b> | Total Bill: <b style="color:#16a34a;">₹{{ o.total_amount }}</b></div>
        <div style="font-size: 12px; color: #64748b; background: #f8fafc; padding: 6px 10px; border-radius: 6px;">
            <b>Customer:</b> {{ o.customer_name }} ({{ o.customer_phone }})<br>
            <b>Address:</b> {{ o.customer_address }}
        </div>

        {% if o.status == 'Pending' %}
        <div style="margin-top: 10px; text-align: right;">
            <a href="/cancel-order/{{ o.id }}" class="btn-cancel" onclick="return confirm('Kya aap sach me ye order cancel karna chahte hain?')">Order Cancel Karein</a>
        </div>
        {% endif %}
    </div>
    {% endfor %}
</div>

<nav class="bottom-nav">
    <a href="/"><span>🏠</span><span>Store</span></a>
    <a href="/my-orders" class="active"><span>📦</span><span>Orders List</span></a>
    <a href="/admin"><span>⚙️</span><span>Admin</span></a>
</nav>

</body>
</html>
"""

ADMIN_TEMPLATE = BASE_HEADER + """
    <style>
        .admin-wrap { max-width: 800px; margin: auto; padding: 16px; }
        .panel-card { background: white; padding: 18px; border-radius: 14px; border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 20px; }
        h2 { font-size: 18px; color: var(--primary); margin-bottom: 12px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; }
        
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
        .field { margin-bottom: 10px; }
        .field label { display: block; font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 3px; }
        .field input, .field select { width: 100%; padding: 8px 10px; border: 1.5px solid var(--border); border-radius: 6px; font-size: 13px; outline: none; }
        
        .btn-submit { background: var(--accent); color: white; border: none; padding: 11px; width: 100%; border-radius: 8px; font-weight: 700; font-size: 14px; cursor: pointer; margin-top: 10px; }
        
        table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 10px; }
        th, td { padding: 8px; border-bottom: 1px solid var(--border); text-align: left; }
        th { background: #f8fafc; color: #475569; }
        .badge-status { padding: 3px 6px; border-radius: 4px; font-weight: 700; font-size: 10px; }
    </style>
</head>
<body>

<header class="top-nav">
    <div class="nav-wrap">
        <div class="logo-title">Admin Dashboard</div>
        <a href="/" style="color:white; text-decoration:none; font-size:13px; font-weight:600;">← Store Dekhein</a>
    </div>
</header>

<div class="admin-wrap">
    <!-- Add Item Form -->
    <div class="panel-card">
        <h2>+ Naya Hardware Saman Jodein</h2>
        <form method="POST" action="/admin/add" enctype="multipart/form-data">
            <div class="field">
                <label>Saman Ka Naam (Product Name) *</label>
                <input type="text" name="name" placeholder="Jaise: Aldrop, Kabja, Tower Bolt" required>
            </div>

            <div class="grid-2">
                <div class="field">
                    <label>Category</label>
                    <select name="category">
                        <option value="Aldrop">Aldrop</option>
                        <option value="Kabja / Hinges">Kabja / Hinges</option>
                        <option value="Tower Bolt">Tower Bolt</option>
                        <option value="Screws & Nut-Bolt">Screws & Nut-Bolt</option>
                        <option value="Door Handles">Door Handles</option>
                        <option value="General Hardware">General Hardware</option>
                    </select>
                </div>
                <div class="field">
                    <label>Gez / Gauge</label>
                    <input type="text" name="gauge" placeholder="e.g. 6 Gez, 8 Gez">
                </div>
            </div>

            <div class="grid-2">
                <div class="field">
                    <label>Size (MM)</label>
                    <input type="text" name="size_mm" placeholder="e.g. 16mm, 50mm">
                </div>
                <div class="field">
                    <label>Size (Inch)</label>
                    <input type="text" name="size_inch" placeholder="e.g. 3 Inch, 8 Inch">
                </div>
            </div>

            <div class="grid-2">
                <div class="field">
                    <label>Wajan (Weight)</label>
                    <input type="text" name="weight" placeholder="e.g. 450 gm, 1.2 kg">
                </div>
                <div class="field">
                    <label>Packing (Pkt/Box)</label>
                    <input type="text" name="packing" placeholder="e.g. 10 Pcs/Pkt, 1 Box">
                </div>
            </div>

            <div class="grid-3">
                <div class="field">
                    <label>Retail Price (₹) *</label>
                    <input type="number" step="any" name="retail_price" placeholder="Rate" required>
                </div>
                <div class="field">
                    <label>Wholesale (₹)</label>
                    <input type="number" step="any" name="wholesale_price" placeholder="Rate">
                </div>
                <div class="field">
                    <label>Unit *</label>
                    <select name="unit">
                        <option value="Piece">Piece</option>
                        <option value="Pkt">Packet (Pkt)</option>
                        <option value="Kg">Kg</option>
                        <option value="Pair">Pair</option>
                        <option value="Box">Box</option>
                        <option value="Dozen">Dozen</option>
                    </select>
                </div>
            </div>

            <div class="field" style="margin-top: 6px;">
                <label>Photo Chunein (Gallery ya Camera)</label>
                <input type="file" name="product_image" accept="image/*">
            </div>

            <button type="submit" class="btn-submit">💾 Saman Save Karein</button>
        </form>
    </div>

    <!-- Orders Management -->
    <div class="panel-card">
        <h2>Sabhi Customer Orders</h2>
        <div style="overflow-x:auto;">
            <table>
                <tr>
                    <th>Order #</th>
                    <th>Customer</th>
                    <th>Item & Qty</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th>Change Status</th>
                </tr>
                {% for o in orders %}
                <tr>
                    <td><b>#{{ o.order_code }}</b></td>
                    <td>{{ o.customer_name }}<br><small>{{ o.customer_phone }}</small></td>
                    <td>{{ o.product_name }} ({{ o.quantity }})</td>
                    <td>₹{{ o.total_amount }}</td>
                    <td><span class="badge-status">{{ o.status }}</span></td>
                    <td>
                        <a href="/admin/order-status/{{ o.id }}/Delivered" style="color:green; font-weight:700; text-decoration:none;">Deliver</a> | 
                        <a href="/admin/order-status/{{ o.id }}/Cancelled" style="color:red; font-weight:700; text-decoration:none;">Cancel</a>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <!-- Product list -->
    <div class="panel-card">
        <h2>Dukan Me Maujood Saman</h2>
        <div style="overflow-x:auto;">
            <table>
                <tr>
                    <th>Naam</th>
                    <th>Size</th>
                    <th>Rate</th>
                    <th>Action</th>
                </tr>
                {% for item in items %}
                <tr>
                    <td>{{ item.name }}</td>
                    <td>{{ item.size_mm or '' }} {{ item.size_inch or '' }}</td>
                    <td>₹{{ item.retail_price }}</td>
                    <td><a href="/admin/delete/{{ item.id }}" style="color:red; font-weight:700;" onclick="return confirm('Hata dein?')">Delete</a></td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</div>

<nav class="bottom-nav">
    <a href="/"><span>🏠</span><span>Store</span></a>
    <a href="/my-orders"><span>📦</span><span>Orders List</span></a>
    <a href="/admin" class="active"><span>⚙️</span><span>Admin</span></a>
</nav>

</body>
</html>
"""

# ----------------- BACKEND ROUTES -----------------

@app.route('/')
def home():
    query = request.args.get('q', '').strip()
    conn = get_db()
    if query:
        items = conn.execute(
            "SELECT * FROM products WHERE name LIKE ? OR size_mm LIKE ? OR size_inch LIKE ? OR category LIKE ? ORDER BY id DESC",
            (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')
        ).fetchall()
    else:
        items = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(STORE_TEMPLATE, items=items, query=query)

@app.route('/place-order', methods=['POST'])
def place_order():
    p_name = request.form.get('product_name')
    rate = float(request.form.get('rate') or 0)
    specs = request.form.get('specs') or ''
    unit = request.form.get('unit') or 'Pcs'
    qty = int(request.form.get('quantity') or 1)
    c_name = request.form.get('customer_name')
    c_phone = request.form.get('customer_phone')
    c_addr = request.form.get('customer_address')
    
    total = rate * qty
    code = f"ARFA-{os.urandom(3).hex().upper()}"
    now_str = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Save to Database
    conn = get_db()
    conn.execute('''
        INSERT INTO orders (order_code, customer_name, customer_phone, customer_address, product_name, product_specs, quantity, rate, total_amount, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
    ''', (code, c_name, c_phone, c_addr, p_name, specs, qty, rate, total, now_str))
    conn.commit()
    conn.close()

    # WhatsApp Message
    msg = (
        f"*🛒 NAYA ORDER - ARFA TRADING*%0A"
        f"*Order ID:* #{code}%0A"
        f"--------------------------------%0A"
        f"*Saman:* {p_name}%0A"
        f"*Specs:* {specs}%0A"
        f"*Rate:* Rs.{rate} / {unit}%0A"
        f"*Quantity:* {qty} {unit}%0A"
        f"*Total Bill:* Rs.{total}%0A"
        f"--------------------------------%0A"
        f"*Customer Details:*%0A"
        f"*Naam:* {c_name}%0A"
        f"*Phone:* {c_phone}%0A"
        f"*Pata:* {c_addr}%0A"
        f"--------------------------------%0A"
        f"Status: Pending Order"
    )

    whatsapp_url = f"https://wa.me/{STORE_PHONE}?text={msg}"
    return redirect(whatsapp_url)

@app.route('/my-orders')
def my_orders():
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(ORDERS_LIST_TEMPLATE, orders=orders)

@app.route('/cancel-order/<int:order_id>')
def cancel_order(order_id):
    conn = get_db()
    conn.execute("UPDATE orders SET status = 'Cancelled' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('my_orders'))

@app.route('/admin')
def admin():
    conn = get_db()
    items = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, items=items, orders=orders)

@app.route('/admin/order-status/<int:order_id>/<string:new_status>')
def update_order_status(order_id, new_status):
    conn = get_db()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/add', methods=['POST'])
def add_product():
    name = request.form.get('name')
    category = request.form.get('category')
    gauge = request.form.get('gauge')
    size_mm = request.form.get('size_mm')
    size_inch = request.form.get('size_inch')
    weight = request.form.get('weight')
    packing = request.form.get('packing')
    retail_price = float(request.form.get('retail_price') or 0)
    wholesale_price = float(request.form.get('wholesale_price') or 0)
    unit = request.form.get('unit')

    image_path = None
    file = request.files.get('product_image')
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_name = f"{os.urandom(4).hex()}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(save_path)
        image_path = save_path

    conn = get_db()
    conn.execute('''
        INSERT INTO products (name, category, size_mm, size_inch, gauge, weight, packing, retail_price, wholesale_price, unit, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, category, size_mm, size_inch, gauge, weight, packing, retail_price, wholesale_price, unit, image_path))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))

@app.route('/admin/delete/<int:item_id>')
def delete_product(item_id):
    conn = get_db()
    item = conn.execute("SELECT image_path FROM products WHERE id = ?", (item_id,)).fetchone()
    if item and item['image_path'] and os.path.exists(item['image_path']):
        try:
            os.remove(item['image_path'])
        except:
            pass
    conn.execute("DELETE FROM products WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
