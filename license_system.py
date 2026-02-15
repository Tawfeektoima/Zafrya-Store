#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام الحماية وربط البرنامج بالجهاز
License & Hardware Lock System
"""

import hashlib
import uuid
import platform
import subprocess
import os
import json
from datetime import datetime

class LicenseSystem:
    """نظام حماية البرنامج وربطه بجهاز واحد"""
    
    def __init__(self):
        self.license_file = 'zafrya.lic'
        self.master_key = 'taw11-feek22-ali$$-7102023'
    
    def get_hardware_id(self):
        """الحصول على معرّف الجهاز الفريد"""
        try:
            # 1. MAC Address
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
            
            # 2. CPU Serial (Windows)
            cpu_serial = ""
            if platform.system() == "Windows":
                try:
                    output = subprocess.check_output(
                        'wmic cpu get ProcessorId', 
                        shell=True
                    ).decode()
                    cpu_serial = output.split('\n')[1].strip()
                except:
                    cpu_serial = platform.processor()
            else:
                cpu_serial = platform.processor()
            
            # 3. Machine GUID
            machine_id = str(uuid.getnode())
            
            # دمج كل المعرّفات
            hardware_string = f"{mac}-{cpu_serial}-{machine_id}"
            
            # تشفير للحصول على HWID نهائي
            hwid = hashlib.sha256(hardware_string.encode()).hexdigest()[:16].upper()
            
            return hwid
            
        except Exception as e:
            print(f"Error getting HWID: {e}")
            return None
    
    def generate_license_key(self, hwid, customer_name=""):
        """توليد مفتاح ترخيص لجهاز معين"""
        # المفتاح يعتمد فقط على HWID + المفتاح السري
        # عشان يكون ثابت في generate و validate
        combined = f"{hwid}-{self.master_key}"
        
        license_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        # تنسيق المفتاح: XXXX-XXXX-XXXX-XXXX
        key_parts = [license_hash[i:i+4].upper() for i in range(0, 16, 4)]
        license_key = '-'.join(key_parts)
        
        return license_key

    
    def validate_license_key(self, entered_key, hwid):
        """التحقق من صحة مفتاح الترخيص"""
        # توليد المفتاح الصحيح للجهاز الحالي
        valid_key = self.generate_license_key(hwid)
        
        # مقارنة
        return entered_key.strip().upper() == valid_key
    
    def save_license(self, hwid, customer_name=""):
        """حفظ الترخيص بعد التفعيل"""
        license_data = {
            'hwid': hwid,
            'customer': customer_name,
            'activated_at': datetime.now().isoformat(),
            'hash': hashlib.sha256(f"{hwid}{self.master_key}".encode()).hexdigest()
        }
        
        try:
            with open(self.license_file, 'w') as f:
                json.dump(license_data, f)
            
            # إخفاء الملف (Windows)
            if platform.system() == "Windows":
                os.system(f'attrib +h "{self.license_file}"')
            
            return True
        except Exception as e:
            print(f"Error saving license: {e}")
            return False
    
    def check_license(self):
        """فحص الترخيص عند بدء البرنامج"""
        # 1. التحقق من وجود ملف الترخيص
        if not os.path.exists(self.license_file):
            return False, "NO_LICENSE"
        
        try:
            # 2. قراءة بيانات الترخيص
            with open(self.license_file, 'r') as f:
                license_data = json.load(f)
            
            # 3. الحصول على HWID الحالي
            current_hwid = self.get_hardware_id()
            
            # 4. مقارنة HWID
            if license_data.get('hwid') != current_hwid:
                return False, "INVALID_HARDWARE"
            
            # 5. التحقق من Hash
            expected_hash = hashlib.sha256(
                f"{current_hwid}{self.master_key}".encode()
            ).hexdigest()
            
            if license_data.get('hash') != expected_hash:
                return False, "TAMPERED_LICENSE"
            
            # 6. كل شيء صحيح
            return True, "VALID"
            
        except Exception as e:
            print(f"License check error: {e}")
            return False, "CORRUPTED_LICENSE"
    
    def get_activation_info(self):
        """الحصول على معلومات التفعيل (للعميل)"""
        hwid = self.get_hardware_id()
        
        info = f"""
