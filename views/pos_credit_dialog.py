#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة فاتورة آجلة من نقطة البيع
Credit Invoice Dialog from POS
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QMessageBox,
    QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
import sqlite3
from datetime import datetime
import re

class POSCreditDialog(QDialog):
    """نافذة لتحويل مشتريات نقطة البيع لفاتورة آجلة"""
    
    def __init__(self, cart_items, total_amount, db_path, parent=None):
        super().__init__(parent)
        self.cart_items = cart_items  # قائمة المشتريات من نقطة البيع
        self.total_amount = total_amount
        self.db_path = db_path
        self.current_customer = None
        
        self.setWindowTitle('📋 فاتورة آجلة')
        self.setModal(True)
        self.setMinimumSize(500, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """تهيئة الواجهة"""
        layout = QVBoxLayout()
        
        # العنوان
        header = QLabel('📝 تحويل إلى فاتورة آجلة')
        header.setFont(QFont('Arial', 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                color: white;
                background: #9b59b6;
                padding: 15px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(header)
        
        # عرض المشتريات
        items_label = QLabel(f'🛍️ المشتريات ({len(self.cart_items)} منتج):')
        items_label.setFont(QFont('Arial', 12, QFont.Bold))
        layout.addWidget(items_label)
        
        items_table = QTableWidget()
        items_table.setColumnCount(3)
        items_table.setHorizontalHeaderLabels(['المنتج', 'الكمية', 'السعر'])
        items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        items_table.setMaximumHeight(200)
        items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        for item in self.cart_items:
            row = items_table.rowCount()
            items_table.insertRow(row)
            items_table.setItem(row, 0, QTableWidgetItem(f"{item['code']} - {item['name']}"))
            items_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
            items_table.setItem(row, 2, QTableWidgetItem(f"{item['price'] * item['quantity']:.2f} ج"))
        
        layout.addWidget(items_table)
        
        # الإجمالي
        total_label = QLabel(f'💰 الإجمالي: {self.total_amount:.2f} جنيه')
        total_label.setFont(QFont('Arial', 18, QFont.Bold))
        total_label.setAlignment(Qt.AlignCenter)
        total_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                background: #d5f4e6;
                padding: 15px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(total_label)
        
        # معلومات الزبون
        customer_group = QLabel('👤 معلومات الزبون')
        customer_group.setFont(QFont('Arial', 12, QFont.Bold))
        customer_group.setStyleSheet("padding: 10px; background: #ecf0f1;")
        layout.addWidget(customer_group)
        
        form_layout = QFormLayout()
        
        # الاسم
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('اكتب اسم الزبون...')
        self.name_input.textChanged.connect(self.search_customer_by_name)
        self.name_input.setStyleSheet("padding: 8px; font-size: 14px;")
        form_layout.addRow('الاسم *:', self.name_input)
        
        # رقم التليفون
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText('01234567890 (11 رقم)')
        self.phone_input.setMaxLength(11)
        self.phone_input.textChanged.connect(self.validate_phone)
        self.phone_input.textChanged.connect(self.search_customer_by_phone)
        self.phone_input.setStyleSheet("padding: 8px; font-size: 14px;")
        form_layout.addRow('التليفون *:', self.phone_input)
        
        # رسالة التحقق
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                border-radius: 3px;
                font-weight: bold;
            }
        """)
        self.validation_label.hide()
        form_layout.addRow('', self.validation_label)
        
        # موعد السداد
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate().addDays(30))
        self.due_date.setStyleSheet("padding: 8px; font-size: 14px;")
        form_layout.addRow('موعد السداد:', self.due_date)
        
        layout.addLayout(form_layout)
        
        # رسالة الاقتراحات
        self.suggestions_label = QLabel()
        self.suggestions_label.setStyleSheet("""
            QLabel {
                background: #e8f8f5;
                color: #27ae60;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        self.suggestions_label.hide()
        layout.addWidget(self.suggestions_label)
        
        # الأزرار
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton('✅ حفظ الفاتورة')
        save_btn.clicked.connect(self.save_credit_invoice)
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
        
        cancel_btn = QPushButton('✖ إلغاء')
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                padding: 12px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def validate_phone(self):
        """التحقق من رقم التليفون"""
        phone = self.phone_input.text().strip()
        
        if len(phone) == 0:
            self.validation_label.hide()
            return
        
        # التحقق من أن كلها أرقام
        if not phone.isdigit():
            self.validation_label.setText('❌ رقم التليفون يجب أن يحتوي على أرقام فقط')
            self.validation_label.setStyleSheet("""
                QLabel {
                    background: #fadbd8;
                    color: #e74c3c;
                    padding: 5px;
                    border-radius: 3px;
                    font-weight: bold;
                }
            """)
            self.validation_label.show()
            return False
        
        # التحقق من الطول
        if len(phone) < 11:
            self.validation_label.setText(f'⚠️ رقم التليفون يجب أن يكون 11 رقم ({len(phone)}/11)')
            self.validation_label.setStyleSheet("""
                QLabel {
                    background: #fff3cd;
                    color: #f39c12;
                    padding: 5px;
                    border-radius: 3px;
                    font-weight: bold;
                }
            """)
            self.validation_label.show()
            return False
        
        if len(phone) == 11:
            # التحقق من أن يبدأ بـ 01
            if not phone.startswith('01'):
                self.validation_label.setText('❌ رقم التليفون يجب أن يبدأ بـ 01')
                self.validation_label.setStyleSheet("""
                    QLabel {
                        background: #fadbd8;
                        color: #e74c3c;
                        padding: 5px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                """)
                self.validation_label.show()
                return False
            
            self.validation_label.setText('✅ رقم صحيح')
            self.validation_label.setStyleSheet("""
                QLabel {
                    background: #d5f4e6;
                    color: #27ae60;
                    padding: 5px;
                    border-radius: 3px;
                    font-weight: bold;
                }
            """)
            self.validation_label.show()
            return True
        
        return False
    
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
            LIMIT 3
        """, (f'%{name}%',))
        
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if customers:
            if len(customers) == 1:
                self.current_customer = customers[0]
                self.phone_input.setText(customers[0]['phone'] or '')
                self.suggestions_label.setText(f"✅ تم العثور على: {customers[0]['name']} - {customers[0]['phone'] or 'لا يوجد تليفون'}")
                self.suggestions_label.show()
            else:
                names = ', '.join([c['name'] for c in customers])
                self.suggestions_label.setText(f"💡 زبائن مشابهون: {names}")
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
    
    def save_credit_invoice(self):
        """حفظ الفاتورة الآجلة"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        
        # التحقق من البيانات
        if not name:
            QMessageBox.warning(self, 'خطأ', 'يجب إدخال اسم الزبون!')
            self.name_input.setFocus()
            return
        
        if not phone:
            QMessageBox.warning(self, 'خطأ', 'يجب إدخال رقم التليفون!')
            self.phone_input.setFocus()
            return
        
        if not self.validate_phone():
            QMessageBox.warning(self, 'خطأ', 'رقم التليفون غير صحيح!\nيجب أن يكون 11 رقم ويبدأ بـ 01')
            self.phone_input.setFocus()
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # إضافة أو تحديث الزبون
            if self.current_customer:
                customer_id = self.current_customer['customer_id']
                # تحديث التليفون لو متغير
                if self.current_customer['phone'] != phone:
                    cursor.execute("""
                        UPDATE customers SET phone = ?
                        WHERE customer_id = ?
                    """, (phone, customer_id))
            else:
                # زبون جديد
                cursor.execute("""
                    INSERT INTO customers (name, phone)
                    VALUES (?, ?)
                """, (name, phone))
                customer_id = cursor.lastrowid
            
            # إنشاء رقم فاتورة
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
            
            # حفظ الفاتورة
            cursor.execute("""
                INSERT INTO credit_invoices
                (customer_id, invoice_number, total_amount, remaining_amount,
                 invoice_date, due_date)
                VALUES (?, ?, ?, ?, date('now'), ?)
            """, (customer_id, invoice_number, self.total_amount, self.total_amount, due_date))
            
            invoice_id = cursor.lastrowid
            
            # حفظ المشتريات
            for item in self.cart_items:
                cursor.execute("""
                    INSERT INTO invoice_items
                    (invoice_id, product_code, product_name, quantity,
                     unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    item['code'],
                    item['name'],
                    item['quantity'],
                    item['price'],
                    item['price'] * item['quantity']
                ))
                
                # تحديث المخزون
                cursor.execute("""
                    UPDATE products
                    SET current_stock = current_stock - ?
                    WHERE product_code = ?
                """, (item['quantity'], item['code']))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(
                self, 'نجح ✅',
                f'تم حفظ الفاتورة بنجاح!\n\n'
                f'رقم الفاتورة: {invoice_number}\n'
                f'الزبون: {name}\n'
                f'الإجمالي: {self.total_amount:.2f} جنيه'
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, 'خطأ',
                f'فشل حفظ الفاتورة:\n{str(e)}'
            )
