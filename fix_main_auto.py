#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إصلاح تلقائي لـ main.py
Automatic Fix Script for main.py - Credit System Integration
"""

import os
import sys

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
    
    # إجراء التعديلات
    lines = content.split('\n')
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 1. إضافة import بعد matplotlib imports
        if 'import matplotlib.font_manager as fm' in line:
            new_lines.append(line)
            new_lines.append('')
            new_lines.append('# ✅ CREDIT SYSTEM IMPORT')
            new_lines.append('from views.credit_view import CreditManagementView')
            print("✅ [1/5] أضفت import CreditManagementView")
            i += 1
            continue
        
        # 2. إضافة init_credit_system() في __init__
        if 'self.init_db()' in line and 'Database' in ''.join(lines[max(0, i-10):i]):
            new_lines.append(line)
            new_lines.append('        # ✅ INITIALIZE CREDIT SYSTEM')
            new_lines.append('        self.init_credit_system()')
            print("✅ [2/5] أضفت init_credit_system() call")
            i += 1
            continue
        
        # 3. إضافة دالة init_credit_system بعد init_db
        if 'conn.commit()' in line and 'conn.close()' in lines[i+1] and 'class Database' in ''.join(lines[max(0, i-100):i]):
            new_lines.append(line)
            if i+1 < len(lines):
                new_lines.append(lines[i+1])  # conn.close()
            
            # إضافة الدالة الجديدة
            new_lines.append('')
            new_lines.append('    def init_credit_system(self):')
            new_lines.append('        """✅ تهيئة جداول نظام الديون"""')
            new_lines.append('        conn = sqlite3.connect(self.db_path)')
            new_lines.append('        cursor = conn.cursor()')
            new_lines.append('')
            new_lines.append('        cursor.execute("""')
            new_lines.append('            CREATE TABLE IF NOT EXISTS customers (')
            new_lines.append('                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,')
            new_lines.append('                name TEXT NOT NULL,')
            new_lines.append('                phone TEXT UNIQUE,')
            new_lines.append('                address TEXT,')
            new_lines.append('                notes TEXT,')
            new_lines.append('                status TEXT DEFAULT \'normal\' CHECK(status IN (\'normal\', \'reliable\', \'late\')),')
            new_lines.append('                credit_limit REAL DEFAULT 0,')
            new_lines.append('                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            new_lines.append('            )')
            new_lines.append('        """)')
            new_lines.append('')
            new_lines.append('        cursor.execute("""')
            new_lines.append('            CREATE TABLE IF NOT EXISTS credit_invoices (')
            new_lines.append('                invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,')
            new_lines.append('                customer_id INTEGER NOT NULL,')
            new_lines.append('                invoice_number TEXT UNIQUE NOT NULL,')
            new_lines.append('                total_amount REAL NOT NULL,')
            new_lines.append('                paid_amount REAL DEFAULT 0,')
            new_lines.append('                remaining_amount REAL NOT NULL,')
            new_lines.append('                invoice_date DATE DEFAULT (date(\'now\')),')
            new_lines.append('                due_date DATE,')
            new_lines.append('                status TEXT DEFAULT \'pending\' CHECK(status IN (\'pending\', \'partial\', \'paid\', \'overdue\')),')
            new_lines.append('                notes TEXT,')
            new_lines.append('                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,')
            new_lines.append('                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)')
            new_lines.append('            )')
            new_lines.append('        """)')
            new_lines.append('')
            new_lines.append('        cursor.execute("""')
            new_lines.append('            CREATE TABLE IF NOT EXISTS invoice_items (')
            new_lines.append('                item_id INTEGER PRIMARY KEY AUTOINCREMENT,')
            new_lines.append('                invoice_id INTEGER NOT NULL,')
            new_lines.append('                product_code TEXT NOT NULL,')
            new_lines.append('                product_name TEXT NOT NULL,')
            new_lines.append('                quantity INTEGER NOT NULL,')
            new_lines.append('                unit_price REAL NOT NULL,')
            new_lines.append('                total_price REAL NOT NULL,')
            new_lines.append('                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,')
            new_lines.append('                FOREIGN KEY (invoice_id) REFERENCES credit_invoices(invoice_id)')
            new_lines.append('            )')
            new_lines.append('        """)')
            new_lines.append('')
            new_lines.append('        cursor.execute("""')
            new_lines.append('            CREATE TABLE IF NOT EXISTS payments (')
            new_lines.append('                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,')
            new_lines.append('                customer_id INTEGER NOT NULL,')
            new_lines.append('                invoice_id INTEGER,')
            new_lines.append('                amount REAL NOT NULL,')
            new_lines.append('                payment_method TEXT DEFAULT \'cash\' CHECK(payment_method IN (\'cash\', \'vodafone_cash\', \'instapay\', \'bank_transfer\')),')
            new_lines.append('                payment_date DATE DEFAULT (date(\'now\')),')
            new_lines.append('                received_by TEXT,')
            new_lines.append('                notes TEXT,')
            new_lines.append('                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,')
            new_lines.append('                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),')
            new_lines.append('                FOREIGN KEY (invoice_id) REFERENCES credit_invoices(invoice_id)')
            new_lines.append('            )')
            new_lines.append('        """)')
            new_lines.append('')
            new_lines.append('        conn.commit()')
            new_lines.append('        conn.close()')
            
            print("✅ [3/5] أضفت دالة init_credit_system()")
            i += 2  # نتخطى conn.close() لأنه أضيف بالفعل
            continue
        
        # 4. إضافة create_credit_tab قبل def load_data
        if line.strip().startswith('def load_data(self):') and 'MainWindow' in ''.join(lines[max(0, i-200):i]):
            new_lines.append('    def create_credit_tab(self):')
            new_lines.append('        """✅ إنشاء تاب نظام الديون"""')
            new_lines.append('        return CreditManagementView(self.db.db_path, self)')
            new_lines.append('')
            new_lines.append(line)
            print("✅ [4/5] أضفت create_credit_tab()")
            i += 1
            continue
        
        # 5. إضافة التاب في init_ui
        if "self.tabs.addTab(self.create_reports_tab(), '📈 التقارير')" in line:
            new_lines.append(line)
            new_lines.append("        # ✅ إضافة تاب نظام الديون")
            new_lines.append("        self.tabs.addTab(self.create_credit_tab(), '💰 الديون')")
            print("✅ [5/5] أضفت credit tab لـ tabs")
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    # حفظ الملف الجديد
    new_content = '\n'.join(new_lines)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
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
