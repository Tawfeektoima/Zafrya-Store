#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة محل زفرية - النسخة المحدثة
Zafrya Store Management System - Fixed Version
"""

import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox, QTabWidget,
    QGroupBox, QFormLayout, QDialog, QDialogButtonBox, QHeaderView,
    QTextEdit, QDateEdit, QCompleter
)
from PyQt5.QtCore import Qt, QDate, QStringListModel
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
                min_stock_alert INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                ('ش38DC', 'شبشب DC مقاس 38', 'شباشب', '38', 'DC', 75.0, 115.0, 30),
                ('د38A4', 'دفتر A4 38 ورقة', 'أدوات مدرسية', '', 'مصر', 15.0, 25.0, 50),
                ('د50A5', 'دفتر A5 50 ورقة', 'أدوات مدرسية', '', 'مصر', 18.0, 30.0, 40),
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

        # تحديث لوحة التحكم تلقائياً كل 5 ثواني
        from PyQt5.QtCore import QTimer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(3000)  # كل 5 ثواني

    def init_ui(self):
        self.setWindowTitle('نظام إدارة محل الظافرية')
        self.setGeometry(50, 50, 1400, 800)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        # العنوان
        title = QLabel('🏪 نظام إدارة محل ظافرية')
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
        self.statusBar().showMessage('النظام جاهز ✅ | آخر تحديث: ' + datetime.now().strftime('%H:%M:%S'))

    def create_dashboard_tab(self):
        """لوحة التحكم"""
        widget = QWidget()
        self.dashboard_layout = QVBoxLayout()

        # سيتم ملء المحتوى في refresh_dashboard
        self.dashboard_stats_layout = QHBoxLayout()
        self.dashboard_layout.addLayout(self.dashboard_stats_layout)

        # جدول المنتجات المنخفضة
        low_stock_label = QLabel('⚠️ تنبيهات المخزون المنخفض')
        low_stock_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.dashboard_layout.addWidget(low_stock_label)

        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(6)
        self.low_stock_table.setHorizontalHeaderLabels(['الكود', 'اسم المنتج', 'الفئة', 'المخزون', 'الحد الأدنى', 'الحالة'])
        self.low_stock_table.horizontalHeader().setStretchLastSection(True)
        self.dashboard_layout.addWidget(self.low_stock_table)

        # زر التحديث اليدوي
        refresh_btn = QPushButton('🔄 تحديث البيانات')
        refresh_btn.clicked.connect(self.refresh_dashboard)
        refresh_btn.setStyleSheet("background: #3498db; color: white; padding: 10px; font-size: 14px;")
        self.dashboard_layout.addWidget(refresh_btn)

        widget.setLayout(self.dashboard_layout)
        return widget

    def refresh_dashboard(self):
        """تحديث لوحة التحكم"""
        # مسح البطاقات القديمة
        while self.dashboard_stats_layout.count():
            child = self.dashboard_stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

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

        # إضافة البطاقات الجديدة
        self.dashboard_stats_layout.addWidget(self.create_stat_card('عدد الفواتير اليوم', str(sales_count), '#3498db'))
        self.dashboard_stats_layout.addWidget(self.create_stat_card('إجمالي المبيعات', f'{total_sales:.2f} ج', '#2ecc71'))
        self.dashboard_stats_layout.addWidget(self.create_stat_card('صافي الربح', f'{total_profit:.2f} ج', '#f39c12'))
        self.dashboard_stats_layout.addWidget(self.create_stat_card('قيمة المخزون', f'{inventory_value:.2f} ج', '#9b59b6'))
        self.dashboard_stats_layout.addWidget(self.create_stat_card('تنبيهات المخزون', str(low_stock), '#e74c3c'))

        # تحديث جدول المنتجات المنخفضة
        self.load_low_stock_table()

        # تحديث شريط الحالة
        self.statusBar().showMessage('✅ تم التحديث | الوقت: ' + datetime.now().strftime('%H:%M:%S'))

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
        """نقطة البيع مع بحث تلقائي"""
        widget = QWidget()
        main_layout = QHBoxLayout()

        # الجانب الأيسر - البحث والمنتجات
        left_layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('🔍 بحث تلقائي:'))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('اكتب للبحث التلقائي (مثل: DC, دفتر, شبشب)...')

        # إضافة البحث التلقائي
        self.search_input.textChanged.connect(self.live_search_products)

        search_layout.addWidget(self.search_input)

        left_layout.addLayout(search_layout)

        # جدول نتائج البحث
        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(7)
        self.search_results_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'الفئة', 'السعر', 'المخزون', 'الكمية', 'إضافة'])
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
        refresh_btn.clicked.connect(self.load_all_data)
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

        btn_layout = QHBoxLayout()

        label = QLabel('📊 حالة المخزون الحالية')
        label.setFont(QFont('Arial', 14, QFont.Bold))
        btn_layout.addWidget(label)

        btn_layout.addStretch()

        refresh_btn = QPushButton('🔄 تحديث المخزون')
        refresh_btn.clicked.connect(self.load_inventory_table)
        refresh_btn.setStyleSheet("background: #3498db; color: white; padding: 8px;")
        btn_layout.addWidget(refresh_btn)

        layout.addLayout(btn_layout)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'الفئة', 'سعر الشراء', 'سعر البيع', 'الكمية', 'القيمة'])
        self.inventory_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.inventory_table)

        widget.setLayout(layout)
        return widget

    def create_reports_tab(self):
        """التقارير المحسنة"""
        widget = QWidget()
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        label = QLabel('📈 تقارير المبيعات والأرباح')
        label.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(label)
        header_layout.addStretch()

        generate_btn = QPushButton('📊 تحديث التقرير')
        generate_btn.clicked.connect(self.generate_daily_report)
        generate_btn.setStyleSheet("background: #9b59b6; color: white; padding: 10px; font-size: 13px;")
        header_layout.addWidget(generate_btn)

        layout.addLayout(header_layout)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont('Courier New', 11))
        self.report_text.setStyleSheet("background: #2c3e50; color: #ecf0f1; padding: 15px;")
        layout.addWidget(self.report_text)

        widget.setLayout(layout)
        return widget

    def load_data(self):
        """تحميل جميع البيانات"""
        self.refresh_dashboard()
        self.load_products_table()
        self.load_inventory_table()
        self.generate_daily_report()

    def load_all_data(self):
        """تحديث جميع الصفحات"""
        self.load_data()
        QMessageBox.information(self, 'تم التحديث', 'تم تحديث جميع البيانات بنجاح ✅')

    def load_low_stock_table(self):
        """تحميل جدول المنتجات المنخفضة"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_code, product_name, category, current_stock, min_stock_alert FROM products WHERE current_stock <= min_stock_alert ORDER BY current_stock ASC")

        self.low_stock_table.setRowCount(0)
        for row_data in cursor.fetchall():
            row = self.low_stock_table.rowCount()
            self.low_stock_table.insertRow(row)

            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if row_data[3] == 0:
                    item.setBackground(QColor(255, 200, 200))
                elif row_data[3] <= 5:
                    item.setBackground(QColor(255, 235, 200))
                self.low_stock_table.setItem(row, col, item)

            status = 'نفذ ⛔' if row_data[3] == 0 else 'منخفض ⚠️'
            status_item = QTableWidgetItem(status)
            if row_data[3] == 0:
                status_item.setBackground(QColor(255, 200, 200))
            self.low_stock_table.setItem(row, 5, status_item)

        conn.close()

    def load_products_table(self):
        """تحميل جدول المنتجات"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, product_code, product_name, category, size, manufacturer, purchase_price, selling_price, current_stock FROM products ORDER BY product_name")

        self.products_table.setRowCount(0)
        for row_data in cursor.fetchall():
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)

            for col, value in enumerate(row_data[1:], 0):
                self.products_table.setItem(row, col, QTableWidgetItem(str(value or '')))

            del_btn = QPushButton('🗑️')
            del_btn.clicked.connect(lambda checked, pid=row_data[0]: self.delete_product(pid))
            del_btn.setStyleSheet("background: #e74c3c; color: white; padding: 3px;")
            self.products_table.setCellWidget(row, 8, del_btn)

        conn.close()

    def load_inventory_table(self):
        """تحميل جدول المخزون - محدث"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_code, product_name, category, purchase_price, selling_price, current_stock FROM products ORDER BY category, product_name")

        self.inventory_table.setRowCount(0)
        for row_data in cursor.fetchall():
            row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row)

            for col, value in enumerate(row_data):
                self.inventory_table.setItem(row, col, QTableWidgetItem(str(value)))

            value = row_data[3] * row_data[5]
            self.inventory_table.setItem(row, 6, QTableWidgetItem(f'{value:.2f}'))

        conn.close()

    def live_search_products(self):
        """البحث التلقائي المباشر"""
        search_term = self.search_input.text().strip()

        if len(search_term) < 1:
            self.search_results_table.setRowCount(0)
            return

        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # بحث شامل في الكود، الاسم، الفئة، والشركة
        cursor.execute("""
            SELECT * FROM products 
            WHERE product_code LIKE ? 
               OR product_name LIKE ? 
               OR category LIKE ?
               OR manufacturer LIKE ?
            ORDER BY product_name
            LIMIT 20
        """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))

        self.search_results_table.setRowCount(0)

        for row_data in cursor.fetchall():
            row = self.search_results_table.rowCount()
            self.search_results_table.insertRow(row)

            self.search_results_table.setItem(row, 0, QTableWidgetItem(row_data['product_code']))
            self.search_results_table.setItem(row, 1, QTableWidgetItem(row_data['product_name']))
            self.search_results_table.setItem(row, 2, QTableWidgetItem(row_data['category']))
            self.search_results_table.setItem(row, 3, QTableWidgetItem(f"{row_data['selling_price']:.2f}"))
            self.search_results_table.setItem(row, 4, QTableWidgetItem(str(row_data['current_stock'])))

            qty_spin = QSpinBox()
            qty_spin.setMinimum(1)
            qty_spin.setMaximum(max(1, row_data['current_stock']))
            qty_spin.setValue(1)
            self.search_results_table.setCellWidget(row, 5, qty_spin)

            add_btn = QPushButton('➕ إضافة')
            add_btn.clicked.connect(lambda checked, r=row_data, sp=qty_spin: self.add_to_cart(dict(r), sp.value()))
            add_btn.setStyleSheet("background: #27ae60; color: white; padding: 5px; font-weight: bold;")
            self.search_results_table.setCellWidget(row, 6, add_btn)

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
            del_btn.setStyleSheet("background: #e74c3c; color: white; padding: 3px;")
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
                                  f'تمت عملية البيع بنجاح!\n\n'
                                  f'رقم الفاتورة: {sale_id}\n'
                                  f'الإجمالي: {total_amount:.2f} جنيه\n'
                                  f'الربح: {total_profit:.2f} جنيه')

            self.cart_items = []
            self.refresh_cart()
            self.load_data()  # تحديث كل البيانات

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
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        code_input = QLineEdit()
        code_input.setPlaceholderText('مثال: ش42DC')

        name_input = QLineEdit()
        name_input.setPlaceholderText('مثال: شبشب DC مقاس 42')

        category_input = QComboBox()
        category_input.addItems(['أدوات مدرسية', 'ملابس', 'شباشب', 'أخرى'])
        category_input.setEditable(True)

        size_input = QLineEdit()
        size_input.setPlaceholderText('مثال: 42')

        manufacturer_input = QLineEdit()
        manufacturer_input.setPlaceholderText('مثال: DC')

        purchase_price_input = QDoubleSpinBox()
        purchase_price_input.setMaximum(100000)
        purchase_price_input.setDecimals(2)
        purchase_price_input.setPrefix('ج ')

        selling_price_input = QDoubleSpinBox()
        selling_price_input.setMaximum(100000)
        selling_price_input.setDecimals(2)
        selling_price_input.setPrefix('ج ')

        stock_input = QSpinBox()
        stock_input.setMaximum(100000)
        stock_input.setSuffix(' قطعة')

        layout.addRow('الكود *:', code_input)
        layout.addRow('الاسم *:', name_input)
        layout.addRow('الفئة *:', category_input)
        layout.addRow('المقاس:', size_input)
        layout.addRow('الشركة:', manufacturer_input)
        layout.addRow('سعر الشراء *:', purchase_price_input)
        layout.addRow('سعر البيع *:', selling_price_input)
        layout.addRow('الكمية الأولية:', stock_input)

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

        if purchase_price <= 0 or selling_price <= 0:
            QMessageBox.warning(self, 'خطأ', 'الأسعار يجب أن تكون أكبر من صفر!')
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
            QMessageBox.information(self, 'نجح ✅', f'تم إضافة المنتج "{name}" بنجاح!')
            dialog.accept()

            # تحديث جميع الجداول
            self.load_products_table()
            self.load_inventory_table()
            self.refresh_dashboard()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, 'خطأ', f'الكود "{code}" موجود مسبقاً!')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'فشل حفظ المنتج:\n{str(e)}')
        finally:
            conn.close()

    def delete_product(self, product_id):
        """حذف منتج"""
        reply = QMessageBox.question(self, 'تأكيد الحذف', 
                                    'هل تريد حذف هذا المنتج نهائياً؟\nلا يمكن التراجع عن هذه العملية!',
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
            conn.commit()
            conn.close()

            self.load_products_table()
            self.load_inventory_table()
            self.refresh_dashboard()
            QMessageBox.information(self, 'تم الحذف', 'تم حذف المنتج بنجاح ✅')

    def generate_daily_report(self):
        """إنشاء تقرير يومي محسّن"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        # إحصائيات اليوم
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0), COALESCE(SUM(total_profit), 0)
            FROM sales WHERE DATE(sale_date) = DATE('now')
        """)
        sales_count, total_sales, total_profit = cursor.fetchone()

        # أفضل المنتجات
        cursor.execute("""
            SELECT si.product_name, si.product_code, SUM(si.quantity) as qty, 
                   SUM(si.subtotal) as revenue, SUM(si.item_profit) as profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE DATE(s.sale_date) = DATE('now')
            GROUP BY si.product_id
            ORDER BY qty DESC
            LIMIT 5
        """)
        best_sellers = cursor.fetchall()

        # آخر 5 فواتير
        cursor.execute("""
            SELECT sale_id, sale_date, total_amount, total_profit
            FROM sales
            WHERE DATE(sale_date) = DATE('now')
            ORDER BY sale_date DESC
            LIMIT 5
        """)
        recent_sales = cursor.fetchall()

        # إحصائيات المخزون
        cursor.execute("SELECT COUNT(*), SUM(current_stock), SUM(current_stock * purchase_price) FROM products")
        product_count, total_qty, inventory_value = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM products WHERE current_stock <= min_stock_alert")
        low_stock_count = cursor.fetchone()[0]

        conn.close()

        # تنسيق التقرير المحسّن
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                     📊 تقرير مبيعات اليوم                          ║
║                  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}                   ║
╚══════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────┐
│ 📈 ملخص المبيعات اليومية                                          │
└─────────────────────────────────────────────────────────────────────┘

  💰 إجمالي المبيعات:        {total_sales:>12.2f} جنيه
  💵 صافي الربح:             {total_profit:>12.2f} جنيه
  📋 عدد الفواتير:           {sales_count:>12} فاتورة
  📊 متوسط الفاتورة:         {(total_sales / sales_count if sales_count > 0 else 0):>12.2f} جنيه
  📈 هامش الربح:             {((total_profit / total_sales * 100) if total_sales > 0 else 0):>11.1f} %

