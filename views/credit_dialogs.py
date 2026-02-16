#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نوافذ تفصيلية لنظام الديون
Credit Dialogs
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox,
    QFormLayout, QDialogButtonBox, QTextEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDateEdit, QGroupBox,
    QHeaderView, QAbstractItemView, QListWidget
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from controllers.credit_controller import CreditController
import sqlite3
from datetime import datetime, timedelta
import traceback  # ✅ للتعامل مع الأخطاء

class CustomerDetailsDialog(QDialog):
    """نافذة تفاصيل زبون"""
    
    def __init__(self, customer_id, db_path, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.db_path = db_path
        self.controller = CreditController(db_path)
        
        self.setWindowTitle('تفاصيل الزبون')
        self.setModal(True)
        self.setMinimumSize(900, 700)
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # معلومات الزبون
        self.info_group = QGroupBox('👤 معلومات الزبون')
        self.info_layout = QFormLayout()
        self.info_group.setLayout(self.info_layout)
        layout.addWidget(self.info_group)
        
        # إحصائيات
        self.stats_layout = QHBoxLayout()
        layout.addLayout(self.stats_layout)
        
        # جدول الفواتير
        invoices_label = QLabel('🧾 الفواتير المستحقة')
        invoices_label.setFont(QFont('Arial', 12, QFont.Bold))
        layout.addWidget(invoices_label)
        
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(6)
        self.invoices_table.setHorizontalHeaderLabels([
            'رقم الفاتورة', 'التاريخ', 'الإجمالي', 'المدفوع', 'المتبقي', 'إجراء'
        ])
        self.invoices_table.horizontalHeader().setStretchLastSection(True)
        self.invoices_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.invoices_table)
        
        # أزرار
        btn_layout = QHBoxLayout()
        
        payment_btn = QPushButton('💰 تسجيل دفعة')
        payment_btn.clicked.connect(self.add_payment_dialog)
        payment_btn.setStyleSheet("background: #27ae60; color: white; padding: 10px; font-size: 14px;")
        btn_layout.addWidget(payment_btn)
        
        close_btn = QPushButton('إغلاق')
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background: #e74c3c; color: white; padding: 10px;")
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        customer = self.controller.get_customer_details(self.customer_id)
        
        if not customer:
            QMessageBox.warning(self, 'خطأ', 'لم يتم العثور على الزبون!')
            self.reject()
            return
        
        # معلومات الزبون
        self.info_layout.addRow('الاسم:', QLabel(f"<b>{customer['name']}</b>"))
        self.info_layout.addRow('التليفون:', QLabel(customer['phone'] or '-'))
        self.info_layout.addRow('العنوان:', QLabel(customer['address'] or '-'))
        
        # إحصائيات
        stats = customer['stats']
        
        self.stats_layout.addWidget(self.create_stat_card(
            'إجمالي الديون', f"{stats['total_debt']:.2f} ج", '#e74c3c'
        ))
        self.stats_layout.addWidget(self.create_stat_card(
            'عدد الفواتير', str(stats['pending_invoices']), '#3498db'
        ))
        self.stats_layout.addWidget(self.create_stat_card(
            'إجمالي المدفوع', f"{stats['total_payments']:.2f} ج", '#27ae60'
        ))
        
        # الفواتير
        for invoice in customer['invoices']:
            if invoice['status'] == 'paid':
                continue  # نتجاهل المدفوع بالكامل
                
            row = self.invoices_table.rowCount()
            self.invoices_table.insertRow(row)
            
            self.invoices_table.setItem(row, 0, QTableWidgetItem(invoice['invoice_number']))
            self.invoices_table.setItem(row, 1, QTableWidgetItem(invoice['invoice_date']))
            self.invoices_table.setItem(row, 2, QTableWidgetItem(f"{invoice['total_amount']:.2f}"))
            self.invoices_table.setItem(row, 3, QTableWidgetItem(f"{invoice['paid_amount']:.2f}"))
            self.invoices_table.setItem(row, 4, QTableWidgetItem(f"{invoice['remaining_amount']:.2f}"))
            
            pay_btn = QPushButton('💰 دفع')
            pay_btn.clicked.connect(
                lambda checked, iid=invoice['invoice_id']: 
                self.add_payment_dialog(iid)
            )
            pay_btn.setStyleSheet("background: #27ae60; color: white; padding: 3px;")
            self.invoices_table.setCellWidget(row, 5, pay_btn)
    
    def create_stat_card(self, title, value, color):
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{ 
                font-weight: bold; 
                background: {color}; 
                color: white; 
                padding: 10px; 
                border-radius: 5px; 
            }}
        """)
        layout = QVBoxLayout()
        
        value_label = QLabel(value)
        value_label.setFont(QFont('Arial', 14, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color: white;")
        
        layout.addWidget(value_label)
        group.setLayout(layout)
        return group
    
    def add_payment_dialog(self, invoice_id=None):
        dialog = AddPaymentDialog(self.customer_id, invoice_id, self.db_path, self)
        if dialog.exec_():
            self.load_data()


class InvoiceDetailsDialog(QDialog):
    """نافذة تفاصيل فاتورة"""
    
    def __init__(self, invoice_id, db_path, parent=None):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.db_path = db_path
        self.controller = CreditController(db_path)
        
        self.setWindowTitle('تفاصيل الفاتورة')
        self.setModal(True)
        self.setMinimumSize(800, 600)
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # معلومات الفاتورة
        self.info_label = QLabel()
        self.info_label.setFont(QFont('Arial', 11))
        self.info_label.setStyleSheet("padding: 10px; background: #ecf0f1; border-radius: 5px;")
        layout.addWidget(self.info_label)
        
        # المشتريات
        items_label = QLabel('🛍️ المشتريات:')
        items_label.setFont(QFont('Arial', 12, QFont.Bold))
        layout.addWidget(items_label)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            'الكود', 'المنتج', 'الكمية', 'السعر', 'المجموع'
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.items_table)
        
        # الدفعات
        payments_label = QLabel('💰 الدفعات:')
        payments_label.setFont(QFont('Arial', 12, QFont.Bold))
        layout.addWidget(payments_label)
        
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(4)
        self.payments_table.setHorizontalHeaderLabels([
            'التاريخ', 'المبلغ', 'الطريقة', 'المستلم'
        ])
        self.payments_table.horizontalHeader().setStretchLastSection(True)
        self.payments_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.payments_table)
        
        # ملخص
        self.summary_label = QLabel()
        self.summary_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.summary_label.setStyleSheet("padding: 15px; background: #3498db; color: white; border-radius: 5px;")
        layout.addWidget(self.summary_label)
        
        # زر إغلاق
        close_btn = QPushButton('إغلاق')
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background: #e74c3c; color: white; padding: 10px;")
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def load_data(self):
        invoice = self.controller.get_invoice_details(self.invoice_id)
        
        if not invoice:
            QMessageBox.warning(self, 'خطأ', 'لم يتم العثور على الفاتورة!')
            self.reject()
            return
        
        # معلومات الفاتورة
        info_text = f"""
