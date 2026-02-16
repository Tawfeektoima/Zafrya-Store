#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام قاعدة بيانات الديون
Credit System Database
"""

import sqlite3
from datetime import datetime

class CreditDatabase:
    """إدارة قاعدة بيانات نظام الديون"""
    
    def __init__(self, db_path='aldhaferya_store.db'):
        self.db_path = db_path
        self.init_credit_tables()
    
    def init_credit_tables(self):
        """إنشاء جداول نظام الديون"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول الزبائن
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE,
                address TEXT,
                notes TEXT,
                status TEXT DEFAULT 'normal',
                credit_limit REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول الفواتير الآجلة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_invoices (
                invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                invoice_number TEXT UNIQUE NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                remaining_amount REAL NOT NULL,
                invoice_date DATE NOT NULL,
                due_date DATE,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        
        # جدول تفاصيل المشتريات في كل فاتورة
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
        
        # جدول الدفعات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                invoice_id INTEGER,
                amount REAL NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                payment_date DATE NOT NULL,
                received_by TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (invoice_id) REFERENCES credit_invoices(invoice_id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ تم إنشاء جداول نظام الديون بنجاح")

if __name__ == "__main__":
    # للاختبار
    db = CreditDatabase()
    print("تم تهيئة قاعدة البيانات")
