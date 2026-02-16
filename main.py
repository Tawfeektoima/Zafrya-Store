#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة محل الظافرية - النسخة المحدثة مع نظام الديون
AlDhaferya Store Management System - Updated Version with Credit System
"""

import sys
import sqlite3
import hashlib
import smtplib
import random
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox, QTabWidget,
    QGroupBox, QFormLayout, QDialog, QDialogButtonBox, QHeaderView,
    QTextEdit, QDateEdit, QCompleter, QInputDialog, QScrollArea, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtGui import QFont, QColor

# Matplotlib imports
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.font_manager as fm

# ✅ CREDIT SYSTEM IMPORT
from views.credit_view import CreditManagementView

class Database:
    """إدارة قاعدة البيانات"""
    def __init__(self, db_path='aldhaferya_store.db'):
        self.db_path = db_path
        self.init_db()
        # ✅ INITIALIZE CREDIT SYSTEM
        self.init_credit_system()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                size TEXT,
                manufacturer TEXT,
                purchase_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                current_stock INTEGER DEFAULT 0,
                min_stock_alert INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                total_profit REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_code TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                purchase_price REAL NOT NULL,
                subtotal REAL NOT NULL,
                item_profit REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
        """)

        cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'analytics_password'")
        if cursor.fetchone() is None:
            default_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute("INSERT INTO system_settings VALUES ('analytics_password', ?)", (default_password,))

        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ('ش42DC', 'شبشب DC مقاس 42', 'شباشب', '42', 'DC', 80.0, 120.0, 25),
                ('ش40AB', 'شبشب Adidas مقاس 40', 'شباشب', '40', 'Adidas', 100.0, 150.0, 15),
                ('ش38DC', 'شبشب DC مقاس 38', 'شباشب', '38', 'DC', 75.0, 115.0, 30),
                ('د38A4', 'دفتر A4 38 ورقة', 'أدوات مدرسية', '', 'مصر', 15.0, 25.0, 50),
                ('د50A5', 'دفتر A5 50 ورقة', 'أدوات مدرسية', '', 'مصر', 18.0, 30.0, 40),
                ('ق40SB', 'قميص رجالي مقاس 40', 'ملابس', '40', 'LC', 150.0, 220.0, 10),
            ]
            cursor.executemany("""
                INSERT INTO products (product_code, product_name, category, size, 
                                    manufacturer, purchase_price, selling_price, current_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_products)

        conn.commit()
        conn.close()

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

class AnalyticsProfitDialog(QDialog):