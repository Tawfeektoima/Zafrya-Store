#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج الفاتورة الآجلة
Credit Invoice Model
"""

import sqlite3
from datetime import datetime, timedelta

class CreditInvoice:
    """نموذج بيانات الفاتورة الآجلة"""
    
    def __init__(self, db_path='aldhaferya_store.db'):
        self.db_path = db_path
    
    def generate_invoice_number(self):
        """توليد رقم فاتورة تلقائي"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # الحصول على آخر رقم
        cursor.execute("""
            SELECT invoice_number FROM credit_invoices 
            ORDER BY invoice_id DESC LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # استخراج الرقم من النمط INV-2026-001
            try:
                last_num = int(result[0].split('-')[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        year = datetime.now().year
        return f"INV-{year}-{new_num:03d}"
    
    def create_invoice(self, customer_id, items, due_date=None, notes=None):
        """
        إنشاء فاتورة آجلة جديدة
        items: list of dict [{'code': 'ش42DC', 'name': '...', 'qty': 2, 'price': 150}, ...]
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # حساب الإجمالي
            total = sum(item['qty'] * item['price'] for item in items)
            
            # توليد رقم الفاتورة
            invoice_number = self.generate_invoice_number()
            
            # موعد السداد الافتراضي (شهر من الآن)
            if not due_date:
                due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            # إنشاء الفاتورة
            cursor.execute("""
                INSERT INTO credit_invoices 
                (customer_id, invoice_number, total_amount, remaining_amount, 
                 invoice_date, due_date, notes)
                VALUES (?, ?, ?, ?, date('now'), ?, ?)
            """, (customer_id, invoice_number, total, total, due_date, notes))
            
            invoice_id = cursor.lastrowid
            
            # إضافة المشتريات
            for item in items:
                cursor.execute("""
                    INSERT INTO invoice_items 
                    (invoice_id, product_code, product_name, quantity, 
                     unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice_id, item['code'], item['name'], item['qty'],
                      item['price'], item['qty'] * item['price']))
            
            # تحديث المخزون
            for item in items:
                cursor.execute("""
                    UPDATE products 
                    SET current_stock = current_stock - ? 
                    WHERE product_code = ?
                """, (item['qty'], item['code']))
            
            conn.commit()
            return True, invoice_id, invoice_number, "تم إنشاء الفاتورة بنجاح"
            
        except Exception as e:
            conn.rollback()
            return False, None, None, f"خطأ: {str(e)}"
        finally:
            conn.close()
    
    def get_invoice(self, invoice_id):
        """الحصول على تفاصيل فاتورة"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # معلومات الفاتورة
        cursor.execute("""
            SELECT ci.*, c.name as customer_name, c.phone as customer_phone
            FROM credit_invoices ci
            JOIN customers c ON ci.customer_id = c.customer_id
            WHERE ci.invoice_id = ?
        """, (invoice_id,))
        invoice = cursor.fetchone()
        
        if not invoice:
            conn.close()
            return None
        
        invoice = dict(invoice)
        
        # المشتريات
        cursor.execute("""
            SELECT * FROM invoice_items WHERE invoice_id = ?
        """, (invoice_id,))
        invoice['items'] = [dict(row) for row in cursor.fetchall()]
        
        # الدفعات
        cursor.execute("""
            SELECT * FROM payments 
            WHERE invoice_id = ?
            ORDER BY payment_date DESC
        """, (invoice_id,))
        invoice['payments'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return invoice
    
    def get_customer_invoices(self, customer_id):
        """الحصول على فواتير زبون"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM credit_invoices
            WHERE customer_id = ?
            ORDER BY invoice_date DESC
        """, (customer_id,))
        
        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return invoices
    
    def get_overdue_invoices(self):
        """الحصول على الفواتير المتأخرة"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ci.*, c.name as customer_name, c.phone as customer_phone,
                   julianday('now') - julianday(ci.due_date) as days_overdue
            FROM credit_invoices ci
            JOIN customers c ON ci.customer_id = c.customer_id
            WHERE ci.status != 'paid' AND ci.due_date < date('now')
            ORDER BY days_overdue DESC
        """)
        
        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return invoices
    
    def add_payment(self, customer_id, invoice_id, amount, payment_method='cash', 
                   received_by=None, notes=None):
        """تسجيل دفعة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # التحقق من المبلغ المتبقي
            cursor.execute("""
                SELECT remaining_amount FROM credit_invoices 
                WHERE invoice_id = ?
            """, (invoice_id,))
            
            result = cursor.fetchone()
            if not result:
                return False, "الفاتورة غير موجودة"
            
            remaining = result[0]
            
            if amount > remaining:
                return False, f"المبلغ أكبر من المتبقي ({remaining:.2f} ج)"
            
            # تسجيل الدفعة
            cursor.execute("""
                INSERT INTO payments 
                (customer_id, invoice_id, amount, payment_method, 
                 payment_date, received_by, notes)
                VALUES (?, ?, ?, ?, date('now'), ?, ?)
            """, (customer_id, invoice_id, amount, payment_method, received_by, notes))
            
            # تحديث الفاتورة
            new_remaining = remaining - amount
            new_status = 'paid' if new_remaining == 0 else 'partial'
            
            cursor.execute("""
                UPDATE credit_invoices
                SET paid_amount = paid_amount + ?,
                    remaining_amount = ?,
                    status = ?
                WHERE invoice_id = ?
            """, (amount, new_remaining, new_status, invoice_id))
            
            conn.commit()
            return True, "تم تسجيل الدفعة بنجاح"
            
        except Exception as e:
            conn.rollback()
            return False, f"خطأ: {str(e)}"
        finally:
            conn.close()
    
    def get_all_stats(self):
        """إحصائيات عامة عن الديون"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # إجمالي الديون
        cursor.execute("""
            SELECT COALESCE(SUM(remaining_amount), 0)
            FROM credit_invoices
            WHERE status != 'paid'
        """)
        total_debt = cursor.fetchone()[0]
        
        # عدد الزبائن المديونين
        cursor.execute("""
            SELECT COUNT(DISTINCT customer_id)
            FROM credit_invoices
            WHERE status != 'paid'
        """)
        debtors_count = cursor.fetchone()[0]
        
        # ديون متأخرة (+30 يوم)
        cursor.execute("""
            SELECT COALESCE(SUM(remaining_amount), 0)
            FROM credit_invoices
            WHERE status != 'paid' 
              AND julianday('now') - julianday(due_date) > 30
        """)
        overdue_30 = cursor.fetchone()[0]
        
        # ديون حرجة (+60 يوم)
        cursor.execute("""
            SELECT COALESCE(SUM(remaining_amount), 0)
            FROM credit_invoices
            WHERE status != 'paid' 
              AND julianday('now') - julianday(due_date) > 60
        """)
        overdue_60 = cursor.fetchone()[0]
        
        # أكبر دين
        cursor.execute("""
            SELECT COALESCE(MAX(remaining_amount), 0)
            FROM credit_invoices
            WHERE status != 'paid'
        """)
        max_debt = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_debt': total_debt,
            'debtors_count': debtors_count,
            'avg_debt': total_debt / debtors_count if debtors_count > 0 else 0,
            'overdue_30': overdue_30,
            'overdue_60': overdue_60,
            'max_debt': max_debt
        }
