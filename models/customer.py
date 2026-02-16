#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج الزبون
Customer Model
"""

import sqlite3
from datetime import datetime

class Customer:
    """نموذج بيانات الزبون"""
    
    def __init__(self, db_path='aldhaferya_store.db'):
        self.db_path = db_path
    
    def add_customer(self, name, phone=None, address=None, notes=None, credit_limit=0):
        """إضافة زبون جديد"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO customers (name, phone, address, notes, credit_limit)
                VALUES (?, ?, ?, ?, ?)
            """, (name, phone, address, notes, credit_limit))
            
            conn.commit()
            customer_id = cursor.lastrowid
            return True, customer_id, f"تم إضافة الزبون '{name}' بنجاح"
            
        except sqlite3.IntegrityError:
            return False, None, f"رقم التليفون '{phone}' موجود مسبقاً"
        except Exception as e:
            return False, None, f"خطأ: {str(e)}"
        finally:
            conn.close()
    
    def get_customer(self, customer_id):
        """الحصول على بيانات زبون"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM customers WHERE customer_id = ?
        """, (customer_id,))
        
        customer = cursor.fetchone()
        conn.close()
        
        return dict(customer) if customer else None
    
    def get_all_customers(self):
        """الحصول على جميع الزبائن"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, 
                   COALESCE(SUM(ci.remaining_amount), 0) as total_debt,
                   COUNT(ci.invoice_id) as invoice_count
            FROM customers c
            LEFT JOIN credit_invoices ci ON c.customer_id = ci.customer_id 
                AND ci.status != 'paid'
            GROUP BY c.customer_id
            ORDER BY total_debt DESC
        """)
        
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return customers
    
    def search_customers(self, search_term):
        """البحث عن زبائن"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, 
                   COALESCE(SUM(ci.remaining_amount), 0) as total_debt
            FROM customers c
            LEFT JOIN credit_invoices ci ON c.customer_id = ci.customer_id 
                AND ci.status != 'paid'
            WHERE c.name LIKE ? OR c.phone LIKE ?
            GROUP BY c.customer_id
            ORDER BY c.name
        """, (f'%{search_term}%', f'%{search_term}%'))
        
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return customers
    
    def update_customer(self, customer_id, name=None, phone=None, 
                       address=None, notes=None, credit_limit=None, status=None):
        """تحديث بيانات زبون"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if phone:
            updates.append("phone = ?")
            params.append(phone)
        if address:
            updates.append("address = ?")
            params.append(address)
        if notes:
            updates.append("notes = ?")
            params.append(notes)
        if credit_limit is not None:
            updates.append("credit_limit = ?")
            params.append(credit_limit)
        if status:
            updates.append("status = ?")
            params.append(status)
        
        if not updates:
            return False, "لا توجد تحديثات"
        
        params.append(customer_id)
        query = f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = ?"
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return True, "تم التحديث بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
        finally:
            conn.close()
    
    def delete_customer(self, customer_id):
        """حذف زبون"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # التحقق من وجود ديون
        cursor.execute("""
            SELECT COUNT(*) FROM credit_invoices 
            WHERE customer_id = ? AND status != 'paid'
        """, (customer_id,))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False, "لا يمكن حذف زبون لديه ديون مستحقة"
        
        try:
            cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
            conn.commit()
            return True, "تم حذف الزبون بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
        finally:
            conn.close()
    
    def get_customer_stats(self, customer_id):
        """إحصائيات الزبون"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # إجمالي الديون
        cursor.execute("""
            SELECT COALESCE(SUM(remaining_amount), 0)
            FROM credit_invoices
            WHERE customer_id = ? AND status != 'paid'
        """, (customer_id,))
        total_debt = cursor.fetchone()[0]
        
        # عدد الفواتير المستحقة
        cursor.execute("""
            SELECT COUNT(*)
            FROM credit_invoices
            WHERE customer_id = ? AND status != 'paid'
        """, (customer_id,))
        pending_invoices = cursor.fetchone()[0]
        
        # إجمالي المدفوعات
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM payments
            WHERE customer_id = ?
        """, (customer_id,))
        total_payments = cursor.fetchone()[0]
        
        # أقدم دين
        cursor.execute("""
            SELECT MIN(invoice_date)
            FROM credit_invoices
            WHERE customer_id = ? AND status != 'paid'
        """, (customer_id,))
        oldest_debt = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_debt': total_debt,
            'pending_invoices': pending_invoices,
            'total_payments': total_payments,
            'oldest_debt': oldest_debt
        }
