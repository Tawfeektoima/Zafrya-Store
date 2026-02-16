#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج الدفعات
Payment Model
"""

import sqlite3
from datetime import datetime

class Payment:
    """نموذج بيانات الدفعات"""
    
    def __init__(self, db_path='aldhaferya_store.db'):
        self.db_path = db_path
    
    def add_payment(self, customer_id, invoice_id, amount, payment_method='cash',
                   received_by=None, notes=None):
        """إضافة دفعة جديدة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # التحقق من الفاتورة والمبلغ المتبقي
            cursor.execute("""
                SELECT remaining_amount, invoice_number 
                FROM credit_invoices 
                WHERE invoice_id = ?
            """, (invoice_id,))
            
            result = cursor.fetchone()
            if not result:
                return False, None, "الفاتورة غير موجودة"
            
            remaining, invoice_number = result
            
            if amount <= 0:
                return False, None, "المبلغ يجب أن يكون أكبر من صفر"
            
            if amount > remaining:
                return False, None, f"المبلغ أكبر من المتبقي ({remaining:.2f} ج)"
            
            # إضافة الدفعة
            cursor.execute("""
                INSERT INTO payments 
                (customer_id, invoice_id, amount, payment_method, 
                 payment_date, received_by, notes)
                VALUES (?, ?, ?, ?, date('now'), ?, ?)
            """, (customer_id, invoice_id, amount, payment_method, received_by, notes))
            
            payment_id = cursor.lastrowid
            
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
            
            message = f"تم تسجيل دفعة {amount:.2f} ج على الفاتورة {invoice_number}"
            if new_remaining == 0:
                message += "\n✅ تم سداد الفاتورة بالكامل!"
            
            return True, payment_id, message
            
        except Exception as e:
            conn.rollback()
            return False, None, f"خطأ: {str(e)}"
        finally:
            conn.close()
    
    def get_payment(self, payment_id):
        """الحصول على تفاصيل دفعة"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, 
                   c.name as customer_name,
                   ci.invoice_number
            FROM payments p
            JOIN customers c ON p.customer_id = c.customer_id
            LEFT JOIN credit_invoices ci ON p.invoice_id = ci.invoice_id
            WHERE p.payment_id = ?
        """, (payment_id,))
        
        payment = cursor.fetchone()
        conn.close()
        
        return dict(payment) if payment else None
    
    def get_customer_payments(self, customer_id, limit=None):
        """الحصول على دفعات زبون"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT p.*, ci.invoice_number
            FROM payments p
            LEFT JOIN credit_invoices ci ON p.invoice_id = ci.invoice_id
            WHERE p.customer_id = ?
            ORDER BY p.payment_date DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (customer_id,))
        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return payments
    
    def get_invoice_payments(self, invoice_id):
        """الحصول على دفعات فاتورة محددة"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, c.name as customer_name
            FROM payments p
            JOIN customers c ON p.customer_id = c.customer_id
            WHERE p.invoice_id = ?
            ORDER BY p.payment_date DESC
        """, (invoice_id,))
        
        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return payments
    
    def get_payments_by_date(self, start_date, end_date=None):
        """الحصول على الدفعات خلال فترة معينة"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if end_date:
            cursor.execute("""
                SELECT p.*, 
                       c.name as customer_name,
                       ci.invoice_number
                FROM payments p
                JOIN customers c ON p.customer_id = c.customer_id
                LEFT JOIN credit_invoices ci ON p.invoice_id = ci.invoice_id
                WHERE p.payment_date BETWEEN ? AND ?
                ORDER BY p.payment_date DESC
            """, (start_date, end_date))
        else:
            cursor.execute("""
                SELECT p.*, 
                       c.name as customer_name,
                       ci.invoice_number
                FROM payments p
                JOIN customers c ON p.customer_id = c.customer_id
                LEFT JOIN credit_invoices ci ON p.invoice_id = ci.invoice_id
                WHERE p.payment_date = ?
                ORDER BY p.payment_date DESC
            """, (start_date,))
        
        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return payments
    
    def get_daily_payments_summary(self, date=None):
        """ملخص الدفعات اليومية"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # إجمالي الدفعات
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0), COUNT(*)
            FROM payments
            WHERE payment_date = ?
        """, (date,))
        total, count = cursor.fetchone()
        
        # حسب طريقة الدفع
        cursor.execute("""
            SELECT payment_method, COALESCE(SUM(amount), 0), COUNT(*)
            FROM payments
            WHERE payment_date = ?
            GROUP BY payment_method
        """, (date,))
        by_method = {row[0]: {'amount': row[1], 'count': row[2]} 
                    for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'date': date,
            'total_amount': total,
            'total_count': count,
            'by_method': by_method
        }
    
    def delete_payment(self, payment_id):
        """حذف دفعة (استخدام حذر)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # الحصول على بيانات الدفعة
            cursor.execute("""
                SELECT invoice_id, amount FROM payments WHERE payment_id = ?
            """, (payment_id,))
            
            result = cursor.fetchone()
            if not result:
                return False, "الدفعة غير موجودة"
            
            invoice_id, amount = result
            
            # حذف الدفعة
            cursor.execute("DELETE FROM payments WHERE payment_id = ?", (payment_id,))
            
            # تحديث الفاتورة
            if invoice_id:
                cursor.execute("""
                    UPDATE credit_invoices
                    SET paid_amount = paid_amount - ?,
                        remaining_amount = remaining_amount + ?,
                        status = CASE 
                            WHEN paid_amount - ? = 0 THEN 'pending'
                            ELSE 'partial'
                        END
                    WHERE invoice_id = ?
                """, (amount, amount, amount, invoice_id))
            
            conn.commit()
            return True, "تم حذف الدفعة وتحديث الفاتورة"
            
        except Exception as e:
            conn.rollback()
            return False, f"خطأ: {str(e)}"
        finally:
            conn.close()
    
    def get_payment_stats(self):
        """إحصائيات عامة للدفعات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # إجمالي الدفعات
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0), COUNT(*)
            FROM payments
        """)
        total, count = cursor.fetchone()
        
        # دفعات اليوم
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0), COUNT(*)
            FROM payments
            WHERE payment_date = date('now')
        """)
        today_total, today_count = cursor.fetchone()
        
        # دفعات الشهر
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0), COUNT(*)
            FROM payments
            WHERE strftime('%Y-%m', payment_date) = strftime('%Y-%m', 'now')
        """)
        month_total, month_count = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_amount': total,
            'total_count': count,
            'today_amount': today_total,
            'today_count': today_count,
            'month_amount': month_total,
            'month_count': month_count,
            'avg_payment': total / count if count > 0 else 0
        }
