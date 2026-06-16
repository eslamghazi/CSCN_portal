# CSCN_portal — نظام إدارة مركز تنمية مهارات التمريض

نظام سطح مكتب لإدارة **مركز تنمية مهارات التمريض** بكلية التمريض – جامعة كفر الشيخ.
يوفّر إدارة متكاملة للمعايير والجودة، الوثائق، السجلات، البرامج التدريبية، شؤون العاملين,
المالية والشراكات، التقارير، وإدارة المستخدمين والصلاحيات — مع دعم كامل للغة العربية (RTL).

A desktop management system for the Health & Nursing Skills Enhancement Center
(Faculty of Nursing, Kafrelsheikh University).

---

## المميزات (Features)

- **المعايير والجودة:** معايير ومؤشرات وحساب نِسب المطابقة.
- **الوثائق:** رفع وإصدارات المستندات وربطها كأدلة عبر نظام مرفقات متعدد الكيانات.
- **السجلات:** إدارة السجلات وأنواعها.
- **التدريب:** برامج/دورات/ورش وجلسات وحضور.
- **شؤون العاملين:** الموظفون والوظائف.
- **المالية والشراكات:** الإيرادات والمصروفات وبنود الميزانية، والجهات والاتفاقيات.
- **التقارير:** توليد تقارير PDF/Word/Excel.
- **الأمان:** تسجيل دخول bcrypt، أدوار وصلاحيات (RBAC)، وسجل تدقيق (Audit Log).

## التقنيات (Tech Stack)

| الطبقة | التقنية |
|--------|---------|
| اللغة | Python 3.11+ |
| الواجهة | PySide6 (Qt6, RTL) + qtawesome (أيقونات) |
| قاعدة البيانات | SQLite + SQLAlchemy 2.0 (ORM) |
| الهجرات | Alembic |
| الأمان | bcrypt |
| التقارير | reportlab, python-docx, openpyxl, Jinja2 |
| العربية | arabic-reshaper, python-bidi |
| السجلّات | loguru |

البنية طبقية نظيفة: `domain` (الكيانات) → `application` (الخدمات و DTOs) → `infrastructure` (المستودعات) → `ui` (صفحات PySide6).

## المتطلبات (Requirements)

- Python 3.11 أو أحدث
- نظام Windows (تم تطويره وبناؤه على Windows؛ الكود متوافق مع المنصّات الأخرى عدا سكربت البناء)

## التشغيل (Setup & Run)

```powershell
# 1. إنشاء بيئة افتراضية وتفعيلها
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. تثبيت الاعتماديات
pip install -r requirements.txt
# للتطوير والاختبارات:
pip install -r requirements-dev.txt

# 3. (اختياري لكن موصى به) ضبط كلمة مرور مدير النظام قبل أول تشغيل
$env:CSCN_portal_SUPERADMIN_PASSWORD = "اختر-كلمة-مرور-قوية"

# 4. التشغيل
python main.py
```

عند أول تشغيل وقاعدة بيانات فارغة، يقوم النظام بإنشاء الأدوار، حساب **superadmin**،
ومصفوفة الصلاحيات تلقائيًا.

### بيانات الدخول الأولى (First-run login)

- **اسم المستخدم:** `superadmin`
- **كلمة المرور:** قيمة `CSCN_portal_SUPERADMIN_PASSWORD` إن ضُبطت؛ وإلا تُولَّد كلمة مرور عشوائية
  وتُسجَّل **مرة واحدة** في سجلّ التطبيق (`data/logs/`) — سجّل الدخول بها ثم غيّرها فورًا.

راجع [.env.example](.env.example) لمتغيرات البيئة.

## الاختبارات (Tests)

```powershell
venv\Scripts\python.exe -m pytest        # تشغيل كل الاختبارات
venv\Scripts\python.exe -m ruff check .  # فحص جودة الكود
```

الاختبارات تستخدم قاعدة SQLite في الذاكرة مع تفعيل قيود المفاتيح الأجنبية، وتغطي
خدمات الشراكات والمالية والتدريب والوثائق والصلاحيات والجودة، إضافةً إلى اختبارات
تكامل للمستودعات وعملية الإقلاع (seeding + wiring).

## البناء (Build — Windows executable)

```powershell
.\build.ps1
```

يُنتج تطبيقًا قابلاً للتشغيل في `dist\CSCN_portal\` عبر PyInstaller.

## هيكل المشروع (Project Structure)

```
CSCN_portal/
├── main.py                # نقطة الدخول: seed_initial_data() + build_services()
├── config/                # الإعدادات وتهيئة السجلّات
├── database/              # المحرّك، الجلسة، Base/AuditMixin، هجرات Alembic
├── domain/                # الكيانات (entities) والواجهات (interfaces)
├── application/           # الخدمات (services) و DTOs
├── infrastructure/        # المستودعات (repositories)
├── ui/                    # واجهة PySide6 (pages, widgets, dialogs, themes)
├── tests/                 # unit / integration
└── data/                  # قاعدة البيانات، المرفوعات، التقارير، السجلّات (غير متعقّبة في git)
```

## ملاحظات معمارية (Notes)

- **مصدر السكيمة:** يتم إنشاء الجداول وقت التشغيل عبر `Base.metadata.create_all`
  (يُنشئ الجداول الناقصة فقط)، مع بقاء **Alembic** متاحًا للهجرات المُصدَّرة.
- **الجلسة:** جلسة `scoped_session` مشتركة لعمر التطبيق (تطبيق أحادي المستخدم)؛ عمليات
  الكتابة في المستودع الأساسي تُرجِع للحالة السابقة (rollback) عند الخطأ.
- **نظام التصميم (UI):** كل الألوان/الخطوط/المسافات معرّفة كـ Tokens في `ui/themes/`
  (`colors.py`, `typography.py`, `tokens.py`)، وتُولّد ورقة الأنماط من
  `ui/themes/stylesheet.py:build_stylesheet()` (مصدر واحد للحقيقة بدل ملف QSS ثابت).
  مكوّنات مشتركة في `ui/widgets/` (`Card`, `PageHeader`, `StatCard`, `StatusBadge`,
  `IconButton`, `Toast`, `LoadingOverlay`) و`ui/dialogs/base_dialog.py`. الأيقونات عبر
  qtawesome (`ui/themes/icons.py`). لتفعيل خط عربي مخصص ضع ملفات Cairo/Tajawal في
  `ui/resources/fonts/`.

## الترخيص (License)

راجع ملف [LICENSE](LICENSE).
