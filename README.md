# JobBridge

## Các bước để chạy ứng dụng

### 1. Tạo file env

Tạo file `.env` tại thư mực gốc, lấy nội dung của file `.env.example` đưa vào file `.env`:

```bash
cp .env.example .env
```

### 2. Chạy môi trường Docker

```bash
docker compose up -d --build
```

### 3. Tạo cấu trúc cơ sở dữ liệu

```bash
docker compose exec web python manage.py migrate
```

### 4. Nhập dữ liệu mẫu (tùy chọn)

```bash
docker compose exec web python manage.py loaddata recruitment/fixtures/demo_data.json
```

Fixture cung cấp ba tài khoản và một tin tuyển dụng. Không cần chạy `createsuperuser` nếu sử dụng các tài khoản mẫu này.

Truy cập:

- Website: http://localhost:8000/
- Django Admin: http://localhost:8000/admin/

## Tài khoản demo

Mật khẩu của cả ba tài khoản: `tintinA123`.

| Vai trò | Email | Quyền |
|---|---|---|
| Quản trị viên | admin@jobbridge.com | Django Admin; API cấp tài khoản HR hoặc Employee |
| HR | nhansu@jobbridge.com | Quản lý tin, ứng viên, hồ sơ và xác nhận thưởng |
| Employee | nhanvien@jobbridge.com | Xem tin đang tuyển, giới thiệu ứng viên, theo dõi hồ sơ và thưởng của mình |


