# Fake Upload Generator | ابزار آپلود فیک

ابزار خط فرمان برای شبیه‌سازی آپلود و افزایش نمودار ترافیک آپلود سرور.

## ویژگی‌ها

- ✅ آپلود فیک با داده‌های تصادفی
- ✅ قابل تنظیم: مقدار، سرعت، مدت زمان
- ✅ نمایش پیشرفت به صورت Real-time
- ✅ پشتیبانی از حالت مداوم
- ✅ قابلیت تنظیم سرور و پورت مقصد
- ✅ پروفایل‌های از پیش تعریف شده
- ✅ کنترل سرعت خودکار

## نصب

```bash
# کلون کردن یا دانلود فایل‌ها
cd fake-upload

# قابل اجرا کردن اسکریپت (اختیاری)
chmod +x fake_upload.py
```

## استفاده سریع

### مثال 1: آپلود 400 گیگ در 24 ساعت

```bash
python fake_upload.py -g 400
```

### مثال 2: آپلود 100 گیگ در 12 ساعت

```bash
python fake_upload.py -g 100 -d 12
```

### مثال 3: آپلود مداوم

```bash
python fake_upload.py -g 50 -c
```

### مثال 4: آپلود به سرور خاص

```bash
python fake_upload.py -g 200 -H example.com -p 80
```

## پارامترها

| پارامتر | کوتاه | توضیحات | پیش‌فرض |
|---------|-------|---------|---------|
| `--gigabytes` | `-g` | مقدار گیگابایت برای آپلود | **الزامی** |
| `--host` | `-H` | آدرس سرور مقصد | `localhost` |
| `--port` | `-p` | پورت سرور | `9` |
| `--chunk-size` | `-s` | سایز هر تکه (MB) | `10` |
| `--duration` | `-d` | مدت زمان (ساعت) | `24` |
| `--continuous` | `-c` | آپلود مداوم | `false` |

## راهنمای تنظیم سرور مقصد

### روش 1: استفاده از Discard Service (توصیه می‌شود)

در سیستم‌های Unix/Linux، سرویس discard در پورت 9 وجود دارد که تمام داده‌های دریافتی را دور می‌اندازد.

```bash
# فعال‌سازی discard service در macOS
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.discard.plist

# فعال‌سازی در Linux (با xinetd)
sudo apt-get install xinetd
sudo systemctl enable xinetd
sudo systemctl start xinetd
```

### روش 2: استفاده از netcat

```bash
# شنود در پورت 8080 و دور انداختن داده‌ها
nc -l 8080 > /dev/null
```

### روش 3: سرور HTTP ساده Python

ایجاد فایل `dummy_server.py`:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class DummyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        self.rfile.read(content_length)  # خواندن و دور انداختن
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        pass  # غیرفعال کردن لاگ

httpd = HTTPServer(('', 8080), DummyHandler)
print("سرور در حال اجرا در پورت 8080...")
httpd.serve_forever()
```

سپس:

```bash
python dummy_server.py
```

و در ترمینال دیگر:

```bash
python fake_upload.py -g 100 -p 8080
```

## پروفایل‌های تعریف شده

فایل `config.json` شامل پروفایل‌های از پیش تعریف شده است:

- **default**: 400GB در 24 ساعت
- **light**: 50GB در 24 ساعت  
- **heavy**: 1TB در 24 ساعت
- **continuous**: آپلود مداوم

## نکات مهم

### 1. سرعت اینترنت

این ابزار واقعاً داده ارسال می‌کند، پس:
- از bandwidth شما استفاده می‌کند
- برای تست، از سرور محلی استفاده کنید
- برای آپلود به اینترنت، محدودیت سرعت اینترنت را در نظر بگیرید

### 2. استفاده از CPU و RAM

- تولید داده‌های تصادفی CPU می‌برد
- برای کاهش مصرف، `chunk_size` را کمتر کنید

### 3. مونیتورینگ

برای مشاهده ترافیک واقعی:

```bash
# مشاهده ترافیک شبکه (Linux)
iftop

# مشاهده ترافیک (macOS)
nettop

# مشاهده connections
netstat -an | grep ESTABLISHED
```

## مثال‌های کاربردی

### سناریو 1: تست سرور آپلود

```bash
# راه‌اندازی سرور تست
python dummy_server.py &

# ارسال 10GB در 1 ساعت
python fake_upload.py -g 10 -d 1 -p 8080
```

### سناریو 2: شبیه‌سازی ترافیک مداوم

```bash
# آپلود مداوم با سرعت 20GB در روز
python fake_upload.py -g 20 -c
```

### سناریو 3: تست Load

```bash
# چند instance همزمان
python fake_upload.py -g 50 -d 2 &
python fake_upload.py -g 50 -d 2 &
python fake_upload.py -g 50 -d 2 &
```

## توقف برنامه

برای توقف از `Ctrl+C` استفاده کنید. برنامه آمار نهایی را نمایش می‌دهد.

## عیب‌یابی

### خطای Connection Refused

```bash
# بررسی اینکه سرور در حال شنود است
netstat -an | grep LISTEN | grep <PORT>
```

### سرعت پایین

- سایز `chunk_size` را افزایش دهید
- مطمئن شوید سرور مقصد پاسخگوست
- محدودیت‌های شبکه را بررسی کنید

## هشدار

⚠️ **این ابزار برای تست و شبیه‌سازی است. از آن به صورت مسئولانه استفاده کنید.**

- از آن برای حمله DDoS استفاده نکنید
- فقط روی سرورهای خودتان تست کنید
- محدودیت‌های ISP و هاستینگ را رعایت کنید

## لایسنس

MIT License - استفاده آزاد
