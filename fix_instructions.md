# تعليمات إصلاح ملف main.py

## المشكلة
ملف main.py الحالي ناقص بعض الدوال الأساسية

## الحل:

أنسخ الملف الكامل من commit رقم: `04a888a3049f56cbb64465592c74bc16320d128b`

ثم أضف فقط التعديلات التالية:

### 1. إضافة import في أعلى الملف (بعد matplotlib imports)
```python
# ✅ CREDIT SYSTEM IMPORT
from views.credit_view import CreditManagementView
```

### 2. في Database class بعد `__init__`
أضف السطر:
```python
# ✅ INITIALIZE CREDIT SYSTEM
self.init_credit_system()
```

### 3. في Database class بعد `init_db`
أضف الدالة:
```python
def init_credit_system(self):
    """✅ INITIALIZE CREDIT SYSTEM TABLES"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE,
            address TEXT,
            notes TEXT,
            status TEXT DEFAULT 'normal' CHECK(status IN ('normal', 'reliable', 'late')),
            credit_limit REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            invoice_number TEXT UNIQUE NOT NULL,
            total_amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            remaining_amount REAL NOT NULL,
            invoice_date DATE DEFAULT (date('now')),
            due_date DATE,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'partial', 'paid', 'overdue')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_code TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES credit_invoices(invoice_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            invoice_id INTEGER,
            amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'cash' CHECK(payment_method IN ('cash', 'vodafone_cash', 'instapay', 'bank_transfer')),
            payment_date DATE DEFAULT (date('now')),
            received_by TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (invoice_id) REFERENCES credit_invoices(invoice_id)
        )
    """)

    conn.commit()
    conn.close()
```

### 4. في MainWindow class بعد create_reports_tab
أضف:
```python
def create_credit_tab(self):
    """✅ CREATE CREDIT SYSTEM TAB"""
    return CreditManagementView(self.db.db_path, self)
```

### 5. في init_ui method بعد إضافة تاب التقارير
أضف:
```python
# ✅ ADD CREDIT SYSTEM TAB
self.tabs.addTab(self.create_credit_tab(), '💰 الديون')
```

## بعد الإصلاح
احفظ الملف وارفعه على GitHub
