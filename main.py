#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة محل الظافرية - النسخة المحدثة
AlDhaferya Store Management System - Updated Version
"""

import sys
import sqlite3
import hashlib
import smtplib
import random
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox, QTabWidget,
    QGroupBox, QFormLayout, QDialog, QDialogButtonBox, QHeaderView,
    QTextEdit, QDateEdit, QCompleter, QInputDialog, QScrollArea, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtGui import QFont, QColor

# Matplotlib imports
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.font_manager as fm

class Database:
    """إدارة قاعدة البيانات"""
    def __init__(self, db_path='aldhaferya_store.db'):
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

        # جدول إعدادات النظام (لحفظ كلمة المرور والإيميل)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
        """)

        # تعيين كلمة مرور افتراضية (admin123 مشفرة)
        cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'analytics_password'")
        if cursor.fetchone() is None:
            default_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute("INSERT INTO system_settings VALUES ('analytics_password', ?)", (default_password,))

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

class AnalyticsProfitDialog(QDialog):
    """نافذة الأرباح والتحليلات المحمية بكلمة مرور"""
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle('📊 Analytics & Profits - تحليلات الأرباح')
        self.setMinimumSize(1200, 900)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # العنوان
        title = QLabel('📊 تحليلات الأرباح التفصيلية')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 15px; background: #ecf0f1;")
        main_layout.addWidget(title)

        # بطاقات الأرباح
        stats_layout = QHBoxLayout()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # أرباح اليوم
        cursor.execute("SELECT COALESCE(SUM(total_profit), 0) FROM sales WHERE DATE(sale_date) = DATE('now')")
        today_profit = cursor.fetchone()[0]

        # أرباح الشهر
        cursor.execute("SELECT COALESCE(SUM(total_profit), 0) FROM sales WHERE strftime('%Y-%m', sale_date) = strftime('%Y-%m', 'now')")
        month_profit = cursor.fetchone()[0]

        # إجمالي الأرباح
        cursor.execute("SELECT COALESCE(SUM(total_profit), 0) FROM sales")
        total_profit = cursor.fetchone()[0]

        # أرباح متوقعة من المخزون
        cursor.execute("SELECT COALESCE(SUM(current_stock * (selling_price - purchase_price)), 0) FROM products")
        expected_profit = cursor.fetchone()[0]

        conn.close()

        stats_layout.addWidget(self.create_profit_card('أرباح اليوم', f'{today_profit:.2f} ج', '#27ae60'))
        stats_layout.addWidget(self.create_profit_card('أرباح الشهر', f'{month_profit:.2f} ج', '#16a085'))
        stats_layout.addWidget(self.create_profit_card('إجمالي الأرباح', f'{total_profit:.2f} ج', '#f39c12'))
        stats_layout.addWidget(self.create_profit_card('أرباح متوقعة', f'{expected_profit:.2f} ج', '#9b59b6'))

        main_layout.addLayout(stats_layout)

        # === Scroll Area للرسومات والجداول ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)

        # === الرسومات البيانية ===
        charts_label = QLabel('📈 الرسومات البيانية')
        charts_label.setFont(QFont('Arial', 14, QFont.Bold))
        charts_label.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        layout.addWidget(charts_label)

        # Charts container
        charts_layout = QHBoxLayout()
        
        # Bar Chart - الأرباح حسب الأقسام
        self.bar_chart = self.create_profit_bar_chart()
        charts_layout.addWidget(self.bar_chart)

        # Pie Chart - توزيع المبيعات
        self.pie_chart = self.create_sales_pie_chart()
        charts_layout.addWidget(self.pie_chart)

        layout.addLayout(charts_layout)

        # Line Chart - اتجاه المبيعات
        self.line_chart = self.create_sales_trend_chart()
        layout.addWidget(self.line_chart)

        # === جدول تحليل الأقسام ===
        category_label = QLabel('📂 تحليل العوائد والتكاليف حسب الأقسام')
        category_label.setFont(QFont('Arial', 12, QFont.Bold))
        category_label.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        layout.addWidget(category_label)

        self.category_table = QTableWidget()
        self.category_table.setColumnCount(6)
        self.category_table.setHorizontalHeaderLabels(['القسم', 'العوائد (مبيعات)', 'التكلفة', 'الربح', 'هامش الربح %', 'الكمية المباعة'])
        self.category_table.horizontalHeader().setStretchLastSection(True)
        self.category_table.setMaximumHeight(200)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.category,
                SUM(si.subtotal) as revenue,
                SUM(si.quantity * si.purchase_price) as cost,
                SUM(si.item_profit) as profit,
                SUM(si.quantity) as total_qty
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sales s ON si.sale_id = s.sale_id
            GROUP BY p.category
            ORDER BY profit DESC
        """)

        for row_data in cursor.fetchall():
            row = self.category_table.rowCount()
            self.category_table.insertRow(row)

            category = row_data[0]
            revenue = row_data[1]
            cost = row_data[2]
            profit = row_data[3]
            total_qty = row_data[4]
            margin = (profit / revenue * 100) if revenue > 0 else 0

            if margin >= 30:
                bg_color = QColor(200, 255, 200)
            elif margin >= 20:
                bg_color = QColor(255, 255, 200)
            else:
                bg_color = QColor(255, 230, 230)

            items = [
                QTableWidgetItem(category),
                QTableWidgetItem(f"{revenue:.2f} ج"),
                QTableWidgetItem(f"{cost:.2f} ج"),
                QTableWidgetItem(f"{profit:.2f} ج"),
                QTableWidgetItem(f"{margin:.1f}%"),
                QTableWidgetItem(f"{int(total_qty)} قطعة")
            ]

            for col, item in enumerate(items):
                item.setBackground(bg_color)
                if col >= 1:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.category_table.setItem(row, col, item)

        conn.close()
        layout.addWidget(self.category_table)

        # جدول تفصيلي بالأرباح حسب الفاتورة
        table_label = QLabel('📈 تفاصيل الأرباح حسب الفاتورة')
        table_label.setFont(QFont('Arial', 12, QFont.Bold))
        table_label.setStyleSheet("margin-top: 10px;")
        layout.addWidget(table_label)

        self.profit_table = QTableWidget()
        self.profit_table.setColumnCount(5)
        self.profit_table.setHorizontalHeaderLabels(['رقم الفاتورة', 'التاريخ', 'الإجمالي', 'الربح', 'هامش الربح %'])
        self.profit_table.horizontalHeader().setStretchLastSection(True)
        self.profit_table.setMaximumHeight(250)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sale_id, sale_date, total_amount, total_profit FROM sales ORDER BY sale_date DESC LIMIT 100")

        for row_data in cursor.fetchall():
            row = self.profit_table.rowCount()
            self.profit_table.insertRow(row)

            margin = (row_data[3] / row_data[2] * 100) if row_data[2] > 0 else 0

            self.profit_table.setItem(row, 0, QTableWidgetItem(str(row_data[0])))
            self.profit_table.setItem(row, 1, QTableWidgetItem(row_data[1]))
            self.profit_table.setItem(row, 2, QTableWidgetItem(f"{row_data[2]:.2f}"))
            self.profit_table.setItem(row, 3, QTableWidgetItem(f"{row_data[3]:.2f}"))
            self.profit_table.setItem(row, 4, QTableWidgetItem(f"{margin:.1f}%"))

        conn.close()
        layout.addWidget(self.profit_table)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # زر الإغلاق
        close_btn = QPushButton('إغلاق')
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background: #e74c3c; color: white; padding: 10px; font-size: 14px;")
        main_layout.addWidget(close_btn)

        self.setLayout(main_layout)

    def create_profit_bar_chart(self):
        """إنشاء Bar Chart للأرباح حسب الأقسام"""
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.category, SUM(si.item_profit) as profit
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            GROUP BY p.category
            ORDER BY profit DESC
        """)
        
        data = cursor.fetchall()
        conn.close()

        if data:
            categories = [row[0] for row in data]
            profits = [row[1] for row in data]

            colors = ['#27ae60', '#16a085', '#f39c12', '#e74c3c', '#9b59b6']
            bars = ax.bar(range(len(categories)), profits, color=colors[:len(categories)])
            ax.set_xticks(range(len(categories)))
            ax.set_xticklabels(categories, rotation=0, ha='center')
            ax.set_ylabel('Profit (EGP)', fontweight='bold')
            ax.set_title('Profit by Category', fontweight='bold', fontsize=12)
            ax.grid(axis='y', alpha=0.3)

            # إضافة القيم فوق الأعمدة
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}',
                       ha='center', va='bottom', fontsize=9, fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)

        fig.tight_layout()
        canvas = FigureCanvas(fig)
        return canvas

    def create_sales_pie_chart(self):
        """إنشاء Pie Chart لتوزيع المبيعات"""
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.category, SUM(si.subtotal) as revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            GROUP BY p.category
            ORDER BY revenue DESC
        """)
        
        data = cursor.fetchall()
        conn.close()

        if data:
            categories = [row[0] for row in data]
            revenues = [row[1] for row in data]

            colors = ['#27ae60', '#16a085', '#f39c12', '#e74c3c', '#9b59b6']
            wedges, texts, autotexts = ax.pie(revenues, labels=categories, autopct='%1.1f%%',
                                               colors=colors[:len(categories)],
                                               startangle=90)
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(9)

            ax.set_title('Sales Distribution by Category', fontweight='bold', fontsize=12)
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)

        fig.tight_layout()
        canvas = FigureCanvas(fig)
        return canvas

    def create_sales_trend_chart(self):
        """إنشاء Line Chart لاتجاه المبيعات"""
        fig = Figure(figsize=(12, 4), dpi=100)
        ax = fig.add_subplot(111)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # بيانات آخر 7 أيام
        cursor.execute("""
            SELECT DATE(sale_date) as sale_day, 
                   SUM(total_amount) as daily_sales,
                   SUM(total_profit) as daily_profit
            FROM sales
            WHERE DATE(sale_date) >= DATE('now', '-7 days')
            GROUP BY DATE(sale_date)
            ORDER BY sale_day
        """)
        
        data = cursor.fetchall()
        conn.close()

        if data and len(data) > 1:
            days = [row[0] for row in data]
            sales = [row[1] for row in data]
            profits = [row[2] for row in data]

            ax.plot(days, sales, marker='o', linewidth=2, color='#3498db', label='Sales')
            ax.plot(days, profits, marker='s', linewidth=2, color='#27ae60', label='Profit')
            
            ax.set_xlabel('Date', fontweight='bold')
            ax.set_ylabel('Amount (EGP)', fontweight='bold')
            ax.set_title('Sales & Profit Trend (Last 7 Days)', fontweight='bold', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
        else:
            ax.text(0.5, 0.5, 'Not enough data (need at least 2 days)', 
                   ha='center', va='center', transform=ax.transAxes)

        fig.tight_layout()
        canvas = FigureCanvas(fig)
        return canvas

    def create_profit_card(self, title, value, color):
        """إنشاء بطاقة ربح"""
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.cart_items = []
        self.init_ui()
        self.load_data()

        from PyQt5.QtCore import QTimer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(3000)

    def init_ui(self):
        self.setWindowTitle('نظام إدارة محل الظافرية')
        self.setGeometry(50, 50, 1400, 800)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        
        title = QLabel('🏪 نظام إدارة محل الظافرية')
        title.setFont(QFont('Arial', 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 15px; background: #ecf0f1;")
        header_layout.addWidget(title)

        analytics_btn = QPushButton('📊 Analytics')
        analytics_btn.setStyleSheet("background: #9b59b6; color: white; padding: 10px; font-size: 12px; font-weight: bold;")
        analytics_btn.clicked.connect(self.open_analytics)
        analytics_btn.setFixedWidth(120)
        header_layout.addWidget(analytics_btn)

        password_btn = QPushButton('🔐 تغيير كلمة المرور')
        password_btn.setStyleSheet("background: #e67e22; color: white; padding: 10px; font-size: 12px; font-weight: bold;")
        password_btn.clicked.connect(self.change_password_dialog)
        password_btn.setFixedWidth(150)
        header_layout.addWidget(password_btn)

        layout.addLayout(header_layout)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont('Arial', 11))

        self.tabs.addTab(self.create_dashboard_tab(), '📊 لوحة التحكم')
        self.tabs.addTab(self.create_pos_tab(), '🛒 نقطة البيع')
        self.tabs.addTab(self.create_products_tab(), '📦 المنتجات')
        self.tabs.addTab(self.create_inventory_tab(), '🗃️ المخزون')
        self.tabs.addTab(self.create_reports_tab(), '📈 التقارير')

        layout.addWidget(self.tabs)

        central.setLayout(layout)
        self.statusBar().showMessage('النضام جاهز ✅ | آخر تحديث: ' + datetime.now().strftime('%H:%M:%S'))

    def open_analytics(self):
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'analytics_password'")
        stored_password = cursor.fetchone()[0]
        conn.close()

        password, ok = QInputDialog.getText(self, 'كلمة المرور', 'أدخل كلمة المرور للوصول إلى Analytics:', QLineEdit.Password)

        if ok and password:
            hashed_input = hashlib.sha256(password.encode()).hexdigest()
            if hashed_input == stored_password:
                dialog = AnalyticsProfitDialog(self.db.db_path, self)
                dialog.exec_()
            else:
                QMessageBox.warning(self, 'خطأ', '❌ كلمة المرور غير صحيحة!')

    def change_password_dialog(self):
        email, ok = QInputDialog.getText(self, 'تأكيد الهوية', 'أدخل بريدك الإلكتروني:')
        
        if not ok or not email:
            return

        if '@' not in email or '.' not in email:
            QMessageBox.warning(self, 'خطأ', 'البريد الإلكتروني غير صحيح!')
            return

        verification_code = str(random.randint(100000, 999999))
        QMessageBox.information(self, 'رمز التحقق', 
                               f'تم إرسال رمز التحقق إلى {email}\n\nرمز التحقق (للاختبار): {verification_code}\n\nملاحظة: في الإصدار الحقيقي، سيتم إرسال الرمز عبر البريد الإلكتروني.')

        entered_code, ok = QInputDialog.getText(self, 'رمز التحقق', 'أدخل رمز التحقق المرسل:')

        if not ok or entered_code != verification_code:
            QMessageBox.warning(self, 'خطأ', '❌ رمز التحقق غير صحيح!')
            return

        new_password, ok = QInputDialog.getText(self, 'كلمة المرور الجديدة', 'أدخل كلمة المرور الجديدة:', QLineEdit.Password)

        if not ok or not new_password or len(new_password) < 6:
            QMessageBox.warning(self, 'خطأ', 'كلمة المرور يجب أن تكون 6 أحرف على الأقل!')
            return

        confirm_password, ok = QInputDialog.getText(self, 'تأكيد كلمة المرور', 'أعد إدخال كلمة المرور:', QLineEdit.Password)

        if not ok or new_password != confirm_password:
            QMessageBox.warning(self, 'خطأ', '❌ كلمتا المرور غير متطابقتين!')
            return

        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE system_settings SET setting_value = ? WHERE setting_key = 'analytics_password'", (hashed_password,))
        conn.commit()
        conn.close()

        QMessageBox.information(self, 'نجح ✅', 'تم تغيير كلمة المرور بنجاح!')

    def create_dashboard_tab(self):
        widget = QWidget()
        self.dashboard_layout = QVBoxLayout()

        self.dashboard_stats_layout = QHBoxLayout()
        self.dashboard_layout.addLayout(self.dashboard_stats_layout)

        low_stock_label = QLabel('⚠️ تنبيهات المخزون المنخفض')
        low_stock_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.dashboard_layout.addWidget(low_stock_label)

        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(6)
        self.low_stock_table.setHorizontalHeaderLabels(['الكود', 'اسم المنتج', 'الفئة', 'المخزون', 'الحد الأدنى', 'الحالة'])
        self.low_stock_table.horizontalHeader().setStretchLastSection(True)
        # ✅ منع التعديل تماماً في لوحة التحكم
        self.low_stock_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dashboard_layout.addWidget(self.low_stock_table)

        refresh_btn = QPushButton('🔄 تحديث البيانات')
        refresh_btn.clicked.connect(self.refresh_dashboard)
        refresh_btn.setStyleSheet("background: #3498db; color: white; padding: 10px; font-size: 14px;")
        self.dashboard_layout.addWidget(refresh_btn)

        widget.setLayout(self.dashboard_layout)
        return widget

    def refresh_dashboard(self):
        while self.dashboard_stats_layout.count():
            child = self.dashboard_stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_amount), 0) FROM sales WHERE DATE(sale_date) = DATE('now')")
        sales_count, total_sales = cursor.fetchone()

        cursor.execute("SELECT COALESCE(SUM(current_stock * purchase_price), 0) FROM products")
        inventory_value = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products WHERE current_stock <= min_stock_alert")
        low_stock = cursor.fetchone()[0]

        conn.close()

        self.dashboard_stats_layout.addWidget(self.create_stat_card('عدد الفواتير اليوم', str(sales_count), '#3498db'))
        self.dashboard_stats_layout.addWidget(self.create_stat_card('إجمالي المبيعات', f'{total_sales:.2f} ج', '#2ecc71'))
        self.dashboard_stats_layout.addWidget(self.create_stat_card('قيمة المخزون', f'{inventory_value:.2f} ج', '#9b59b6'))
        self.dashboard_stats_layout.addWidget(self.create_stat_card('تنبيهات المخزون', str(low_stock), '#e74c3c'))

        self.load_low_stock_table()
        self.statusBar().showMessage('✅ تم التحديث | الوقت: ' + datetime.now().strftime('%H:%M:%S'))

    def create_stat_card(self, title, value, color):
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
        widget = QWidget()
        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('🔍 بحث تلقائي:'))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('اكتب للبحث التلقائي (مثل: DC, دفتر, شبشب)...')
        self.search_input.textChanged.connect(self.live_search_products)
        search_layout.addWidget(self.search_input)

        left_layout.addLayout(search_layout)

        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(7)
        self.search_results_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'الفئة', 'السعر', 'المخزون', 'الكمية', 'إضافة'])
        self.search_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # ✅ منع التعديل تماماً في نقطة البيع
        self.search_results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # ✨ إضافة Hover Effect
        self.search_results_table.setStyleSheet("""
            QTableWidget::item:hover {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
            }
        """)
        left_layout.addWidget(self.search_results_table)

        right_layout = QVBoxLayout()

        cart_label = QLabel('🛒 سلة المشتريات')
        cart_label.setFont(QFont('Arial', 14, QFont.Bold))
        right_layout.addWidget(cart_label)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'السعر', 'الكمية', 'الإجمالي', 'حذف'])
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # ✅ منع التعديل تماماً في السلة
        self.cart_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # ✨ إضافة Hover Effect
        self.cart_table.setStyleSheet("""
            QTableWidget::item:hover {
                background-color: #fff3e0;
                border: 1px solid #ff9800;
            }
        """)
        right_layout.addWidget(self.cart_table)

        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel('الإجمالي:'))
        self.total_label = QLabel('0.00 جنيه')
        self.total_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.total_label.setStyleSheet("color: #27ae60;")
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()
        right_layout.addLayout(total_layout)

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

        # رسالة تحذير
        warning_label = QLabel('💡 تلميح: يمكنك التعديل المباشر على المنتجات - سيتم طلب تأكيد قبل حفظ التغييرات')
        warning_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 5px; background: #d5f4e6; border-radius: 3px;")
        layout.addWidget(warning_label)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(10)
        self.products_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'الفئة', 'المقاس', 'الشركة', 'سعر الشراء', 'سعر البيع', 'المخزون', 'نسخ', 'حذف'])
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # ✅ السماح بالتعديل مع رسالة تأكيد
        self.products_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        # متغير لتتبع حالة التعديل
        self.products_table_editing = False
        self.products_table.itemChanged.connect(self.on_product_item_changed)
        
        layout.addWidget(self.products_table)

        widget.setLayout(layout)
        return widget

    def on_product_item_changed(self, item):
        """معالج التعديلات على جدول المنتجات"""
        # تجنب infinite loop
        if self.products_table_editing:
            return
        
        # التحقق من أن التغيير ليس من أزرار
        if item.column() >= 8:  # أزرار النسخ والحذف
            return
        
        # حفظ القيمة الجديدة مؤقتاً
        new_value = item.text()
        row = item.row()
        col = item.column()
        
        # قراءة البيانات الحالية من قاعدة البيانات
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # الحصول على product_code من العمود 0
        product_code = self.products_table.item(row, 0).text()
        cursor.execute("SELECT * FROM products WHERE product_code = ?", (product_code,))
        product_data = cursor.fetchone()
        conn.close()
        
        if not product_data:
            return
        
        # أسماء الأعمدة
        columns = ['product_code', 'product_name', 'category', 'size', 'manufacturer', 
                   'purchase_price', 'selling_price', 'current_stock']
        column_name = columns[col]
        old_value = product_data[col + 1]  # +1 لأن product_id هو العمود 0 في البيانات
        
        # عرض رسالة التأكيد
        reply = QMessageBox.question(
            self, 
            'تأكيد التعديل',
            f'هل أنت متأكد من تغيير\n\n'
            f'الحقل: {self.products_table.horizontalHeaderItem(col).text()}\n'
            f'من: {old_value}\n'
            f'إلى: {new_value}',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # تطبيق التعديل في قاعدة البيانات
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            try:
                # التحقق من نوع البيانات
                if col in [5, 6]:  # أسعار
                    new_value = float(new_value)
                elif col == 7:  # مخزون
                    new_value = int(new_value)
                
                cursor.execute(f"UPDATE products SET {column_name} = ? WHERE product_code = ?",
                             (new_value, product_code))
                conn.commit()
                
                QMessageBox.information(self, 'تم التحديث ✅', f'تم تحديث {column_name} بنجاح!')
                
                # تحديث كل البيانات
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, 'خطأ', f'فشل التحديث:\n{str(e)}')
                # إعادة القيمة القديمة
                self.products_table_editing = True
                item.setText(str(old_value))
                self.products_table_editing = False
            finally:
                conn.close()
        else:
            # إلغاء التعديل
            self.products_table_editing = True
            item.setText(str(old_value))
            self.products_table_editing = False

    def create_inventory_tab(self):
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

        # رسالة تحذير
        warning_label = QLabel('🔒 جدول المخزون للعرض فقط - لا يمكن التعديل المباشر')
        warning_label.setStyleSheet("color: #3498db; font-weight: bold; padding: 5px; background: #d1ecf1; border-radius: 3px;")
        layout.addWidget(warning_label)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels(['الكود', 'الاسم', 'الفئة', 'سعر الشراء', 'سعر البيع', 'الكمية', 'القيمة'])
        self.inventory_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # ✅ منع التعديل تماماً في المخزون
        self.inventory_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.inventory_table)

        widget.setLayout(layout)
        return widget

    def create_reports_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        label = QLabel('📈 تقارير المبيعات')
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
        self.refresh_dashboard()
        self.load_products_table()
        self.load_inventory_table()
        self.generate_daily_report()

    def load_all_data(self):
        self.load_data()
        QMessageBox.information(self, 'تم التحديث', 'تم تحديث جميع البيانات بنجاح ✅')

    def load_low_stock_table(self):
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
        # منع إطلاق itemChanged أثناء التحميل
        self.products_table_editing = True
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, product_code, product_name, category, size, manufacturer, purchase_price, selling_price, current_stock FROM products ORDER BY product_name")

        self.products_table.setRowCount(0)
        for row_data in cursor.fetchall():
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)

            for col, value in enumerate(row_data[1:], 0):
                self.products_table.setItem(row, col, QTableWidgetItem(str(value or '')))

            copy_btn = QPushButton('📋 نسخ')
            copy_btn.clicked.connect(lambda checked, pid=row_data[0]: self.copy_product_dialog(pid))
            copy_btn.setStyleSheet("background: #3498db; color: white; padding: 3px; font-weight: bold;")
            self.products_table.setCellWidget(row, 8, copy_btn)

            del_btn = QPushButton('🗑️')
            del_btn.clicked.connect(lambda checked, pid=row_data[0]: self.delete_product(pid))
            del_btn.setStyleSheet("background: #e74c3c; color: white; padding: 3px;")
            self.products_table.setCellWidget(row, 9, del_btn)

        conn.close()
        
        # تفعيل itemChanged مرة أخرى
        self.products_table_editing = False

    def load_inventory_table(self):
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
        search_term = self.search_input.text().strip()

        if len(search_term) < 1:
            self.search_results_table.setRowCount(0)
            return

        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

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
        del self.cart_items[index]
        self.refresh_cart()

    def clear_cart(self):
        self.cart_items = []
        self.refresh_cart()

    def complete_sale(self):
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
                                  f'الإجمالي: {total_amount:.2f} جنيه')

            self.cart_items = []
            self.refresh_cart()
            self.load_data()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, 'خطأ', f'فشلت عملية البيع:\n{str(e)}')
        finally:
            conn.close()

    def copy_product_dialog(self, product_id):
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_code, product_name, category, size, manufacturer, purchase_price, selling_price, current_stock FROM products WHERE product_id = ?", (product_id,))
        product_data = cursor.fetchone()
        conn.close()

        if not product_data:
            QMessageBox.warning(self, 'خطأ', 'لم يتم العثور على المنتج!')
            return

        self.add_product_dialog(copy_from=product_data)

    def replace_numbers_in_text(self, text, old_number, new_number):
        """استبدال رقم بآخر في النص - يدعم العربي والإنجليزي"""
        if not old_number or not new_number:
            return text
        
        # استخدام negative lookahead و lookbehind لضمان عدم استبدال أرقام جزئية
        # مثلاً: 42 في 420 لن يتم استبداله
        pattern = r'(?<!\d)' + re.escape(str(old_number)) + r'(?!\d)'
        return re.sub(pattern, str(new_number), text)

    def add_product_dialog(self, copy_from=None):
        dialog = QDialog(self)
        dialog.setWindowTitle('📋 نسخ منتج' if copy_from else 'إضافة منتج جديد')
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

        # حفظ المقاس الأصلي في dialog attribute
        dialog.last_size = ''
        
        # إذا كان نسخ، املأ كل الحقول بما فيها الكود
        if copy_from:
            code_input.setText(copy_from[0])
            name_input.setText(copy_from[1])
            category_input.setCurrentText(copy_from[2])
            dialog.last_size = copy_from[3] or ''
            size_input.setText(dialog.last_size)
            manufacturer_input.setText(copy_from[4] or '')
            purchase_price_input.setValue(copy_from[5])
            selling_price_input.setValue(copy_from[6])
            stock_input.setValue(0)

            # Function للتحديث التلقائي
            def on_size_text_changed():
                new_size = size_input.text().strip()
                old_size = dialog.last_size
                
                if not old_size or not new_size or old_size == new_size:
                    return
                
                # تحديث الكود
                current_code = code_input.text()
                new_code = self.replace_numbers_in_text(current_code, old_size, new_size)
                code_input.setText(new_code)
                
                # تحديث الاسم
                current_name = name_input.text()
                new_name = self.replace_numbers_in_text(current_name, old_size, new_size)
                name_input.setText(new_name)
                
                # حفظ المقاس الجديد
                dialog.last_size = new_size
            
            # ربط signal
            size_input.textChanged.connect(on_size_text_changed)

        layout.addRow('الكود *:', code_input)
        layout.addRow('الاسم *:', name_input)
        layout.addRow('الفئة *:', category_input)
        layout.addRow('المقاس:', size_input)
        layout.addRow('الشركة:', manufacturer_input)
        layout.addRow('سعر الشراء *:', purchase_price_input)
        layout.addRow('سعر البيع *:', selling_price_input)
        layout.addRow('الكمية الأولية:', stock_input)

        if copy_from:
            note_label = QLabel('💡 غيّر المقاس وستتحدث بقية الحقول تلقائياً\nمثال: 42 → 55 يحدث الكود والاسم فوراً ⚡')
            note_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px; padding: 10px; background: #d5f4e6; border-radius: 5px;")
            layout.addRow(note_label)

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
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0), COALESCE(SUM(total_profit), 0)
            FROM sales WHERE DATE(sale_date) = DATE('now')
        """)
        sales_count, total_sales, total_profit = cursor.fetchone()

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

        cursor.execute("""
            SELECT sale_id, sale_date, total_amount
            FROM sales
            WHERE DATE(sale_date) = DATE('now')
            ORDER BY sale_date DESC
            LIMIT 5
        """)
        recent_sales = cursor.fetchall()

        cursor.execute("SELECT COUNT(*), SUM(current_stock), SUM(current_stock * purchase_price) FROM products")
        product_count, total_qty, inventory_value = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM products WHERE current_stock <= min_stock_alert")
        low_stock_count = cursor.fetchone()[0]

        conn.close()

        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                     📊 تقرير مبيعات اليوم                          ║
