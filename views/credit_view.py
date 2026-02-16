#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
واجهة نظام الديون
Credit Management View
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QTextEdit,
    QComboBox, QDoubleSpinBox, QSpinBox, QDateEdit, QTabWidget,
    QGroupBox, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from controllers.credit_controller import CreditController
from datetime import datetime, timedelta

# ✅ Import dialogs and quick view
from views.credit_dialogs import (
    CustomerDetailsDialog,
    InvoiceDetailsDialog,
    AddPaymentDialog,
    CreateInvoiceDialog
)
from views.quick_credit_view import QuickCreditView

class CreditManagementView(QWidget):
    """الواجهة الرئيسية لإدارة الديون"""
    
    def __init__(self, db_path='aldhaferya_store.db', parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.controller = CreditController(db_path)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """تهيئة الواجهة"""
        layout = QVBoxLayout()
        
        # العنوان
        header = QLabel('💰 إدارة الديون والمبيعات الآجلة')
        header.setFont(QFont('Arial', 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 15px; background: #ecf0f1;")
        layout.addWidget(header)
        
        # إحصائيات عامة
        self.stats_layout = QHBoxLayout()
        layout.addLayout(self.stats_layout)
        
        # التبويبات
        self.tabs = QTabWidget()
        
        # ✅ التاب الرئيسي: التسجيل السريع
        self.tabs.addTab(QuickCreditView(self.db_path, self), '⚡ تسجيل فاتورة')
        
        # باقي التبويبات للتفاصيل
        self.tabs.addTab(self.create_customers_tab(), '👥 الزبائن')
        self.tabs.addTab(self.create_overdue_tab(), '⚠️ المتأخرون')
        
        layout.addWidget(self.tabs)
        
        self.setLayout(layout)
    
    def create_customers_tab(self):
        """تبويب الزبائن"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # أزرار الإدارة
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton('➕ إضافة زبون جديد')
        add_btn.clicked.connect(self.add_customer_dialog)
        add_btn.setStyleSheet("background: #27ae60; color: white; padding: 10px; font-size: 14px;")
        btn_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton('🔄 تحديث')
        refresh_btn.clicked.connect(self.load_data)
        refresh_btn.setStyleSheet("background: #3498db; color: white; padding: 10px;")
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        
        # البحث
        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText('🔍 البحث بالاسم أو التليفون...')
        self.customer_search.textChanged.connect(self.search_customers)
        btn_layout.addWidget(self.customer_search)
        
        layout.addLayout(btn_layout)
        
        # جدول الزبائن
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(7)
        self.customers_table.setHorizontalHeaderLabels([
            'الاسم', 'التليفون', 'إجمالي الدين', 'عدد الفواتير', 
            'الحالة', 'التفاصيل', 'حذف'
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.customers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.customers_table.setStyleSheet("""
            QTableWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        layout.addWidget(self.customers_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_overdue_tab(self):
        """تبويب المتأخرون في السداد"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        alert = QLabel('⚠️ الزبائن المتأخرون في السداد')
        alert.setFont(QFont('Arial', 14, QFont.Bold))
        alert.setStyleSheet("color: #e74c3c; padding: 10px;")
        layout.addWidget(alert)
        
        self.overdue_table = QTableWidget()
        self.overdue_table.setColumnCount(7)
        self.overdue_table.setHorizontalHeaderLabels([
            'الزبون', 'التليفون', 'رقم الفاتورة', 'المبلغ المتبقي',
            'تاريخ الاستحقاق', 'أيام التأخير', 'إجراء'
        ])
        self.overdue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.overdue_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.overdue_table)
        
        widget.setLayout(layout)
        return widget
    
    def load_data(self):
        """تحميل جميع البيانات"""
        self.load_stats()
        self.load_customers()
        self.load_overdue()
    
    def load_stats(self):
        """تحميل الإحصائيات"""
        # مسح الإحصائيات القديمة
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        stats = self.controller.get_dashboard_stats()
        
        self.stats_layout.addWidget(self.create_stat_card(
            'إجمالي الديون', f"{stats['total_debt']:.2f} ج", '#e74c3c'
        ))
        self.stats_layout.addWidget(self.create_stat_card(
            'عدد المديونين', str(stats['debtors_count']), '#3498db'
        ))
        self.stats_layout.addWidget(self.create_stat_card(
            'ديون متأخرة +30', f"{stats['overdue_30']:.2f} ج", '#f39c12'
        ))
        self.stats_layout.addWidget(self.create_stat_card(
            'ديون حرجة +60', f"{stats['overdue_60']:.2f} ج", '#c0392b'
        ))
    
    def create_stat_card(self, title, value, color):
        """إنشاء بطاقة إحصائية"""
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
        value_label.setFont(QFont('Arial', 16, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color: white;")
        
        layout.addWidget(value_label)
        group.setLayout(layout)
        return group
    
    def load_customers(self):
        """تحميل جدول الزبائن"""
        customers = self.controller.get_all_customers()
        
        self.customers_table.setRowCount(0)
        for customer in customers:
            row = self.customers_table.rowCount()
            self.customers_table.insertRow(row)
            
            # البيانات
            self.customers_table.setItem(row, 0, QTableWidgetItem(customer['name']))
            self.customers_table.setItem(row, 1, QTableWidgetItem(customer['phone'] or ''))
            self.customers_table.setItem(row, 2, QTableWidgetItem(f"{customer['total_debt']:.2f} ج"))
            self.customers_table.setItem(row, 3, QTableWidgetItem(str(customer['invoice_count'])))
            
            # الحالة
            status_map = {
                'reliable': '✅ موثوق',
                'normal': '⚪ عادي',
                'late': '⚠️ متأخر'
            }
            status_item = QTableWidgetItem(status_map.get(customer['status'], '⚪ عادي'))
            if customer['status'] == 'late':
                status_item.setBackground(QColor(255, 230, 230))
            self.customers_table.setItem(row, 4, status_item)
            
            # زر التفاصيل
            details_btn = QPushButton('📋 عرض')
            details_btn.clicked.connect(
                lambda checked, cid=customer['customer_id']: 
                self.show_customer_details(cid)
            )
            details_btn.setStyleSheet("background: #3498db; color: white; padding: 5px;")
            self.customers_table.setCellWidget(row, 5, details_btn)
            
            # زر الحذف
            delete_btn = QPushButton('🗑️')
            delete_btn.clicked.connect(
                lambda checked, cid=customer['customer_id']: 
                self.delete_customer(cid)
            )
            delete_btn.setStyleSheet("background: #e74c3c; color: white; padding: 5px;")
            self.customers_table.setCellWidget(row, 6, delete_btn)
    
    def search_customers(self):
        """البحث عن زبائن"""
        search_term = self.customer_search.text().strip()
        
        if len(search_term) < 1:
            self.load_customers()
            return
        
        customers = self.controller.search_customers(search_term)
        
        self.customers_table.setRowCount(0)
        for customer in customers:
            row = self.customers_table.rowCount()
            self.customers_table.insertRow(row)
            
            self.customers_table.setItem(row, 0, QTableWidgetItem(customer['name']))
            self.customers_table.setItem(row, 1, QTableWidgetItem(customer['phone'] or ''))
            self.customers_table.setItem(row, 2, QTableWidgetItem(f"{customer['total_debt']:.2f} ج"))
            
            details_btn = QPushButton('📋 عرض')
            details_btn.clicked.connect(
                lambda checked, cid=customer['customer_id']: 
                self.show_customer_details(cid)
            )
            details_btn.setStyleSheet("background: #3498db; color: white; padding: 5px;")
            self.customers_table.setCellWidget(row, 5, details_btn)
    
    def load_overdue(self):
        """تحميل المتأخرون في السداد"""
        invoices = self.controller.get_overdue_invoices()
        
        self.overdue_table.setRowCount(0)
        for invoice in invoices:
            row = self.overdue_table.rowCount()
            self.overdue_table.insertRow(row)
            
            days_overdue = int(invoice['days_overdue'])
            
            # لون الصف حسب التأخير
            bg_color = QColor(255, 230, 230)
            if days_overdue > 60:
                bg_color = QColor(255, 200, 200)
            
            items = [
                QTableWidgetItem(invoice['customer_name']),
                QTableWidgetItem(invoice['customer_phone'] or ''),
                QTableWidgetItem(invoice['invoice_number']),
                QTableWidgetItem(f"{invoice['remaining_amount']:.2f} ج"),
                QTableWidgetItem(invoice['due_date']),
                QTableWidgetItem(f"{days_overdue} يوم"),
            ]
            
            for col, item in enumerate(items):
                item.setBackground(bg_color)
                self.overdue_table.setItem(row, col, item)
            
            # زر الإجراء
            action_btn = QPushButton('💰 تسجيل دفعة')
            action_btn.clicked.connect(
                lambda checked, iid=invoice['invoice_id'], 
                cid=invoice['customer_id']: 
                self.add_payment_dialog(cid, iid)
            )
            action_btn.setStyleSheet("background: #27ae60; color: white; padding: 5px;")
            self.overdue_table.setCellWidget(row, 6, action_btn)
    
    def add_customer_dialog(self):
        """نافذة إضافة زبون"""
        dialog = QDialog(self)
        dialog.setWindowTitle('إضافة زبون جديد')
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText('مثال: أحمد محمد')
        
        phone_input = QLineEdit()
        phone_input.setPlaceholderText('مثال: 01012345678')
        
        address_input = QLineEdit()
        address_input.setPlaceholderText('مثال: شارع النصر')
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        notes_input.setPlaceholderText('ملاحظات اختيارية...')
        
        credit_limit_input = QDoubleSpinBox()
        credit_limit_input.setMaximum(1000000)
        credit_limit_input.setValue(0)
        credit_limit_input.setSuffix(' جنيه')
        
        layout.addRow('الاسم *:', name_input)
        layout.addRow('التليفون:', phone_input)
        layout.addRow('العنوان:', address_input)
        layout.addRow('حد الائتمان:', credit_limit_input)
        layout.addRow('ملاحظات:', notes_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(lambda: self.save_customer(
            name_input.text(),
            phone_input.text(),
            address_input.text(),
            notes_input.toPlainText(),
            credit_limit_input.value(),
            dialog
        ))
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def save_customer(self, name, phone, address, notes, credit_limit, dialog):
        """حفظ الزبون"""
        if not name:
            QMessageBox.warning(self, 'خطأ', 'الاسم مطلوب!')
            return
        
        success, customer_id, message = self.controller.add_customer(
            name, phone or None, address or None, 
            notes or None, credit_limit
        )
        
        if success:
            QMessageBox.information(self, 'نجح ✅', message)
            dialog.accept()
            self.load_data()
        else:
            QMessageBox.warning(self, 'خطأ', message)
    
    def delete_customer(self, customer_id):
        """حذف زبون"""
        reply = QMessageBox.question(
            self, 'تأكيد الحذف',
            'هل تريد حذف هذا الزبون？\n'
            'سيتم حذف جميع سجلاته أيضاً!',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.controller.delete_customer(customer_id)
            
            if success:
                QMessageBox.information(self, 'تم الحذف', message)
                self.load_data()
            else:
                QMessageBox.warning(self, 'خطأ', message)
    
    def show_customer_details(self, customer_id):
        """عرض تفاصيل زبون"""
        dialog = CustomerDetailsDialog(customer_id, self.db_path, self)
        dialog.exec_()
        self.load_data()  # تحديث البيانات بعد الإغلاق
    
    def add_payment_dialog(self, customer_id, invoice_id):
        """نافذة تسجيل دفعة"""
        dialog = AddPaymentDialog(customer_id, invoice_id, self.db_path, self)
        if dialog.exec_():
            self.load_data()
