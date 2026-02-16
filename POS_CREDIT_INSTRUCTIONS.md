# 📍 تعليمات إضافة زر الفاتورة الآجلة لنقطة البيع

## ✅ تم إنجازه:

1. ✅ **تحقق رقم التليفون (11 رقم)** - في `quick_credit_view.py`
2. ✅ **Dialog الفاتورة الآجلة من نقطة البيع** - في `views/pos_credit_dialog.py`

---

## 🚀 الخطوة النهائية: إضافة الزر في نقطة البيع

### 📖 الطريقة الأولى: يدوياً (موصى بها)

#### 1. افتح `main.py`

#### 2. أضف الـ import في البداية:

ابحث عن هذا السطر:
```python
from views.credit_view import CreditManagementView
```

وأضف تحته مباشرة:
```python
from views.pos_credit_dialog import POSCreditDialog
```

---

#### 3. أضف الدالة الجديدة:

ابحث عن class النظام الرئيسي (غالباً `class StoreMainWindow` أو `class MainWindow`)

وأضف هذه الدالة داخل الـ class (في آخر الدوال):

```python
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
```

---

#### 4. أضف الزر في نقطة البيع:

ابحث عن الدالة اللي بتنشئ نقطة البيع (غالباً `create_pos_tab` أو `setup_pos_interface`)

لما تلاقي الأزرار اللي فيها:
- "✅ إتمام البيع"
- "🗑️ مسح السلة"

أضف بعدهم مباشرة:

```python
# زر الفاتورة الآجلة
credit_btn = QPushButton('📋 فاتورة آجلة')
credit_btn.clicked.connect(self.create_credit_invoice_from_pos)
credit_btn.setStyleSheet("""\n    QPushButton {\n        background: #9b59b6;\n        color: white;\n        padding: 10px;\n        font-size: 14px;\n        font-weight: bold;\n        border-radius: 5px;\n    }\n    QPushButton:hover {\n        background: #8e44ad;\n    }\n""")
buttons_layout.addWidget(credit_btn)  # أضفه للـ layout اللي فيه الأزرار
```

**ملحوظة:** غيّر `buttons_layout` للاسم الفعلي للـ layout اللي عندك

---

### 🤖 الطريقة الثانية: تلقائياً (تجريبي)

شغّل السكريبت التلقائي:

```bash
python add_pos_credit_button.py
```

السكريبت هيعمل:
- ✅ نسخة احتياطية من main.py
- ✅ إضافة الـ import
- ✅ إضافة الدالة الجديدة
- ⚠️ سيعطيك تعليمات لإضافة الزر يدوياً

---

## 📝 مثال كامل للكود:

إذا كان عندك كود زي كده:

```python
def create_pos_tab(self):
    # ... كود نقطة البيع ...
    
    # الأزرار
    buttons_layout = QHBoxLayout()
    
    complete_btn = QPushButton('✅ إتمام البيع')
    complete_btn.clicked.connect(self.complete_sale)
    buttons_layout.addWidget(complete_btn)
    
    clear_btn = QPushButton('🗑️ مسح السلة')
    clear_btn.clicked.connect(self.clear_pos_cart)
    buttons_layout.addWidget(clear_btn)
    
    # ⭐ أضف هنا ⭐
    # ... بقية الكود
```

**هيبقى:**

```python
def create_pos_tab(self):
    # ... كود نقطة البيع ...
    
    # الأزرار
    buttons_layout = QHBoxLayout()
    
    complete_btn = QPushButton('✅ إتمام البيع')
    complete_btn.clicked.connect(self.complete_sale)
    buttons_layout.addWidget(complete_btn)
    
    clear_btn = QPushButton('🗑️ مسح السلة')
    clear_btn.clicked.connect(self.clear_pos_cart)
    buttons_layout.addWidget(clear_btn)
    
    # ⭐ الزر الجديد ⭐
    credit_btn = QPushButton('📋 فاتورة آجلة')
    credit_btn.clicked.connect(self.create_credit_invoice_from_pos)
    credit_btn.setStyleSheet("""\n        QPushButton {\n            background: #9b59b6;\n            color: white;\n            padding: 10px;\n            font-size: 14px;\n            font-weight: bold;\n            border-radius: 5px;\n        }\n        QPushButton:hover {\n            background: #8e44ad;\n        }\n    """)
    buttons_layout.addWidget(credit_btn)
    
    # ... بقية الكود
```

---

## 🎯 كيف يشتغل:

1. 🛍️ المستخدم يضيف منتجات في نقطة البيع
2. 📋 يضغط "فاتورة آجلة"
3. 📝 يدخل الاسم والتليفون (11 رقم ✅)
4. 💾 يحفظ الفاتورة
5. 🧹 السلة تتمسح تلقائياً
6. ✅ المخزون يتحدّث

---

## 👁️ ما يتحقق منه الزر:

✅ **رقم التليفون:**
- 11 رقم بالظبط
- يبدأ بـ **01**
- رسائل فورية للتحقق

✅ **البحث التلقائي:**
- ابحث بالاسم → يملا التليفون
- ابحث بالتليفون → يملا الاسم

✅ **زبون جديد:**
- لو مش موجود → يضيفه تلقائياً

---

## 🔧 مشاكل محتملة:

### ❓ لو السلة اسمها مختلف:

غيّر `self.sale_items` للاسم اللي عندك (مثلاً `self.cart` أو `self.pos_cart`)

### ❓ لو دوال التحديث مختلفة:

غيّر:
- `self.refresh_pos_table()` → للدالة اللي بتحدّث جدول نقطة البيع
- `self.update_pos_total()` → للدالة اللي بتحدّث الإجمالي

### ❓ لو بينات السلة مختلفة:

غيّر المفاتيح في الدالة:
```python
cart_items.append({
    'code': item.get('product_code', ''),  # غيّر المفتاح
    'name': item.get('product_name', ''),  # غيّر المفتاح
    # ...
})
```

---

## 📊 مثال كامل للتجربة:

```bash
cd C:\Users\Dell\Zafrya-Store\Zafrya-Store
git pull
python main.py
```

1. اختر منتجات في نقطة البيع
2. اضغط "📋 فاتورة آجلة" (لو مضيفته)
3. اكتب الاسم: `محمد علي`
4. اكتب التليفون: `01234567890`
5. احفظ!

---

## ✉️ لو محتاج مساعدة:

1. انسخ سطر من الكود اللي فيه الأزرار في نقطة البيع
2. هساعدك تضيف الزر في المكان الصح! 🚀
