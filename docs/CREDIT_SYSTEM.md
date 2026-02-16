# نظام الديون - دليل الاستخدام
## Credit System Documentation

## نظرة عامة

نظام إدارة الديون المتكامل لمحل الظافرية يتيح تتبع المبيعات الآجلة، إدارة الزبائن، وتسجيل الدفعات.

## المكونات الأساسية

### 1. قاعدة البيانات
**الموقع:** `database/credit_system.py`

#### الجداول:

##### customers (الزبائن)
```sql
- customer_id: المعرف الفريد
- name: اسم الزبون
- phone: رقم التليفون (فريد)
- address: العنوان
- notes: ملاحظات
- status: الحالة (normal/reliable/late)
- credit_limit: حد الدين المسموح
- created_at: تاريخ الإضافة
```

##### credit_invoices (الفواتير الآجلة)
```sql
- invoice_id: المعرف الفريد
- customer_id: معرف الزبون
- invoice_number: رقم الفاتورة (مثل: INV-2026-001)
- total_amount: إجمالي الفاتورة
- paid_amount: المبلغ المدفوع
- remaining_amount: الباقي
- invoice_date: تاريخ الفاتورة
- due_date: موعد السداد
- status: الحالة (pending/partial/paid/overdue)
- notes: ملاحظات
- created_at: تاريخ الإنشاء
```

##### invoice_items (تفاصيل المشتريات)
```sql
- item_id: المعرف الفريد
- invoice_id: معرف الفاتورة
- product_code: كود المنتج
- product_name: اسم المنتج
- quantity: الكمية
- unit_price: سعر الوحدة
- total_price: الإجمالي
- created_at: تاريخ الإضافة
```

##### payments (الدفعات)
```sql
- payment_id: المعرف الفريد
- customer_id: معرف الزبون
- invoice_id: معرف الفاتورة
- amount: المبلغ
- payment_method: طريقة الدفع (cash/vodafone_cash/instapay)
- payment_date: تاريخ الدفع
- received_by: المستلم
- notes: ملاحظات
- created_at: تاريخ الإضافة
```

### 2. Models (النماذج)

#### Customer Model
**الموقع:** `models/customer.py`

**الوظائف الرئيسية:**
- `add_customer()`: إضافة زبون جديد
- `get_customer()`: الحصول على بيانات زبون
- `get_all_customers()`: عرض جميع الزبائن مع إجمالي ديونهم
- `search_customers()`: البحث عن زبائن
- `update_customer()`: تحديث بيانات زبون
- `delete_customer()`: حذف زبون (إذا لم يكن لديه ديون)
- `get_customer_stats()`: إحصائيات الزبون

#### CreditInvoice Model
**الموقع:** `models/credit_invoice.py`

**الوظائف الرئيسية:**
- `generate_invoice_number()`: توليد رقم فاتورة تلقائي
- `create_invoice()`: إنشاء فاتورة آجلة
- `get_invoice()`: الحصول على تفاصيل فاتورة مع المشتريات والدفعات
- `get_customer_invoices()`: عرض فواتير زبون
- `get_overdue_invoices()`: الفواتير المتأخرة
- `add_payment()`: تسجيل دفعة
- `get_all_stats()`: إحصائيات عامة

#### Payment Model
**الموقع:** `models/payment.py`

**الوظائف الرئيسية:**
- `add_payment()`: إضافة دفعة جديدة
- `get_payment()`: الحصول على تفاصيل دفعة
- `get_customer_payments()`: دفعات زبون
- `get_invoice_payments()`: دفعات فاتورة
- `get_payments_by_date()`: الدفعات خلال فترة
- `get_daily_payments_summary()`: ملخص الدفعات اليومية
- `delete_payment()`: حذف دفعة
- `get_payment_stats()`: إحصائيات الدفعات

### 3. Views (الواجهات)

#### CreditView
**الموقع:** `views/credit_view.py`

الواجهة الرئيسية لنظام الديون تحتوي على:
- جدول الزبائن المديونين
- إحصائيات عامة
- البحث والفلترة
- أزرار الإجراءات

