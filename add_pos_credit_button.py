#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإضافة زر الفاتورة الآجلة لنقطة البيع
Script to add credit invoice button to POS

استخدم هذا السكريبت لإضافة الزر تلقائياً إلى main.py
"""

import re
import shutil
from datetime import datetime

def add_credit_button_to_pos():
    """إضافة زر الفاتورة الآجلة لنقطة البيع"""
    
    # 1. عمل نسخة احتياطية
    backup_file = f'main_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
    try:
        shutil.copy('main.py', backup_file)
        print(f"✅ تم عمل نسخة احتياطية: {backup_file}")
    except Exception as e:
        print(f"❌ فشل عمل النسخة الاحتياطية: {e}")
        return False
    
    # 2. قراءة الملف
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ فشل قراءة main.py: {e}")
        return False
    
    # 3. التحقق إذا كان الزر موجود بالفعل
    if 'POSCreditDialog' in content:
        print("⚠️ الزر موجود بالفعل!")
        return True
    
    # 4. إضافة الـ import
    import_line = "from views.pos_credit_dialog import POSCreditDialog\n"
    
    # البحث عن سطر imports النظام
    import_pattern = r'(from views\.credit_view import CreditManagementView)'
    if re.search(import_pattern, content):
        content = re.sub(
            import_pattern,
            r'\1\n' + import_line,
            content
        )
        print("✅ تم إضافة import")
    else:
        print("⚠️ لم يتم العثور على مكان imports")
        # إضافته بعد آخر import للـ views
        if 'from views' in content:
            last_import = content.rfind('from views')
            if last_import != -1:
                line_end = content.find('\n', last_import)
                content = content[:line_end+1] + import_line + content[line_end+1:]
                print("✅ تم إضافة import بعد آخر import")
    
    # 5. إضافة الدوال الجديدة
    new_functions = '''

    def create_credit_invoice_from_pos(self):
        """تحويل سلة نقطة البيع لفاتورة آجلة"""
        # التحقق من وجود منتجات في السلة
        if not hasattr(self, 'sale_items') or not self.sale_items:
            QMessageBox.warning(self, 'تحذير', 'السلة فارغة!\n\nأضف منتجات أولاً.')
            return
        
        # تحويل السلة للصيغة المطلوبة
        cart_items = []
        total = 0
        
        for item in self.sale_items:
            cart_items.append({
                'code': item.get('product_code', ''),
                'name': item.get('product_name', ''),
                'price': item.get('unit_price', 0),
                'quantity': item.get('quantity', 0)
            })
            total += item.get('unit_price', 0) * item.get('quantity', 0)
        
        # فتح نافذة الفاتورة الآجلة
        dialog = POSCreditDialog(cart_items, total, self.db_path, self)
        if dialog.exec_():
            # لو تم الحفظ بنجاح، امسح السلة
            self.sale_items = []
            self.refresh_pos_table()
            self.update_pos_total()
            QMessageBox.information(
                self, 'نجح ✅',
                'تم تحويل المشتريات لفاتورة آجلة!'
            )
'''
    
    # 6. البحث عن مكان إضافة الدالة (بعد آخر دالة في الكلاس)
    # نبحث عن class للنظام الرئيسي
    class_pattern = r'(class \w+MainWindow.*?:\s*\n(?:.*?\n)*?)(?=\n\nclass |\n\nif __name__|$)'
    
    # نبحث عن مكان إضافة الدالة
    if 'class StoreMainWindow' in content or 'class MainWindow' in content:
        # نضيف الدالة قبل نهاية الكلاس
        # نبحث عن مكان مناسب (قبل if __name__)
        if 'if __name__' in content:
            insert_pos = content.rfind('\n\nif __name__')
            content = content[:insert_pos] + new_functions + content[insert_pos:]
            print("✅ تم إضافة الدالة الجديدة")
    
    # 7. كتابة الملف المعدل
    try:
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ تم حفظ التعديلات")
    except Exception as e:
        print(f"❌ فشل الحفظ: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ تم إضافة الكود بنجاح!")
    print("\nلإضافة الزر في واجهة نقطة البيع، أضف هذا الكود في دالة create_pos_tab:")
    print("""\n# في دالة create_pos_tab، بعد أزرار 'إتمام البيع' و 'مسح السلة':

credit_btn = QPushButton('📋 فاتورة آجلة')
credit_btn.clicked.connect(self.create_credit_invoice_from_pos)
credit_btn.setStyleSheet(\"\"\"\n    QPushButton {\n        background: #9b59b6;\n        color: white;\n        padding: 10px;\n        font-size: 14px;\n        font-weight: bold;\n        border-radius: 5px;\n    }\n    QPushButton:hover {\n        background: #8e44ad;\n    }\n\"\"\")
buttons_layout.addWidget(credit_btn)  # أضفه للـ layout اللي فيه الأزرار
""")
    print("="*60)
    
    return True

if __name__ == '__main__':
    print("🚀 بدء إضافة زر الفاتورة الآجلة لنقطة البيع...\n")
    
    success = add_credit_button_to_pos()
    
    if success:
        print("\n✅ العملية نجحت!")
        print("\nاتبع التعليمات أعلاه لإضافة الزر في واجهة نقطة البيع.")
    else:
        print("\n❌ فشلت العملية!")
        print("الرجاء التحقق من بنية main.py")
