#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
واجهة التسجيل السريع للفواتير الآجلة
Quick Credit Registration View
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QTextEdit,
    QComboBox, QDoubleSpinBox, QSpinBox, QDateEdit, QGroupBox,
    QHeaderView, QAbstractItemView, QSplitter
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

import sqlite3
from datetime import datetime, timedelta
import traceback

class QuickCreditView(QWidget):
    """واجهة مبسطة لتسجيل الفواتير الآجلة"""
    
    def __init__(self, db_path='aldhaferya_store.db', parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.cart_items = []
        self.current_customer = None
        self.init_ui()
        self.load_invoices()
    
    def init_ui(self):
        """تهيئة الواجهة"""
        main_layout = QHBoxLayout()
        
        # القسم الأيمن: تسجيل فاتورة جديدة
        registration_widget = self.create_registration_panel()
        
        # القسم الأيسر: البحث والفواتير
        search_widget = self.create_search_panel()
        
        # تقسيم الشاشة
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(registration_widget)
        splitter.addWidget(search_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def create_registration_panel(self):
        """إنشاء لوحة التسجيل"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # العنوان
        header = QLabel('📝 تسجيل فاتورة آجلة')
        header.setFont(QFont('Arial', 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 10px; background: #ecf0f1; border-radius: 5px;")
        layout.addWidget(header)
        
        # معلومات الزبون
        customer_group = QGroupBox('👤 معلومات الزبون')
        customer_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('اكتب الاسم...')
        self.name_input.textChanged.connect(self.search_customer_by_name)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText('01234567890')
        self.phone_input.textChanged.connect(self.search_customer_by_phone)
        
        customer_layout.addRow('الاسم:', self.name_input)
        customer_layout.addRow('التليفون:', self.phone_input)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # اقتراحات الزبائن
        self.suggestions_label = QLabel()
        self.suggestions_label.setStyleSheet("""
            QLabel {
                background: #e8f8f5;
                padding: 5px;
                border-radius: 3px;
                color: #27ae60;
                font-weight: bold;
            }
        """)
        self.suggestions_label.hide()
        layout.addWidget(self.suggestions_label)
        
        # المنتجات
        products_group = QGroupBox('🛍️ المشتريات')
        products_layout = QVBoxLayout()
        
        # بحث منتج
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('بحث:'))
        
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText('اكتب كود أو اسم المنتج...')
        self.product_search.textChanged.connect(self.search_products)
        search_layout.addWidget(self.product_search)
        
        products_layout.addLayout(search_layout)
        
        # نتائج البحث المصغرة
        self.search_results = QTableWidget()
        self.search_results.setColumnCount(5)
        self.search_results.setHorizontalHeaderLabels(['الكود', 'المنتج', 'السعر', 'الكمية', 'إضافة'])
        self.search_results.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.search_results.setMaximumHeight(150)
        self.search_results.setEditTriggers(QAbstractItemView.NoEditTriggers)
        products_layout.addWidget(self.search_results)
        
        # السلة
        cart_label = QLabel('السلة:')
        cart_label.setFont(QFont('Arial', 10, QFont.Bold))
        products_layout.addWidget(cart_label)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(['المنتج', 'السعر', 'الكمية', 'المجموع', 'حذف'])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        products_layout.addWidget(self.cart_table)
        
        products_group.setLayout(products_layout)
        layout.addWidget(products_group)
        
        # الإجمالي
        self.total_label = QLabel('الإجمالي: 0.00 ج')
        self.total_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.total_label.setStyleSheet("color: #27ae60; padding: 10px; background: #d5f4e6; border-radius: 5px;")
        self.total_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.total_label)
        
        # موعد السداد
        due_layout = QHBoxLayout()
        due_layout.addWidget(QLabel('موعد السداد:'))
        
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate().addDays(30))
        due_layout.addWidget(self.due_date)
        
        layout.addLayout(due_layout)
        
        # أزرار الإجراءات
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton('💾 حفظ الفاتورة')
        save_btn.clicked.connect(self.save_invoice)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        btn_layout.addWidget(save_btn)
        
        clear_btn = QPushButton('🗑️ مسح')
        clear_btn.clicked.connect(self.clear_form)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                padding: 12px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_search_panel(self):
        """إنشاء لوحة البحث والفواتير"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # العنوان
        header = QLabel('🔍 البحث في الفواتير')
        header.setFont(QFont('Arial', 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 10px; background: #ecf0f1; border-radius: 5px;")
        layout.addWidget(header)
        
        # شريط البحث
        search_layout = QHBoxLayout()
        
        self.invoice_search = QLineEdit()
        self.invoice_search.setPlaceholderText('🔍 ابحث بالاسم، التليفون، أو رقم الفاتورة...')
        self.invoice_search.textChanged.connect(self.search_invoices)
        self.invoice_search.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 5px;
            }
        """)
        search_layout.addWidget(self.invoice_search)
        
        refresh_btn = QPushButton('🔄')
        refresh_btn.clicked.connect(self.load_invoices)
        refresh_btn.setStyleSheet("background: #3498db; color: white; padding: 10px; font-weight: bold;")
        search_layout.addWidget(refresh_btn)
        
        layout.addLayout(search_layout)
        
        # جدول الفواتير
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(7)
        self.invoices_table.setHorizontalHeaderLabels([
            'رقم الفاتورة', 'الزبون', 'التليفون', 'الإجمالي',
            'المتبقي', 'التاريخ', 'إجراء'
        ])
        self.invoices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.invoices_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        layout.addWidget(self.invoices_table)
        
        widget.setLayout(layout)
        return widget
    
    def search_customer_by_name(self):
        """البحث عن زبون بالاسم"""
        name = self.name_input.text().strip()
        if len(name) < 2:
            self.suggestions_label.hide()
            self.current_customer = None
            return
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM customers
            WHERE name LIKE ?
            LIMIT 5
        """, (f'%{name}%',))
        
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if customers:
            if len(customers) == 1:
                # زبون واحد فقط - نملأ البيانات تلقائياً
                self.current_customer = customers[0]
                self.phone_input.setText(customers[0]['phone'] or '')
                self.suggestions_label.setText(f"✅ تم العثور على: {customers[0]['name']} ({customers[0]['phone'] or 'لا يوجد تليفون'})")
                self.suggestions_label.show()
            else:
                # عدة زبائن - نعرض الاقتراحات
                names = ', '.join([c['name'] for c in customers[:3]])
                self.suggestions_label.setText(f"💡 زبائن مشابهون: {names}...")
                self.suggestions_label.show()
                self.current_customer = None
        else:
            self.suggestions_label.setText(f"🆕 زبون جديد: {name}")
            self.suggestions_label.show()
            self.current_customer = None
    
    def search_customer_by_phone(self):
        """البحث عن زبون بالتليفون"""
        phone = self.phone_input.text().strip()
        if len(phone) < 4:
            return
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM customers
            WHERE phone LIKE ?
            LIMIT 1
        """, (f'%{phone}%',))
        
        customer = cursor.fetchone()
        conn.close()
        
        if customer:
            self.current_customer = dict(customer)
            self.name_input.setText(customer['name'])
            self.suggestions_label.setText(f"✅ تم العثور على: {customer['name']}")
            self.suggestions_label.show()
    
    def search_products(self):
        """البحث عن منتجات"""
        search_term = self.product_search.text().strip()
        
        if len(search_term) < 1:
            self.search_results.setRowCount(0)
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM products
                WHERE (product_code LIKE ? OR product_name LIKE ?)
                AND current_stock > 0
                LIMIT 8
            """, (f'%{search_term}%', f'%{search_term}%'))
            
            products = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.search_results.setRowCount(0)
            for product in products:
                row = self.search_results.rowCount()
                self.search_results.insertRow(row)
                
                self.search_results.setItem(row, 0, QTableWidgetItem(product['product_code']))
                self.search_results.setItem(row, 1, QTableWidgetItem(product['product_name']))
                self.search_results.setItem(row, 2, QTableWidgetItem(f"{product['selling_price']:.2f} ج"))
                
                # خانة الكمية
                qty_spin = QSpinBox()
                qty_spin.setMinimum(1)
                qty_spin.setMaximum(max(1, product['current_stock']))
                qty_spin.setValue(1)
                qty_spin.setStyleSheet("padding: 3px; font-size: 12px;")
                self.search_results.setCellWidget(row, 3, qty_spin)
                
                # زر الإضافة
                add_btn = QPushButton('➕')
                add_btn.clicked.connect(
                    lambda checked, p=product, sp=qty_spin:
                    self.add_to_cart(p, sp.value())
                )
                add_btn.setStyleSheet("background: #27ae60; color: white; font-weight: bold; padding: 5px;")
                self.search_results.setCellWidget(row, 4, add_btn)
        
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'فشل البحث عن المنتجات:\n{str(e)}')
    
    def add_to_cart(self, product, quantity):
        """إضافة منتج للسلة"""
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
                    self.product_search.clear()
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
            QMessageBox.critical(self, 'خطأ', f'فشل إضافة المنتج:\n{str(e)}')
    
    def refresh_cart(self):
        """تحديث السلة"""
        self.cart_table.setRowCount(0)
        total = 0
        
        for i, item in enumerate(self.cart_items):
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            
            subtotal = item['qty'] * item['price']
            total += subtotal
            
            self.cart_table.setItem(row, 0, QTableWidgetItem(f"{item['code']} - {item['name']}"))
            self.cart_table.setItem(row, 1, QTableWidgetItem(f"{item['price']:.2f} ج"))
            self.cart_table.setItem(row, 2, QTableWidgetItem(str(item['qty'])))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"{subtotal:.2f} ج"))
            
            del_btn = QPushButton('🗑️')
            del_btn.clicked.connect(lambda checked, idx=i: self.remove_from_cart(idx))
            del_btn.setStyleSheet("background: #e74c3c; color: white; font-weight: bold;")
            self.cart_table.setCellWidget(row, 4, del_btn)
        
        self.total_label.setText(f'الإجمالي: {total:.2f} ج')
    
    def remove_from_cart(self, index):
        """حذف منتج من السلة"""
        del self.cart_items[index]
        self.refresh_cart()
    
    def save_invoice(self):
        """حفظ الفاتورة"""
        try:
            # التحقق من البيانات
            name = self.name_input.text().strip()
            phone = self.phone_input.text().strip()
            
            if not name:
                QMessageBox.warning(self, 'خطأ', 'يجب إدخال اسم الزبون!')
                return
            
            if not self.cart_items:
                QMessageBox.warning(self, 'خطأ', 'يجب إضافة منتجات!')
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # إضافة أو جلب الزبون
            if self.current_customer:
                customer_id = self.current_customer['customer_id']
            else:
                # إنشاء زبون جديد
                cursor.execute("""
                    INSERT INTO customers (name, phone)
                    VALUES (?, ?)
                """, (name, phone or None))
                customer_id = cursor.lastrowid
            
            # حساب الإجمالي
            total = sum(item['qty'] * item['price'] for item in self.cart_items)
            
            # إنشاء رقم الفاتورة
            cursor.execute("""
                SELECT invoice_number FROM credit_invoices
                ORDER BY invoice_id DESC LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                try:
                    last_num = int(result[0].split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            invoice_number = f"INV-{datetime.now().year}-{new_num:03d}"
            due_date = self.due_date.date().toString('yyyy-MM-dd')
            
            # إنشاء الفاتورة
            cursor.execute("""
                INSERT INTO credit_invoices
                (customer_id, invoice_number, total_amount, remaining_amount,
                 invoice_date, due_date)
                VALUES (?, ?, ?, ?, date('now'), ?)
            """, (customer_id, invoice_number, total, total, due_date))
            
            invoice_id = cursor.lastrowid
            
            # إضافة المشتريات
            for item in self.cart_items:
                cursor.execute("""
                    INSERT INTO invoice_items
                    (invoice_id, product_code, product_name, quantity,
                     unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice_id, item['code'], item['name'], item['qty'],
                      item['price'], item['qty'] * item['price']))
                
                # تحديث المخزون
                cursor.execute("""
                    UPDATE products
                    SET current_stock = current_stock - ?
                    WHERE product_code = ?
                """, (item['qty'], item['code']))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(
                self, 'نجح ✅',
                f'تم حفظ الفاتورة بنجاح!\n\nرقم الفاتورة: {invoice_number}\nالإجمالي: {total:.2f} ج'
            )
            
            self.clear_form()
            self.load_invoices()
            
        except Exception as e:
            QMessageBox.critical(
                self, 'خطأ',
                f'فشل حفظ الفاتورة:\n{str(e)}\n\n{traceback.format_exc()}'
            )
    
    def clear_form(self):
        """مسح النموذج"""
        self.name_input.clear()
        self.phone_input.clear()
        self.product_search.clear()
        self.cart_items = []
        self.current_customer = None
        self.suggestions_label.hide()
        self.refresh_cart()
        self.due_date.setDate(QDate.currentDate().addDays(30))
    
    def load_invoices(self):
        """تحميل الفواتير"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ci.*, c.name as customer_name, c.phone as customer_phone
                FROM credit_invoices ci
                JOIN customers c ON ci.customer_id = c.customer_id
                ORDER BY ci.invoice_date DESC
                LIMIT 200
            """)
            
            invoices = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.display_invoices(invoices)
            
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'فشل تحميل الفواتير:\n{str(e)}')
    
    def search_invoices(self):
        """البحث في الفواتير"""
        search_term = self.invoice_search.text().strip()
        
        if len(search_term) < 1:
            self.load_invoices()
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ci.*, c.name as customer_name, c.phone as customer_phone
                FROM credit_invoices ci
                JOIN customers c ON ci.customer_id = c.customer_id
                WHERE c.name LIKE ? OR c.phone LIKE ? OR ci.invoice_number LIKE ?
                ORDER BY ci.invoice_date DESC
                LIMIT 200
            """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            
            invoices = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.display_invoices(invoices)
            
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'فشل البحث:\n{str(e)}')
    
    def display_invoices(self, invoices):
        """عرض الفواتير في الجدول"""
        self.invoices_table.setRowCount(0)
        
        for invoice in invoices:
            row = self.invoices_table.rowCount()
            self.invoices_table.insertRow(row)
            
            # لون الصف حسب الحالة
            if invoice['status'] == 'paid':
                bg_color = QColor(200, 255, 200)
            elif invoice['remaining_amount'] > 0:
                bg_color = QColor(255, 245, 220)
            else:
                bg_color = QColor(255, 255, 255)
            
            items = [
                QTableWidgetItem(invoice['invoice_number']),
                QTableWidgetItem(invoice['customer_name']),
                QTableWidgetItem(invoice['customer_phone'] or '-'),
                QTableWidgetItem(f"{invoice['total_amount']:.2f} ج"),
                QTableWidgetItem(f"{invoice['remaining_amount']:.2f} ج"),
                QTableWidgetItem(invoice['invoice_date'])
            ]
            
            for col, item in enumerate(items):
                item.setBackground(bg_color)
                self.invoices_table.setItem(row, col, item)
            
            # زر الإجراء
            action_btn = QPushButton('📝 تعديل')
            action_btn.clicked.connect(
                lambda checked, iid=invoice['invoice_id']:
                self.edit_invoice_dialog(iid)
            )
            action_btn.setStyleSheet("background: #3498db; color: white; padding: 5px; font-weight: bold;")
            self.invoices_table.setCellWidget(row, 6, action_btn)
    
    def edit_invoice_dialog(self, invoice_id):
        """نافذة تعديل الفاتورة"""
        dialog = EditInvoiceDialog(invoice_id, self.db_path, self)
        if dialog.exec_():
            self.load_invoices()


class EditInvoiceDialog(QDialog):
    """نافذة تعديل فاتورة"""
    
    def __init__(self, invoice_id, db_path, parent=None):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.db_path = db_path
        
        self.setWindowTitle('تعديل الفاتورة')
        self.setModal(True)
        self.setMinimumSize(700, 600)
        
        self.load_invoice()
        self.init_ui()
    
    def load_invoice(self):
        """تحميل بيانات الفاتورة"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ci.*, c.name as customer_name, c.phone as customer_phone
            FROM credit_invoices ci
            JOIN customers c ON ci.customer_id = c.customer_id
            WHERE ci.invoice_id = ?
        """, (self.invoice_id,))
        
        self.invoice = dict(cursor.fetchone())
        
        # تحميل المشتريات
        cursor.execute("""
            SELECT * FROM invoice_items
            WHERE invoice_id = ?
        """, (self.invoice_id,))
        
        self.invoice['items'] = [dict(row) for row in cursor.fetchall()]
        
        # تحميل الدفعات
        cursor.execute("""
            SELECT * FROM payments
            WHERE invoice_id = ?
            ORDER BY payment_date DESC
        """, (self.invoice_id,))
        
        self.invoice['payments'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
    
    def init_ui(self):
        """تهيئة الواجهة"""
        layout = QVBoxLayout()
        
        # معلومات الفاتورة
        info_label = QLabel(
            f"📄 <b>فاتورة رقم: {self.invoice['invoice_number']}</b><br>"
            f"👤 الزبون: {self.invoice['customer_name']}<br>"
            f"📞 التليفون: {self.invoice['customer_phone'] or '-'}<br>"
            f"📅 التاريخ: {self.invoice['invoice_date']}"
        )
        info_label.setStyleSheet("padding: 15px; background: #ecf0f1; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # المشتريات
        items_label = QLabel('🛍️ <b>المشتريات:</b>')
        layout.addWidget(items_label)
        
        items_table = QTableWidget()
        items_table.setColumnCount(4)
        items_table.setHorizontalHeaderLabels(['المنتج', 'الكمية', 'السعر', 'المجموع'])
        items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        items_table.setMaximumHeight(200)
        
        for item in self.invoice['items']:
            row = items_table.rowCount()
            items_table.insertRow(row)
            items_table.setItem(row, 0, QTableWidgetItem(f"{item['product_code']} - {item['product_name']}"))
            items_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
            items_table.setItem(row, 2, QTableWidgetItem(f"{item['unit_price']:.2f} ج"))
            items_table.setItem(row, 3, QTableWidgetItem(f"{item['total_price']:.2f} ج"))
        
        layout.addWidget(items_table)
        
        # ملخص مالي
        summary_group = QGroupBox('💰 الملخص المالي')
        summary_layout = QFormLayout()
        
        summary_layout.addRow('<b>إجمالي الفاتورة:</b>',
                            QLabel(f"<b style='color: #2c3e50;'>{self.invoice['total_amount']:.2f} ج</b>"))
        summary_layout.addRow('<b>المدفوع:</b>',
                            QLabel(f"<b style='color: #27ae60;'>{self.invoice['paid_amount']:.2f} ج</b>"))
        summary_layout.addRow('<b>المتبقي:</b>',
                            QLabel(f"<b style='color: #e74c3c;'>{self.invoice['remaining_amount']:.2f} ج</b>"))
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # الدفعات السابقة
        if self.invoice['payments']:
            payments_label = QLabel('📋 <b>الدفعات السابقة:</b>')
            layout.addWidget(payments_label)
            
            payments_table = QTableWidget()
            payments_table.setColumnCount(3)
            payments_table.setHorizontalHeaderLabels(['التاريخ', 'المبلغ', 'الطريقة'])
            payments_table.setMaximumHeight(150)
            
            for payment in self.invoice['payments']:
                row = payments_table.rowCount()
                payments_table.insertRow(row)
                payments_table.setItem(row, 0, QTableWidgetItem(payment['payment_date']))
                payments_table.setItem(row, 1, QTableWidgetItem(f"{payment['amount']:.2f} ج"))
                payments_table.setItem(row, 2, QTableWidgetItem(payment['payment_method']))
            
            layout.addWidget(payments_table)
        
        # إضافة دفعة جديدة
        if self.invoice['remaining_amount'] > 0:
            payment_group = QGroupBox('➕ إضافة دفعة جديدة')
            payment_layout = QFormLayout()
            
            self.payment_amount = QDoubleSpinBox()
            self.payment_amount.setMaximum(self.invoice['remaining_amount'])
            self.payment_amount.setValue(self.invoice['remaining_amount'])
            self.payment_amount.setSuffix(' جنيه')
            self.payment_amount.setStyleSheet("padding: 5px; font-size: 14px;")
            
            self.payment_method = QComboBox()
            self.payment_method.addItems(['cash', 'vodafone_cash', 'instapay', 'bank_transfer'])
            
            payment_layout.addRow('المبلغ:', self.payment_amount)
            payment_layout.addRow('الطريقة:', self.payment_method)
            
            payment_group.setLayout(payment_layout)
            layout.addWidget(payment_group)
            
            # أزرار
            btn_layout = QHBoxLayout()
            
            pay_btn = QPushButton('💰 تسجيل دفعة')
            pay_btn.clicked.connect(self.add_payment)
            pay_btn.setStyleSheet("""
                QPushButton {
                    background: #27ae60;
                    color: white;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
            btn_layout.addWidget(pay_btn)
            
            pay_full_btn = QPushButton('✅ سداد كامل')
            pay_full_btn.clicked.connect(self.pay_full)
            pay_full_btn.setStyleSheet("""
                QPushButton {
                    background: #3498db;
                    color: white;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
            btn_layout.addWidget(pay_full_btn)
            
            layout.addLayout(btn_layout)
        else:
            paid_label = QLabel('✅ تم السداد بالكامل')
            paid_label.setFont(QFont('Arial', 14, QFont.Bold))
            paid_label.setAlignment(Qt.AlignCenter)
            paid_label.setStyleSheet("color: #27ae60; padding: 15px; background: #d5f4e6; border-radius: 5px;")
            layout.addWidget(paid_label)
        
        # زر إغلاق
        close_btn = QPushButton('إغلاق')
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background: #95a5a6; color: white; padding: 10px;")
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def add_payment(self):
        """تسجيل دفعة"""
        amount = self.payment_amount.value()
        
        if amount <= 0:
            QMessageBox.warning(self, 'خطأ', 'المبلغ يجب أن يكون أكبر من صفر!')
            return
        
        if amount > self.invoice['remaining_amount']:
            QMessageBox.warning(self, 'خطأ', f'المبلغ أكبر من المتبقي ({self.invoice["remaining_amount"]:.2f} ج)!')
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # تسجيل الدفعة
            cursor.execute("""
                INSERT INTO payments
                (customer_id, invoice_id, amount, payment_method, payment_date)
                VALUES (?, ?, ?, ?, date('now'))
            """, (self.invoice['customer_id'], self.invoice_id, amount, self.payment_method.currentText()))
            
            # تحديث الفاتورة
            new_remaining = self.invoice['remaining_amount'] - amount
            new_status = 'paid' if new_remaining == 0 else 'partial'
            
            cursor.execute("""
                UPDATE credit_invoices
                SET paid_amount = paid_amount + ?,
                    remaining_amount = ?,
                    status = ?
                WHERE invoice_id = ?
            """, (amount, new_remaining, new_status, self.invoice_id))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, 'نجح ✅', f'تم تسجيل دفعة بقيمة {amount:.2f} ج')
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'فشل تسجيل الدفعة:\n{str(e)}')
    
    def pay_full(self):
        """سداد كامل"""
        self.payment_amount.setValue(self.invoice['remaining_amount'])
        self.add_payment()
