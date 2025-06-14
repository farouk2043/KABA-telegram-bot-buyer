# استخدم صورة Python أساسية
FROM python:3.10-slim-buster

# اضبط دليل العمل داخل الحاوية
WORKDIR /app

# انسخ ملف المتطلبات أولاً لتسريع عملية البناء (إذا لم تتغير المتطلبات)
COPY requirements.txt requirements.txt

# قم بتثبيت التبعيات
RUN pip install --no-cache-dir -r requirements.txt

# انسخ بقية الكود
COPY . .

# حدد المنفذ الذي ستستمع عليه الخدمة (Cloud Run سيوفر هذا كمتغير بيئة)
ENV PORT 8080

# حدد الأمر الذي سيتم تنفيذه عند بدء تشغيل الحاوية
CMD exec uvicorn app:main --host 0.0.0.0 --port $PORT
