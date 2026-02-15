#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة محل زفرية - نظام كامل
Zafrya Store Management System
"""

import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox, QTabWidget,
    QGroupBox, QFormLayout, QDialog, QDialogButtonBox, QHeaderView,
    QTextEdit, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

class Database:
    """إدارة قاعدة البيانات"""
    def __init__(self, db_path='zafrya_store.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                size TEXT,
                manufacturer TEXT,
                purchase_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                current_stock INTEGER DEFAULT 0,
                min_stock_alert INTEGER DEFAULT 5
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                total_profit REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_code TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                purchase_price REAL NOT NULL,
                subtotal REAL NOT NULL,
                item_profit REAL NOT NULL
            )
        """)

        # إضافة بيانات تجريبية
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ('ش42DC', 'شبشب DC مقاس 42', 'شباشب', '42', 'DC', 80.0, 120.0, 25),
                ('ش40AB', 'شبشب Adidas مقاس 40', 'شباشب', '40', 'Adidas', 100.0, 150.0, 15),
                ('د38A4', 'دفتر A4 38 ورقة', 'أدوات مدرسية', '', 'مصر', 15.0, 25.0, 50),
                ('ق40SB', 'قميص رجالي مقاس 40', 'ملابس', '40', 'LC', 150.0, 220.0, 10),
            ]
            cursor.executemany("""
                INSERT INTO products (product_code, product_name, category, size, 
                                    manufacturer, purchase_price, selling_price, current_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_products)

        conn.commit()
        conn.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.cart_items = []
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setWindowTitle('نظام إدارة محل زفرية - نظام كامل')
        self.setGeometry(50, 50, 1400, 800)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        # العنوان
        title = QLabel('🏪 نظام إدارة محل زفرية')
        title.setFont(QFont('Arial', 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 15px; background: #ecf0f1;")
        layout.addWidget(title)

        # التبويبات
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont('Arial', 11))

        self.tabs.addTab(self.create_dashboard_tab(), '📊 لوحة التحكم')
        self.tabs.addTab(self.create_pos_tab(), '🛒 نقطة البيع')
        self.tabs.addTab(self.create_products_tab(), '📦 المنتجات')
        self.tabs.addTab(self.create_inventory_tab(), '🗃️ المخزون')
        self.tabs.addTab(self.create_reports_tab(), '📈 التقارير')

        layout.addWidget(self.tabs)

        central.setLayout(layout)
        self.statusBar().showMessage('النظام جاهز ✅')

    def create_dashboard_tab(self):
        """لوحة التحكم"""
        widget = QWidget()
        layout = QVBoxLayout()

        # إحصائيات اليوم
        stats_layout = QHBoxLayout()

        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        # عدد الفواتير اليوم
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_amount), 0), COALESCE(SUM(total_profit), 0) FROM sales WHERE DATE(sale_date) = DATE('now')")
        sales_count, total_sales, total_profit = cursor.fetchone()

        # قيمة المخزون
        cursor.execute("SELECT COALESCE(SUM(current_stock * purchase_price), 0) FROM products")
        inventory_value = cursor.fetchone()[0]

        # عدد المنتجات المنخفضة
        cursor.execute("SELECT COUNT(*) FROM products WHERE current_stock <= min_stock_alert")
        low_stock = cursor.fetchone()[0]

        conn.close()

        stats_layout.addWidget(self.create_stat_card('عدد الفواتير اليوم', str(sales_count), '#3498db'))
        stats_layout.addWidget(self.create_stat_card('إجمالي المبيعات', f'{total_sales:.2f} ج', '#2ecc71'))
        stats_layout.addWidget(self.create_stat_card('صافي الربح', f'{total_profit:.2f} ج', '#f39c12'))
        stats_layout.addWidget(self.create_stat_card('قيمة المخزون', f'{inventory_value:.2f} ج', '#9b59b6'))
        stats_layout.addWidget(self.create_stat_card('تنبيهات المخزون', str(low_stock), '#e74c3c'))

        layout.addLayout(stats_layout)

        # جدول المنتجات المنخفضة
        low_stock_label = QLabel('⚠️ تنبيهات المخزون المنخفض')
        low_stock_label.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(low_stock_label)

        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(6)
        self.low_stock_table.setHorizontalHeaderLabels(['الكود', 'اسم المنتج', 'الفئة', 'المخزون', 'الحد الأدنى', 'الحالة'])
        self.low_stock_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.low_stock_table)

        widget.setLayout(layout)
        return widget

    def create_stat_card(self, title, value, color):
        """إنشاء بطاقة إحصائية"""
        group = QGroupBox(title)
        group.setStyleSheet(f"QGroupBox {{ font-weight: bold; background: {color}; color: white; padding: 10px; border-radius: 5px; }}")
        layout = QVBoxLayout()

        value_label = QLabel(value)
        value_label.setFont(QFont('Arial', 18, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color: white;")

        layout.addWidget(value_label)
        group.setLayout(layout)
        return group

    def create_pos_tab(self):
        """نقطة البيع"""
        widget = QWidget()
        main_layout = QHBoxLayout()

        # الجانب الأيسر - البحث والمنتجات
        left_layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('🔍 بحث:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('ابحث بالكود أو الاسم...')
        self.search_input.returnPressed.connect(self.search_products)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton('بحث')
        search_btn.clicked.connect(self.search_products)
        search_btn.setStyleSheet("background: #3498db; color: white; padding: 8px;")
        search_layout.addWidget(search_btn)

        left_layout.addLayout(search_layout)

        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(7)
        self.search_results_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'السعر', 'المخزون', 'الكمية', 'إضافة', ''])
        self.search_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        left_layout.addWidget(self.search_results_table)

        # الجانب الأيمن - السلة
        right_layout = QVBoxLayout()

        cart_label = QLabel('🛒 سلة المشتريات')
        cart_label.setFont(QFont('Arial', 14, QFont.Bold))
        right_layout.addWidget(cart_label)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'السعر', 'الكمية', 'الإجمالي', 'حذف'])
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        right_layout.addWidget(self.cart_table)

        # الإجمالي
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel('الإجمالي:'))
        self.total_label = QLabel('0.00 جنيه')
        self.total_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.total_label.setStyleSheet("color: #27ae60;")
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()
        right_layout.addLayout(total_layout)

        # الأزرار
        btn_layout = QHBoxLayout()

        complete_btn = QPushButton('✅ إتمام البيع')
        complete_btn.clicked.connect(self.complete_sale)
        complete_btn.setStyleSheet("background: #27ae60; color: white; font-size: 16px; padding: 15px; font-weight: bold;")
        btn_layout.addWidget(complete_btn)

        clear_btn = QPushButton('🗑️ مسح السلة')
        clear_btn.clicked.connect(self.clear_cart)
        clear_btn.setStyleSheet("background: #e74c3c; color: white; font-size: 16px; padding: 15px; font-weight: bold;")
        btn_layout.addWidget(clear_btn)

        right_layout.addLayout(btn_layout)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)

        widget.setLayout(main_layout)
        return widget

    def create_products_tab(self):
        """إدارة المنتجات"""
        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()

        add_btn = QPushButton('➕ إضافة منتج جديد')
        add_btn.clicked.connect(self.add_product_dialog)
        add_btn.setStyleSheet("background: #27ae60; color: white; padding: 10px; font-size: 14px;")
        btn_layout.addWidget(add_btn)

        refresh_btn = QPushButton('🔄 تحديث')
        refresh_btn.clicked.connect(self.load_products_table)
        refresh_btn.setStyleSheet("background: #3498db; color: white; padding: 10px;")
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(9)
        self.products_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'الفئة', 'المقاس', 'الشركة', 'سعر الشراء', 'سعر البيع', 'المخزون', 'حذف'])
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.products_table)

        widget.setLayout(layout)
        return widget

    def create_inventory_tab(self):
        """المخزون"""
        widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel('📊 حالة المخزون الحالية')
        label.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(label)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'الفئة', 'سعر الشراء', 'سعر البيع', 'الكمية', 'القيمة'])
        self.inventory_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.inventory_table)

        widget.setLayout(layout)
        return widget

    def create_reports_tab(self):
        """التقارير"""
        widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel('📈 تقارير المبيعات والأرباح')
        label.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(label)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont('Courier New', 11))
        layout.addWidget(self.report_text)

        generate_btn = QPushButton('📊 إنشاء تقرير اليوم')
        generate_btn.clicked.connect(self.generate_daily_report)
        generate_btn.setStyleSheet("background: #9b59b6; color: white; padding: 12px; font-size: 14px;")
        layout.addWidget(generate_btn)

        widget.setLayout(layout)
        return widget

    def load_data(self):
        """تحميل البيانات"""
        self.load_low_stock_table()
        self.load_products_table()
        self.load_inventory_table()
        self.generate_daily_report()

    def load_low_stock_table(self):
        """تحميل جدول المنتجات المنخفضة"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_code, product_name, category, current_stock, min_stock_alert FROM products WHERE current_stock <= min_stock_alert")

        self.low_stock_table.setRowCount(0)
        for row_data in cursor.fetchall():
            row = self.low_stock_table.rowCount()
            self.low_stock_table.insertRow(row)

            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if row_data[3] == 0:
                    item.setBackground(QColor(255, 200, 200))
                self.low_stock_table.setItem(row, col, item)

            status = 'نفذ ⛔' if row_data[3] == 0 else 'منخفض ⚠️'
            self.low_stock_table.setItem(row, 5, QTableWidgetItem(status))

        conn.close()

    def load_products_table(self):
        """تحميل جدول المنتجات"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, product_code, product_name, category, size, manufacturer, purchase_price, selling_price, current_stock FROM products")

        self.products_table.setRowCount(0)
        for row_data in cursor.fetchall():
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)

            for col, value in enumerate(row_data[1:], 0):
                self.products_table.setItem(row, col, QTableWidgetItem(str(value or '')))

            del_btn = QPushButton('🗑️')
            del_btn.clicked.connect(lambda checked, pid=row_data[0]: self.delete_product(pid))
            del_btn.setStyleSheet("background: #e74c3c; color: white;")
            self.products_table.setCellWidget(row, 8, del_btn)

        conn.close()

    def load_inventory_table(self):
        """تحميل جدول المخزون"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_code, product_name, category, purchase_price, selling_price, current_stock FROM products")

        self.inventory_table.setRowCount(0)
        for row_data in cursor.fetchall():
            row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row)

            for col, value in enumerate(row_data):
                self.inventory_table.setItem(row, col, QTableWidgetItem(str(value)))

            value = row_data[3] * row_data[5]
            self.inventory_table.setItem(row, 6, QTableWidgetItem(f'{value:.2f}'))

        conn.close()

    def search_products(self):
        """البحث عن منتجات"""
        search_term = self.search_input.text().strip()
        if not search_term:
            return

        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM products 
            WHERE product_code LIKE ? OR product_name LIKE ?
        """, (f'%{search_term}%', f'%{search_term}%'))

        self.search_results_table.setRowCount(0)

        for row_data in cursor.fetchall():
            row = self.search_results_table.rowCount()
            self.search_results_table.insertRow(row)

            self.search_results_table.setItem(row, 0, QTableWidgetItem(row_data['product_code']))
            self.search_results_table.setItem(row, 1, QTableWidgetItem(row_data['product_name']))
            self.search_results_table.setItem(row, 2, QTableWidgetItem(f"{row_data['selling_price']:.2f}"))
            self.search_results_table.setItem(row, 3, QTableWidgetItem(str(row_data['current_stock'])))

            qty_spin = QSpinBox()
            qty_spin.setMinimum(1)
            qty_spin.setMaximum(row_data['current_stock'])
            qty_spin.setValue(1)
            self.search_results_table.setCellWidget(row, 4, qty_spin)

            add_btn = QPushButton('➕ إضافة')
            add_btn.clicked.connect(lambda checked, r=row_data, sp=qty_spin: self.add_to_cart(dict(r), sp.value()))
            add_btn.setStyleSheet("background: #27ae60; color: white; padding: 5px;")
            self.search_results_table.setCellWidget(row, 5, add_btn)

        conn.close()

    def add_to_cart(self, product, quantity):
        """إضافة منتج للسلة"""
        if quantity > product['current_stock']:
            QMessageBox.warning(self, 'تحذير', 'الكمية المطلوبة أكبر من المخزون!')
            return

        for item in self.cart_items:
            if item['product_id'] == product['product_id']:
                item['quantity'] += quantity
                self.refresh_cart()
                return

        self.cart_items.append({
            'product_id': product['product_id'],
            'product_code': product['product_code'],
            'product_name': product['product_name'],
            'unit_price': product['selling_price'],
            'purchase_price': product['purchase_price'],
            'quantity': quantity
        })

        self.refresh_cart()
        self.search_input.clear()
        self.search_results_table.setRowCount(0)

    def refresh_cart(self):
        """تحديث السلة"""
        self.cart_table.setRowCount(0)
        total = 0

        for i, item in enumerate(self.cart_items):
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)

            subtotal = item['quantity'] * item['unit_price']
            total += subtotal

            self.cart_table.setItem(row, 0, QTableWidgetItem(item['product_code']))
            self.cart_table.setItem(row, 1, QTableWidgetItem(item['product_name']))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"{item['unit_price']:.2f}"))
            self.cart_table.setItem(row, 3, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"{subtotal:.2f}"))

            del_btn = QPushButton('🗑️')
            del_btn.clicked.connect(lambda checked, idx=i: self.remove_from_cart(idx))
            del_btn.setStyleSheet("background: #e74c3c; color: white;")
            self.cart_table.setCellWidget(row, 5, del_btn)

        self.total_label.setText(f'{total:.2f} جنيه')

    def remove_from_cart(self, index):
        """حذف من السلة"""
        del self.cart_items[index]
        self.refresh_cart()

    def clear_cart(self):
        """مسح السلة"""
        self.cart_items = []
        self.refresh_cart()

    def complete_sale(self):
        """إتمام عملية البيع"""
        if not self.cart_items:
            QMessageBox.warning(self, 'تحذير', 'السلة فارغة!')
            return

        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        try:
            total_amount = sum(item['quantity'] * item['unit_price'] for item in self.cart_items)
            total_profit = sum(item['quantity'] * (item['unit_price'] - item['purchase_price']) for item in self.cart_items)

            cursor.execute("INSERT INTO sales (total_amount, total_profit) VALUES (?, ?)", (total_amount, total_profit))
            sale_id = cursor.lastrowid

            for item in self.cart_items:
                subtotal = item['quantity'] * item['unit_price']
                profit = item['quantity'] * (item['unit_price'] - item['purchase_price'])

                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_id, product_code, product_name, 
                                          quantity, unit_price, purchase_price, subtotal, item_profit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sale_id, item['product_id'], item['product_code'], item['product_name'],
                     item['quantity'], item['unit_price'], item['purchase_price'], subtotal, profit))

                cursor.execute("UPDATE products SET current_stock = current_stock - ? WHERE product_id = ?",
                             (item['quantity'], item['product_id']))

            conn.commit()

            QMessageBox.information(self, 'نجح ✅', 
                                  f'تمت عملية البيع بنجاح!\n'
                                  f'رقم الفاتورة: {sale_id}\n'
                                  f'الإجمالي: {total_amount:.2f} جنيه\n'
                                  f'الربح: {total_profit:.2f} جنيه')

            self.cart_items = []
            self.refresh_cart()
            self.load_data()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, 'خطأ', f'فشلت عملية البيع:\n{str(e)}')
        finally:
            conn.close()

    def add_product_dialog(self):
        """حوار إضافة منتج"""
        dialog = QDialog(self)
        dialog.setWindowTitle('إضافة منتج جديد')
        dialog.setModal(True)

        layout = QFormLayout()

        code_input = QLineEdit()
        name_input = QLineEdit()
        category_input = QComboBox()
        category_input.addItems(['أدوات مدرسية', 'ملابس', 'شباشب', 'أخرى'])
        category_input.setEditable(True)
        size_input = QLineEdit()
        manufacturer_input = QLineEdit()
        purchase_price_input = QDoubleSpinBox()
        purchase_price_input.setMaximum(100000)
        purchase_price_input.setDecimals(2)
        selling_price_input = QDoubleSpinBox()
        selling_price_input.setMaximum(100000)
        selling_price_input.setDecimals(2)
        stock_input = QSpinBox()
        stock_input.setMaximum(100000)

        layout.addRow('الكود:', code_input)
        layout.addRow('الاسم:', name_input)
        layout.addRow('الفئة:', category_input)
        layout.addRow('المقاس:', size_input)
        layout.addRow('الشركة:', manufacturer_input)
        layout.addRow('سعر الشراء:', purchase_price_input)
        layout.addRow('سعر البيع:', selling_price_input)
        layout.addRow('الكمية:', stock_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self.save_product(
            code_input.text(), name_input.text(), category_input.currentText(),
            size_input.text(), manufacturer_input.text(),
            purchase_price_input.value(), selling_price_input.value(),
            stock_input.value(), dialog
        ))
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_product(self, code, name, category, size, manufacturer, purchase_price, selling_price, stock, dialog):
        """حفظ منتج جديد"""
        if not code or not name:
            QMessageBox.warning(self, 'خطأ', 'الكود والاسم مطلوبان!')
            return

        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO products (product_code, product_name, category, size, manufacturer,
                                    purchase_price, selling_price, current_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, category, size, manufacturer, purchase_price, selling_price, stock))

            conn.commit()
            QMessageBox.information(self, 'نجح', 'تم إضافة المنتج بنجاح!')
            dialog.accept()
            self.load_products_table()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, 'خطأ', 'الكود موجود مسبقاً!')
        finally:
            conn.close()

    def delete_product(self, product_id):
        """حذف منتج"""
        reply = QMessageBox.question(self, 'تأكيد', 'هل تريد حذف هذا المنتج؟',
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
            conn.commit()
            conn.close()

            self.load_products_table()
            QMessageBox.information(self, 'نجح', 'تم حذف المنتج')

    def generate_daily_report(self):
        """إنشاء تقرير يومي"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0), COALESCE(SUM(total_profit), 0)
            FROM sales WHERE DATE(sale_date) = DATE('now')
        """)
        sales_count, total_sales, total_profit = cursor.fetchone()

        cursor.execute("""
            SELECT si.product_name, SUM(si.quantity) as qty, SUM(si.subtotal) as revenue
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE DATE(s.sale_date) = DATE('now')
            GROUP BY si.product_id
            ORDER BY qty DESC
            LIMIT 5
        """)
        best_sellers = cursor.fetchall()

        conn.close()

        report = f"""
{'='*60}
        تقرير مبيعات اليوم - {datetime.now().strftime('%Y-%m-%d')}
{'='*60}

📊 الملخص العام:
   • عدد الفواتير: {sales_count}
   • إجمالي المبيعات: {total_sales:.2f} جنيه
   • صافي الربح: {total_profit:.2f} جنيه
   • متوسط الفاتورة: {(total_sales / sales_count if sales_count > 0 else 0):.2f} جنيه

{'='*60}
🏆 أفضل المنتجات مبيعاً:

"""

        for i, (name, qty, revenue) in enumerate(best_sellers, 1):
            report += f"   {i}. {name}\n"
            report += f"      الكمية: {qty} | الإيرادات: {revenue:.2f} ج\n\n"

        if not best_sellers:
            report += "   لا توجد مبيعات اليوم\n"

        report += "\n" + "="*60

        self.report_text.setPlainText(report)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