#### CreditDialogs
**الموقع:** `views/credit_dialogs.py`

نوافذ حوارية لـ:
- إضافة زبون جديد
- تفاصيل الزبون
- عرض تفاصيل الفاتورة
- تسجيل دفعة
- إنشاء فاتورة آجلة جديدة

## أمثلة الاستخدام

### 1. إضافة زبون جديد

```python
from models.customer import Customer

customer = Customer()
success, customer_id, message = customer.add_customer(
    name="أحمد محمد",
    phone="01012345678",
    address="القاهرة",
    credit_limit=5000
)

if success:
    print(f"تم إضافة الزبون برقم: {customer_id}")
```

### 2. إنشاء فاتورة آجلة

```python
from models.credit_invoice import CreditInvoice
from datetime import datetime, timedelta

invoice = CreditInvoice()

# المشتريات
items = [
    {'code': 'ش42DC', 'name': 'شبشب DC مقاس 42', 'qty': 2, 'price': 150},
    {'code': 'ق40SB', 'name': 'قميص رجالي', 'qty': 1, 'price': 250}
]

# موعد السداد بعد شهر
due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

success, invoice_id, invoice_number, message = invoice.create_invoice(
    customer_id=5,
    items=items,
    due_date=due_date,
    notes="بيع بالآجل"
)

if success:
    print(f"تم إنشاء الفاتورة: {invoice_number}")
```

### 3. تسجيل دفعة

```python
from models.payment import Payment

payment = Payment()

success, payment_id, message = payment.add_payment(
    customer_id=5,
    invoice_id=150,
    amount=300,
    payment_method='cash',
    received_by='المدير'
)

if success:
    print(message)
```

### 4. عرض فواتير زبون

```python
from models.credit_invoice import CreditInvoice

invoice = CreditInvoice()
invoices = invoice.get_customer_invoices(customer_id=5)

for inv in invoices:
    print(f"الفاتورة: {inv['invoice_number']}")
    print(f"الإجمالي: {inv['total_amount']} ج")
    print(f"الباقي: {inv['remaining_amount']} ج")
    print("---")
```

### 5. الإحصائيات العامة

```python
from models.credit_invoice import CreditInvoice

invoice = CreditInvoice()
stats = invoice.get_all_stats()

print(f"إجمالي الديون: {stats['total_debt']:.2f} ج")
print(f"عدد الزبائن المديونين: {stats['debtors_count']}")
print(f"ديون متأخرة +30 يوم: {stats['overdue_30']:.2f} ج")
print(f"ديون حرجة +60 يوم: {stats['overdue_60']:.2f} ج")
```

## Integration مع نقطة البيع

عند البيع الآجل في نقطة البيع، يتم:

1. اختيار "بيع آجل"
2. اختيار أو إضافة الزبون
3. إضافة المنتجات للفاتورة
4. تحديد موعد السداد
5. إنشاء الفاتورة تلقائياً
6. تحديث المخزون
7. إضافة الفاتورة لسجل ديون الزبون

## التقارير

التقارير المتاحة:
- تقرير الديون اليومي
- قائمة المتأخرين في السداد
- تقرير الدفعات
- كشف حساب الزبون
- تحليل أداء التحصيل

## الأمان

- نظام الديون محمي بكلمة مرور (مثل Analytics)
- لا تظهر معلومات الديون في الواجهة الرئيسية
- يمكن تصدير البيانات لـ Excel/PDF
- سجل كامل لجميع العمليات

## التطوير المستقبلي

- [ ] إرسال تذكيرات SMS/WhatsApp تلقائية
- [ ] جدولة مواعيد السداد
- [ ] تقييم تلقائي للزبائن حسب التزامهم
- [ ] ربط مع نظام محاسبي
- [ ] تطبيق موبايل للمتابعة

## المساهمة

لأي استفسارات أو مقترحات، تواصل مع المطور.

---
**نظام إدارة محل الظافرية** - 2026
