#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إصلاح تلقائي لـ main.py
Automatic Fix Script for main.py - Credit System Integration
"""

import os
import sys
import re

def fix_main_py():
    print("🔧 بدء إصلاح main.py...")
    
    # قراءة الملف الحالي
    if not os.path.exists('main.py'):
        print("❌ لم يتم العثور على main.py")
        return False
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("✅ تم قراءة الملف")
    
    # التحقق إذا كانت التعديلات موجودة بالفعل
    if 'from views.credit_view import CreditManagementView' in content:
        print("✅ التعديلات موجودة بالفعل!")
        return True
    
    # نسخة احتياطية
    with open('main.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    print("💾 تم إنشاء نسخة احتياطية: main.py.backup")
    
    # 1. إضافة import بعد matplotlib
    pattern1 = r'(import matplotlib\.font_manager as fm)'
    replacement1 = r'\1\n\n# ✅ CREDIT SYSTEM IMPORT\nfrom views.credit_view import CreditManagementView'
    content = re.sub(pattern1, replacement1, content)
    print("✅ [1/5] أضفت import CreditManagementView")
    
    # 2. إضافة init_credit_system() في __init__ بعد self.init_db()
    pattern2 = r'(class Database:[\s\S]*?def __init__[\s\S]*?self\.init_db\(\))'
    def add_init_credit(match):
        return match.group(1) + '\n        # ✅ INITIALIZE CREDIT SYSTEM\n        self.init_credit_system()'
    content = re.sub(pattern2, add_init_credit, content)
    print("✅ [2/5] أضفت init_credit_system() call")
    
    # 3. إضافة دالة init_credit_system بعد init_db
    init_credit_method = '''

    def init_credit_system(self):
        """✅ تهيئة جداول نظام الديون"""
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
'''
    
    # البحث عن نهاية دالة init_db في class Database
    pattern3 = r'(class Database:[\s\S]*?def init_db\(self\):[\s\S]*?conn\.close\(\))'
    def add_init_credit_method(match):
        return match.group(1) + init_credit_method
    content = re.sub(pattern3, add_init_credit_method, content)
    print("✅ [3/5] أضفت دالة init_credit_system()")
    
    # 4. إضافة create_credit_tab قبل def load_data في MainWindow
    create_credit_tab_method = '''    def create_credit_tab(self):
        """✅ إنشاء تاب نظام الديون"""
        return CreditManagementView(self.db.db_path, self)

'''
    
    pattern4 = r'(class MainWindow[\s\S]*?)(    def load_data\(self\):)'
    def add_create_credit_tab(match):
        return match.group(1) + create_credit_tab_method + match.group(2)
    content = re.sub(pattern4, add_create_credit_tab, content)
    print("✅ [4/5] أضفت create_credit_tab()")
    
    # 5. إضافة التاب في init_ui
    pattern5 = r"(self\.tabs\.addTab\(self\.create_reports_tab\(\), '📈 التقارير'\))"
    replacement5 = r"\1\n        # ✅ إضافة تاب نظام الديون\n        self.tabs.addTab(self.create_credit_tab(), '💰 الديون')"
    content = re.sub(pattern5, replacement5, content)
    print("✅ [5/5] أضفت credit tab لـ tabs")
    
    # حفظ الملف الجديد
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✨ تم إصلاح الملف بنجاح!")
    print("💾 النسخة الاحتياطية: main.py.backup")
    print("\n🎉 يمكنك الآن تشغيل البرنامج:")
    print("   python main.py")
    
    return True

if __name__ == '__main__':
    print("="*60)
    print("🔧 Zafrya Store - Credit System Integration Fix")
    print("="*60)
    print()
    
    if fix_main_py():
        print("\n✅ الإصلاح نجح!")
        sys.exit(0)
    else:
        print("\n❌ فشل الإصلاح")
        sys.exit(1)
