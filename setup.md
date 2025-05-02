
Setup evironment
    python3 -m venv venv

    source venv\bin\activate
1. Cài đặt Django:
```bash
pip install django
```

3. Chạy migrations để tạo cơ sở dữ liệu:
```bash
python manage.py migrate
```

4. Tạo dữ liệu mẫu (nếu cần):
```bash
python create_sample_data.py
```

5. Chạy server:
```bash
python manage.py runserver
```
6. Create admini user
```bash
python manage.py createsuperuser
```

