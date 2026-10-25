# MariaDB Schema — Example / نمونه

> Replace this file with YOUR own MariaDB schema before using real queries.

## Table `customers` / مشتریان

| Column | MariaDB type | توضیح |
| --- | --- | --- |
| `id` | INT PRIMARY KEY | شناسه مشتری |
| `name` | VARCHAR(200) | نام مشتری |
| `city` | VARCHAR(100) | شهر؛ نام شهرها به فارسی ذخیره می‌شود |
| `created_at` | DATETIME | زمان ثبت‌نام با تاریخ میلادی |

## Table `orders` / سفارش‌ها

| Column | MariaDB type | توضیح |
| --- | --- | --- |
| `id` | INT PRIMARY KEY | شناسه سفارش |
| `customer_id` | INT NOT NULL | شناسه مشتری |
| `total_amount` | DECIMAL(15,2) | مبلغ کل سفارش |
| `order_date` | DATETIME | تاریخ سفارش به میلادی در دیتابیس |
| `status` | VARCHAR(30) | `completed`, `pending`, `cancelled` |

## Relationship / روابط

- `orders.customer_id` references `customers.id`.

## Business rules / قواعد کسب‌وکار

- «فروش» = مجموع `orders.total_amount` با شرط `orders.status = 'completed'`.
- «تعداد سفارش» = `COUNT(orders.id)`.
- «مشتریان بدون سفارش» = مشتریانی که در جدول `orders` سفارشی ندارند.
- مقدار شهر تهران به صورت `'تهران'` ذخیره شده است.
- تاریخ‌ها در ستون‌های `DATETIME` به میلادی ذخیره شده‌اند.
- برای «ماه جاری/ماه گذشته» ماه میلادی را در نظر بگیر، مگر سؤال به‌صراحت ماه شمسی بخواهد.
- اگر سؤال درباره ماه شمسی است و هیچ نگاشت تقویمی ارائه نشده، `CANNOT_ANSWER` بده.