<b>📄 فاتورة رقم: {invoice['invoice_number']}</b><br>
👤 الزبون: {invoice['customer_name']}<br>
📞 التليفون: {invoice['customer_phone'] or '-'}<br>
📅 التاريخ: {invoice['invoice_date']}<br>
⏰ موعد السداد: {invoice['due_date'] or '-'}
        """
        self.info_label.setText(info_text)
        
        # المشتريات
        for item in invoice['items']:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            
            self.items_table.setItem(row, 0, QTableWidgetItem(item['product_code']))
            self.items_table.setItem(row, 1, QTableWidgetItem(item['product_name']))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{item['unit_price']:.2f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{item['total_price']:.2f}"))
        
        # الدفعات
        if invoice['payments']:
            for payment in invoice['payments']:
                row = self.payments_table.rowCount()
                self.payments_table.insertRow(row)
                
                self.payments_table.setItem(row, 0, QTableWidgetItem(payment['payment_date']))
                self.payments_table.setItem(row, 1, QTableWidgetItem(f"{payment['amount']:.2f} ج"))
                self.payments_table.setItem(row, 2, QTableWidgetItem(payment['payment_method']))
                self.payments_table.setItem(row, 3, QTableWidgetItem(payment['received_by'] or '-'))
        else:
            self.payments_table.setRowCount(1)
            self.payments_table.setItem(0, 0, QTableWidgetItem('لم يتم تسجيل دفعات بعد'))
        
        # ملخص
        summary_text = f"""