╔══════════════════════════════════════════════╗
║      معلومات تفعيل نظام محل الظافرية          ║
╚══════════════════════════════════════════════╝

🔑 معرّف الجهاز (HWID):
   {hwid}

📋 معلومات الجهاز:
   • النظام: {platform.system()} {platform.release()}
   • المعالج: {platform.processor()}
   • اسم الجهاز: {platform.node()}

📞 للحصول على مفتاح التفعيل:
   1. أرسل معرّف الجهاز للمطور
   2. استلم مفتاح التفعيل
   3. أدخله في البرنامج

╔══════════════════════════════════════════════╗
║  ⚠️  لا تشارك معرّف الجهاز مع الآخرين       ║
╚══════════════════════════════════════════════╝
"""
        return hwid, info


# ═══════════════════════════════════════════════════
# أدوات مساعدة للمطور
# ═══════════════════════════════════════════════════

def generate_key_for_customer(customer_hwid, customer_name=""):
    """
    أداة للمطور: توليد مفتاح تفعيل للعميل
    
    الاستخدام:
    1. العميل يرسل لك الـ HWID
    2. تشغل هذه الدالة
    3. تعطيه المفتاح
    """
    ls = LicenseSystem()
    key = ls.generate_license_key(customer_hwid, customer_name)
    
    print("╔══════════════════════════════════════════════╗")
    print("║        مفتاح تفعيل للعميل                   ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"\n🔑 مفتاح التفعيل:\n   {key}")
    print(f"\n📋 معرّف الجهاز:\n   {customer_hwid}")
    if customer_name:
        print(f"\n👤 اسم العميل:\n   {customer_name}")
    print("\n╔══════════════════════════════════════════════╗")
    print("║  ⚠️  هذا المفتاح يعمل على جهاز واحد فقط    ║")
    print("╚══════════════════════════════════════════════╝\n")
    
    return key


def test_system():
    """اختبار نظام الحماية"""
    print("🧪 اختبار نظام الحماية...\n")
    
    ls = LicenseSystem()
    
    # 1. الحصول على HWID
    hwid = ls.get_hardware_id()
    print(f"✅ معرّف الجهاز: {hwid}\n")
    
    # 2. توليد مفتاح
    key = ls.generate_license_key(hwid)
    print(f"🔑 مفتاح الاختبار: {key}\n")
    
    # 3. التحقق من المفتاح
    is_valid = ls.validate_license_key(key, hwid)
    print(f"✅ التحقق من المفتاح: {'صحيح' if is_valid else 'خطأ'}\n")
    
    # 4. حفظ الترخيص
    ls.save_license(hwid, "اختبار")
    print("✅ تم حفظ الترخيص\n")
    
    # 5. فحص الترخيص
    is_licensed, status = ls.check_license()
    print(f"✅ حالة الترخيص: {status}")
    print(f"   النتيجة: {'مفعّل ✓' if is_licensed else 'غير مفعّل ✗'}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_system()
        elif sys.argv[1] == "info":
            ls = LicenseSystem()
            hwid, info = ls.get_activation_info()
            print(info)
        elif sys.argv[1] == "generate" and len(sys.argv) > 2:
            customer_hwid = sys.argv[2]
            customer_name = sys.argv[3] if len(sys.argv) > 3 else ""
            generate_key_for_customer(customer_hwid, customer_name)
    else:
        print("""
استخدام أدوات نظام الحماية:
============================

1. اختبار النظام:
   python license_system.py test

2. عرض معلومات الجهاز:
   python license_system.py info

3. توليد مفتاح للعميل:
   python license_system.py generate <HWID> [اسم العميل]
   
   مثال:
   python license_system.py generate A1B2C3D4E5F6G7H8 "محل الظافرية"
""")