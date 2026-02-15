#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة محل الظافرية - نسخة محمية
AlDhaferya Store Management System - Protected Version
"""

import sys
import os

# فحص الترخيص قبل بدء البرنامج
from license_system import LicenseSystem
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog, QLineEdit

def check_license_and_activate():
    """فحص الترخيص أو طلب التفعيل"""
    ls = LicenseSystem()
    
    # فحص الترخيص الموجود
    is_valid, status = ls.check_license()
    
    if is_valid:
        return True
    
    # إذا لم يكن مفعّل - عرض نافذة التفعيل
    app = QApplication(sys.argv)
    
    hwid = ls.get_hardware_id()
    
    if status == "NO_LICENSE":
        # أول تشغيل - عرض HWID وطلب المفتاح
        _, info = ls.get_activation_info()
        
        QMessageBox.information(
            None,
            'تفعيل البرنامج',
            f'{info}\n\nاضغط OK لإدخال مفتاح التفعيل'
        )
        
        # طلب مفتاح التفعيل
        license_key, ok = QInputDialog.getText(
            None,
            'إدخال مفتاح التفعيل',
            f'أدخل مفتاح التفعيل (XXXX-XXXX-XXXX-XXXX):\n\n'
            f'معرّف جهازك: {hwid}',
            QLineEdit.Normal
        )
        
        if not ok or not license_key:
            QMessageBox.critical(None, 'خطأ', 'يجب إدخال مفتاح التفعيل!')
            return False
        
        # التحقق من المفتاح
        if ls.validate_license_key(license_key, hwid):
            # حفظ الترخيص
            customer_name, ok = QInputDialog.getText(
                None,
                'معلومات العميل',
                'أدخل اسمك أو اسم المحل (اختياري):'
            )
            
            ls.save_license(hwid, customer_name if ok else "")
            
            QMessageBox.information(
                None,
                'تم التفعيل ✅',
                'تم تفعيل البرنامج بنجاح!\nمرحباً بك 🎉'
            )
            return True
        else:
            QMessageBox.critical(
                None,
                'مفتاح غير صحيح ❌',
                'مفتاح التفعيل غير صحيح!\n\n'
                'تأكد من:\n'
                '1. إدخال المفتاح بشكل صحيح\n'
                '2. هذا المفتاح لجهازك فقط\n'
                '3. التواصل مع الدعم الفني'
            )
            return False
    
    elif status == "INVALID_HARDWARE":
        QMessageBox.critical(
            None,
            'خطأ في الترخيص ⛔',
            'هذا البرنامج مرخّص لجهاز آخر!\n\n'
            'للحصول على ترخيص جديد لهذا الجهاز\n'
            f'معرّف جهازك: {hwid}\n\n'
            'تواصل مع الدعم الفني'
        )
        return False
    
    elif status == "TAMPERED_LICENSE":
        QMessageBox.critical(
            None,
            'تحذير أمني ⚠️',
            'تم اكتشاف تلاعب في ملف الترخيص!\n\n'
            'الرجاء إعادة تفعيل البرنامج'
        )
        # حذف الترخيص التالف
        if os.path.exists(ls.license_file):
            os.remove(ls.license_file)
        return False
    
    else:
        QMessageBox.critical(
            None,
            'خطأ ❌',
            f'خطأ في نظام الترخيص: {status}\n\n'
            'تواصل مع الدعم الفني'
        )
        return False

if __name__ == '__main__':
    # فحص الترخيص قبل البدء
    if check_license_and_activate():
        # استيراد وتشغيل البرنامج الرئيسي
        from main import main
        main()
    else:
        sys.exit(1)
