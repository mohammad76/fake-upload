# Quick Start Guide - راهنمای سریع

## بدون نیاز به سرور (توصیه می‌شود) - No Server Needed

### روش 1: استفاده از سرویس Public Null (بهترین روش)

این روش نیازی به راه‌اندازی سرور ندارد و مستقیم به یک سرویس عمومی آپلود می‌کند:

```bash
# آپلود 400 گیگ در 24 ساعت (بدون نیاز به سرور)
python fake_upload.py -g 400 --null-service

# آپلود 200 گیگ با 8 thread موازی
python fake_upload.py -g 200 -t 8 --null-service

# آپلود مداوم
python fake_upload.py -g 100 -c --null-service
```

### روش 2: استفاده از httpbin.org

```bash
# آپلود به httpbin.org (سرویس تست عمومی)
python fake_upload.py -g 400 --httpbin
```

---

## با سرور خودتان - With Your Own Server

اگر می‌خواهید سرور خودتان رو راه‌اندازی کنید:

### ترمینال 1: راه‌اندازی سرور
```bash
python dummy_server.py -p 8080
```

### ترمینال 2: شروع آپلود
```bash
python fake_upload.py -g 400 -p 8080
```

---

## پارامترهای مفید - Useful Parameters

| پارامتر | توضیح | مثال |
|---------|-------|------|
| `-g` | مقدار گیگابایت | `-g 400` |
| `-t` | تعداد thread های موازی | `-t 8` |
| `-d` | مدت زمان (ساعت) | `-d 12` |
| `-s` | سایز هر بسته (MB) | `-s 5` |
| `-c` | حالت مداوم | `-c` |
| `--null-service` | استفاده از سرویس public | `--null-service` |

---

## مثال‌های عملی - Practical Examples

### سرعت پایین (50GB در روز):
```bash
python fake_upload.py -g 50 --null-service
```

### سرعت متوسط (200GB در روز):
```bash
python fake_upload.py -g 200 -t 4 --null-service
```

### سرعت بالا (500GB در روز):
```bash
python fake_upload.py -g 500 -t 8 --null-service
```

### سرعت بسیار بالا (1TB در روز):
```bash
python fake_upload.py -g 1000 -t 16 -s 20 --null-service
```

---

## توضیحات سرویس‌های Public

### devnull-as-a-service.com (--null-service)
- ✅ **بهترین گزینه**: سریع و بدون محدودیت
- ✅ داده‌ها به `/dev/null` می‌روند (دور انداخته می‌شوند)
- ✅ نیازی به راه‌اندازی سرور نیست
- ✅ مناسب برای تست و شبیه‌سازی

### httpbin.org (--httpbin)
- ✅ سرویس تست HTTP معتبر
- ⚠️ ممکن است کندتر باشه
- ✅ نیازی به راه‌اندازی سرور نیست

---

## نکات مهم - Important Notes

1. **سرویس‌های public بهترین گزینه هستند** - نیازی به سرور ندارید
2. **تعداد thread ها را تنظیم کنید** - بیشتر = سریعتر (4-16 توصیه می‌شود)
3. **اتصال اینترنت** - این ابزار واقعاً آپلود انجام می‌دهد
4. **Ctrl+C** برای توقف استفاده کنید

---

## عیب‌یابی - Troubleshooting

### خطای اتصال:
```bash
# مطمئن شوید اینترنت فعال است
ping devnull-as-a-service.com

# یا از httpbin استفاده کنید
python fake_upload.py -g 100 --httpbin
```

### سرعت پایین:
```bash
# تعداد thread ها را افزایش دهید
python fake_upload.py -g 400 -t 16 --null-service

# سایز بسته را کم کنید
python fake_upload.py -g 400 -t 8 -s 5 --null-service
```