║                  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}                   ║
╚══════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ 📈 ملخص المبيعات اليومية                                          │
└─────────────────────────────────────────────────────────────────┘

  💰 إجمالي المبيعات:        {total_sales:>12.2f} جنيه
  📋 عدد الفواتير:           {sales_count:>12} فاتورة
  📊 متوسط الفاتورة:         {(total_sales / sales_count if sales_count > 0 else 0):>12.2f} جنيه

┌─────────────────────────────────────────────────────────────────┐
│ 🏆 أفضل 5 منتجات مبيعاً                                           │
└─────────────────────────────────────────────────────────────────┘
"""

        if best_sellers:
            for i, (name, code, qty, revenue, profit) in enumerate(best_sellers, 1):
                report += f"""
  {i}. [{code}] {name}
     ├─ الكمية المباعة: {qty} قطعة
     └─ الإيرادات: {revenue:.2f} جنيه
"""
        else:
            report += "\n  ⚠️  لا توجد مبيعات حتى الآن\n"

        report += f"""
┌─────────────────────────────────────────────────────────────────┐
│ 🧾 آخر الفواتير                                                    │
└─────────────────────────────────────────────────────────────────┘
"""

        if recent_sales:
            for sale_id, sale_date, amount in recent_sales:
                time_str = datetime.strptime(sale_date, '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
                report += f"  • فاتورة #{sale_id:<4} | {time_str} | {amount:>8.2f} ج\n"
        else:
            report += "  ⚠️  لا توجد فواتير اليوم\n"

        report += f"""
┌─────────────────────────────────────────────────────────────────┐
│ 📦 حالة المخزون                                                    │
└─────────────────────────────────────────────────────────────────┘

  📊 عدد المنتجات:          {product_count:>12} منتج
  📦 إجمالي الكمية:         {total_qty:>12} قطعة
  💰 قيمة المخزون:          {inventory_value:>12.2f} جنيه
  ⚠️  تنبيهات المخزون:      {low_stock_count:>12} منتج

╔══════════════════════════════════════════════════════════════════╗
║  تم إنشاء التقرير بواسطة: نظام محل الظافرية                        ║
╚══════════════════════════════════════════════════════════════════╝
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
