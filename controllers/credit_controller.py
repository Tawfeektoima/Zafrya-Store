#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
متحكم نظام الديون
Credit Controller
"""

from models.customer import Customer
from models.credit_invoice import CreditInvoice

class CreditController:
    """متحكم منطق نظام الديون"""
    
    def __init__(self, db_path='aldhaferya_store.db'):
        self.db_path = db_path
        self.customer_model = Customer(db_path)
        self.invoice_model = CreditInvoice(db_path)
    
    # ============ إدارة الزبائن ============
    
    def add_customer(self, name, phone=None, address=None, notes=None, credit_limit=0):
        """إضافة زبون جديد"""
        return self.customer_model.add_customer(name, phone, address, notes, credit_limit)
    
    def get_all_customers(self):
        """الحصول على جميع الزبائن"""
        return self.customer_model.get_all_customers()
    
    def search_customers(self, search_term):
        """البحث عن زبائن"""
        return self.customer_model.search_customers(search_term)
    
    def get_customer_details(self, customer_id):
        """الحصول على تفاصيل زبون مع فواتيره وإحصائياته"""
        customer = self.customer_model.get_customer(customer_id)
        if not customer:
            return None
        
        # إضافة الفواتير
        customer['invoices'] = self.invoice_model.get_customer_invoices(customer_id)
        
        # إضافة الإحصائيات
        customer['stats'] = self.customer_model.get_customer_stats(customer_id)
        
        return customer
    
    def update_customer(self, customer_id, **kwargs):
        """تحديث بيانات زبون"""
        return self.customer_model.update_customer(customer_id, **kwargs)
    
    def delete_customer(self, customer_id):
        """حذف زبون"""
        return self.customer_model.delete_customer(customer_id)
    
    # ============ إدارة الفواتير ============
    
    def create_credit_sale(self, customer_id, items, due_date=None, notes=None):
        """إنشاء فاتورة آجلة"""
        return self.invoice_model.create_invoice(customer_id, items, due_date, notes)
    
    def get_invoice_details(self, invoice_id):
        """الحصول على تفاصيل فاتورة"""
        return self.invoice_model.get_invoice(invoice_id)
    
    def get_overdue_invoices(self):
        """الحصول على الفواتير المتأخرة"""
        return self.invoice_model.get_overdue_invoices()
    
    # ============ إدارة الدفعات ============
    
    def add_payment(self, customer_id, invoice_id, amount, payment_method='cash',
                   received_by=None, notes=None):
        """تسجيل دفعة"""
        return self.invoice_model.add_payment(
            customer_id, invoice_id, amount, payment_method, 
            received_by, notes
        )
    
    # ============ إحصائيات ============
    
    def get_dashboard_stats(self):
        """إحصائيات اللوحة الرئيسية"""
        return self.invoice_model.get_all_stats()