┌─────────────────────────────────────────────────────────────────────┐
│ 🏆 أفضل 5 منتجات مبيعاً                                           │
└─────────────────────────────────────────────────────────────────────┘
"""

        if best_sellers:
            for i, (name, code, qty, revenue, profit) in enumerate(best_sellers, 1):
                report += f"""
  {i}. [{code}] {name}
     ├─ الكمية المباعة: {qty} قطعة
     ├─ الإيرادات: {revenue:.2f} جنيه
     └─ الربح: {profit:.2f} جنيه
"""
        else:
            report += "\n  ⚠️  لا توجد مبيعات حتى الآن\n"

        report += f"""
┌─────────────────────────────────────────────────────────────────────┐
│ 🧾 آخر الفواتير                                                    │
└─────────────────────────────────────────────────────────────────────┘
"""

        if recent_sales:
            for sale_id, sale_date, amount, profit in recent_sales:
                time_str = datetime.strptime(sale_date, '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
                report += f"  • فاتورة #{sale_id:<4} | {time_str} | {amount:>8.2f} ج | ربح: {profit:>6.2f} ج\n"
        else:
            report += "  ⚠️  لا توجد فواتير اليوم\n"

        report += f"""
┌─────────────────────────────────────────────────────────────────────┐
│ 📦 حالة المخزون                                                    │
└─────────────────────────────────────────────────────────────────────┘

  📊 عدد المنتجات:          {product_count:>12} منتج
  📦 إجمالي الكمية:         {total_qty:>12} قطعة
  💰 قيمة المخزون:          {inventory_value:>12.2f} جنيه
  ⚠️  تنبيهات المخزون:      {low_stock_count:>12} منتج

╔══════════════════════════════════════════════════════════════════════╗
║  تم إنشاء التقرير بواسطة: نظام محل زفرية                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

        self.report_text.setPlainText(report)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