📊 الملخص:
إجمالي الفاتورة: {invoice['total_amount']:.2f} جنيه  |
المدفوع: {invoice['paid_amount']:.2f} جنيه  |
المتبقي: {invoice['remaining_amount']:.2f} جنيه
        """
        self.summary_label.setText(summary_text)


class AddPaymentDialog(QDialog):
    """نافذة تسجيل دفعة"""
    
    def __init__(self, customer_id, invoice_id, db_path, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.invoice_id = invoice_id
        self.db_path = db_path
        self.controller = CreditController(db_path)
        
        self.setWindowTitle('تسجيل دفعة')
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # معلومات الفاتورة
        invoice = self.controller.get_invoice_details(self.invoice_id)
        
        if invoice:
            info_label = QLabel(
                f"📄 فاتورة: {invoice['invoice_number']}\n"
                f"💰 المتبقي: {invoice['remaining_amount']:.2f} جنيه"
            )
            info_label.setStyleSheet("padding: 10px; background: #e8f8f5; border-radius: 5px; font-weight: bold;")
            layout.addRow(info_label)
        
        # المبلغ
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(1000000)
        self.amount_input.setDecimals(2)
        self.amount_input.setSuffix(' جنيه')
        if invoice:
            self.amount_input.setValue(invoice['remaining_amount'])
        layout.addRow('المبلغ المدفوع *:', self.amount_input)
        
        # طريقة الدفع
        self.method_combo = QComboBox()
        self.method_combo.addItems(['cash', 'vodafone_cash', 'instapay', 'bank_transfer'])
        layout.addRow('طريقة الدفع:', self.method_combo)
        
        # المستلم
        self.received_input = QLineEdit()
        self.received_input.setPlaceholderText('مثال: المدير')
        layout.addRow('اسم المستلم:', self.received_input)
        
        # ملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText('ملاحظات اختيارية...')
        layout.addRow('ملاحظات:', self.notes_input)
        
        # أزرار
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_payment)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def save_payment(self):
        amount = self.amount_input.value()
        
        if amount <= 0:
            QMessageBox.warning(self, 'خطأ', 'المبلغ يجب أن يكون أكبر من صفر!')
            return
        
        success, message = self.controller.add_payment(
            self.customer_id,
            self.invoice_id,
            amount,
            self.method_combo.currentText(),
            self.received_input.text() or None,
            self.notes_input.toPlainText() or None
        )
        
        if success:
            QMessageBox.information(self, 'نجح ✅', message)
            self.accept()
        else:
            QMessageBox.warning(self, 'خطأ', message)


class CreateInvoiceDialog(QDialog):
    """نافذة إنشاء فاتورة آجلة"""
    
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.controller = CreditController(db_path)
        self.cart_items = []
        
        self.setWindowTitle('إنشاء فاتورة آجلة')
        self.setModal(True)
        self.setMinimumSize(900, 700)
        
        self.init_ui()
        self.load_customers()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # اختيار الزبون
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel('الزبون:'))
        
        self.customer_combo = QComboBox()
        customer_layout.addWidget(self.customer_combo)
        
        layout.addLayout(customer_layout)
        
        # بحث المنتجات
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('بحث منتج:'))
        
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText('اكتب للبحث...')
        self.product_search.textChanged.connect(self.search_products)
        search_layout.addWidget(self.product_search)
        
        layout.addLayout(search_layout)
        
        # جدول نتائج البحث
        self.search_table = QTableWidget()
        self.search_table.setColumnCount(6)
        self.search_table.setHorizontalHeaderLabels([
            'الكود', 'الاسم', 'السعر', 'المخزون', 'الكمية', 'إضافة'
        ])
        self.search_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.search_table.setMaximumHeight(200)
        layout.addWidget(self.search_table)
        
        # سلة المشتريات
        cart_label = QLabel('🛍️ المشتريات:')
        cart_label.setFont(QFont('Arial', 12, QFont.Bold))
        layout.addWidget(cart_label)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels([
            'الكود', 'المنتج', 'السعر', 'الكمية', 'المجموع', 'حذف'
        ])
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.cart_table)
        
        # الإجمالي
        self.total_label = QLabel('الإجمالي: 0.00 جنيه')
        self.total_label.setFont(QFont('Arial', 16, QFont.Bold))
        self.total_label.setStyleSheet("color: #27ae60; padding: 10px;")
        layout.addWidget(self.total_label)
        
        # موعد السداد
        due_layout = QHBoxLayout()
        due_layout.addWidget(QLabel('موعد السداد:'))
        
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate().addDays(30))
        due_layout.addWidget(self.due_date)
        
        layout.addLayout(due_layout)
        
        # أزرار
        btn_layout = QHBoxLayout()
        
        create_btn = QPushButton('✅ إنشاء الفاتورة')
        create_btn.clicked.connect(self.create_invoice)
        create_btn.setStyleSheet("background: #27ae60; color: white; padding: 10px; font-size: 14px;")
        btn_layout.addWidget(create_btn)
        
        cancel_btn = QPushButton('إلغاء')
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background: #e74c3c; color: white; padding: 10px;")
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_customers(self):
        """✅ تحميل قائمة الزبائن مع معالجة الأخطاء"""
        try:
            customers = self.controller.get_all_customers()
            
            if not customers:
                QMessageBox.warning(
                    self, 'تنبيه',
                    'لا يوجد زبائن!\n\nيجب إضافة زبون أولاً من تبويب "الزبائن".'
                )
                self.reject()
                return
            
            for customer in customers:
                self.customer_combo.addItem(
                    f"{customer['name']} ({customer['phone'] or 'لا يوجد تليفون'})",
                    customer['customer_id']
                )
        except Exception as e:
            QMessageBox.critical(
                self, 'خطأ',
                f'فشل تحميل الزبائن:\n{str(e)}\n\n{traceback.format_exc()}'
            )
            self.reject()
    
    def search_products(self):
        """✅ البحث عن المنتجات مع معالجة الأخطاء"""
        try:
            search_term = self.product_search.text().strip()
            
            if len(search_term) < 1:
                self.search_table.setRowCount(0)
                return
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM products
                WHERE product_code LIKE ? OR product_name LIKE ?
                LIMIT 10
            """, (f'%{search_term}%', f'%{search_term}%'))
            
            products = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.search_table.setRowCount(0)
            for product in products:
                row = self.search_table.rowCount()
                self.search_table.insertRow(row)
                
                self.search_table.setItem(row, 0, QTableWidgetItem(product['product_code']))
                self.search_table.setItem(row, 1, QTableWidgetItem(product['product_name']))
                self.search_table.setItem(row, 2, QTableWidgetItem(f"{product['selling_price']:.2f}"))
                self.search_table.setItem(row, 3, QTableWidgetItem(str(product['current_stock'])))
                
                qty_spin = QSpinBox()
                qty_spin.setMinimum(1)
                qty_spin.setMaximum(max(1, product['current_stock']))  # ✅ Fix: at least 1
                qty_spin.setValue(1)
                self.search_table.setCellWidget(row, 4, qty_spin)
                
                add_btn = QPushButton('➕')
                add_btn.clicked.connect(
                    lambda checked, p=product, sp=qty_spin: 
                    self.add_to_cart(p, sp.value())
                )
                add_btn.setStyleSheet("background: #27ae60; color: white;")
                self.search_table.setCellWidget(row, 5, add_btn)
                
        except Exception as e:
            QMessageBox.critical(
                self, 'خطأ',
                f'فشل البحث عن المنتجات:\n{str(e)}\n\n{traceback.format_exc()}'
            )
    
    def add_to_cart(self, product, quantity):
        """✅ إضافة منتج للسلة مع معالجة الأخطاء"""
        try:
            # التحقق من المخزون
            if quantity > product['current_stock']:
                QMessageBox.warning(
                    self, 'تحذير',
                    f'الكمية المطلوبة ({quantity}) أكبر من المخزون ({product["current_stock"]})!'
                )
                return
            
            # التحقق من عدم وجوده مسبقاً
            for item in self.cart_items:
                if item['code'] == product['product_code']:
                    item['qty'] += quantity
                    self.refresh_cart()
                    return
            
            self.cart_items.append({
                'code': product['product_code'],
                'name': product['product_name'],
                'price': product['selling_price'],
                'qty': quantity
            })
            
            self.refresh_cart()
            self.product_search.clear()
            
        except Exception as e:
            QMessageBox.critical(
                self, 'خطأ',
                f'فشل إضافة المنتج:\n{str(e)}\n\n{traceback.format_exc()}'
            )
    
    def refresh_cart(self):
        """✅ تحديث سلة المشتريات"""
        try:
            self.cart_table.setRowCount(0)
            total = 0
            
            for i, item in enumerate(self.cart_items):
                row = self.cart_table.rowCount()
                self.cart_table.insertRow(row)
                
                subtotal = item['qty'] * item['price']
                total += subtotal
                
                self.cart_table.setItem(row, 0, QTableWidgetItem(item['code']))
                self.cart_table.setItem(row, 1, QTableWidgetItem(item['name']))
                self.cart_table.setItem(row, 2, QTableWidgetItem(f"{item['price']:.2f}"))
                self.cart_table.setItem(row, 3, QTableWidgetItem(str(item['qty'])))
                self.cart_table.setItem(row, 4, QTableWidgetItem(f"{subtotal:.2f}"))
                
                del_btn = QPushButton('🗑️')
                del_btn.clicked.connect(lambda checked, idx=i: self.remove_from_cart(idx))
                del_btn.setStyleSheet("background: #e74c3c; color: white;")
                self.cart_table.setCellWidget(row, 5, del_btn)
            
            self.total_label.setText(f'الإجمالي: {total:.2f} جنيه')
            
        except Exception as e:
            QMessageBox.critical(
                self, 'خطأ',
                f'فشل تحديث السلة:\n{str(e)}\n\n{traceback.format_exc()}'
            )
    
    def remove_from_cart(self, index):
        """✅ حذف منتج من السلة"""
        try:
            del self.cart_items[index]
            self.refresh_cart()
        except Exception as e:
            QMessageBox.critical(
                self, 'خطأ',
                f'فشل حذف المنتج:\n{str(e)}'
            )
    
    def create_invoice(self):
        """✅ إنشاء الفاتورة مع معالجة شاملة للأخطاء"""
        try:
            # التحقق من اختيار زبون
            if self.customer_combo.currentIndex() < 0:
                QMessageBox.warning(self, 'خطأ', 'يجب اختيار زبون!')
                return
            
            # التحقق من وجود منتجات
            if not self.cart_items:
                QMessageBox.warning(self, 'خطأ', 'يجب إضافة منتجات!')
                return
            
            customer_id = self.customer_combo.currentData()
            due_date = self.due_date.date().toString('yyyy-MM-dd')
            
            # استدعاء الـ controller
            result = self.controller.create_credit_sale(
                customer_id, self.cart_items, due_date
            )
            
            # ✅ التحقق من نوع النتيجة
            if not isinstance(result, tuple) or len(result) != 4:
                raise ValueError(f"نتيجة غير متوقعة من create_credit_sale: {result}")
            
            success, invoice_id, invoice_number, message = result
            
            if success:
                QMessageBox.information(
                    self, 'نجح ✅',
                    f'{message}\n\nرقم الفاتورة: {invoice_number}'
                )
                self.accept()
            else:
                QMessageBox.warning(self, 'خطأ', message)
                
        except Exception as e:
            # ✅ عرض رسالة خطأ تفصيلية
            error_msg = f"""فشل إنشاء الفاتورة!

الخطأ: {str(e)}

التفاصيل الفنية:
{traceback.format_exc()}

الرجاء التحقق من:
1. أن المنتجات متوفرة في المخزون
2. أن قاعدة البيانات تعمل بشكل صحيح
3. أن جميع الحقول مملوءة بشكل صحيح"""
            
            QMessageBox.critical(self, 'خطأ فادح', error_msg)
            print("\n" + "="*60)
            print("❌ ERROR IN CREATE_INVOICE:")
            print(traceback.format_exc())
            print("="*60 + "\n")
