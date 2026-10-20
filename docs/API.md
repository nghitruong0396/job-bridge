# Tài liệu API

## 1. Quyền truy cập

| Đối tượng | Quyền |
|---|---|
| Super admin | Tạo tài khoản HR hoặc nhân viên qua API đăng ký |
| HR (`HR`) | Quản lý tuyển dụng, ứng viên, hồ sơ và xác nhận thưởng |
| Nhân viên (`EMPLOYEE`) | Xem tin đang mở còn hạn, giới thiệu ứng viên, xem hồ sơ và thưởng của mình |

Super admin được xác định bằng `is_superuser=True` và tài khoản phải đang hoạt động. Chỉ có `is_staff=True` không đủ để tạo tài khoản qua API. Quyền HR/nhân viên của các API tuyển dụng xét trường `role`;

## 2. Đăng nhập bằng session và CSRF

Các API dùng cookie session của Django.

1. Gọi `GET /api/accounts/login/` để nhận cookie `csrftoken` và giá trị `csrfToken` trong JSON.
2. Gọi `POST /api/accounts/login/` với email, mật khẩu và header `X-CSRFToken` với giá trị vừa nhận; gửi kèm cookie.
3. Đăng nhập thành công trả cookie session và `csrfToken` mới. Dùng token mới cho các request tiếp theo.

Để tạo super admin cần chạy câu lệnh này với email có domain công ty:

```bash
docker compose exec web python manage.py createsuperuser
```

Domain email công ty được cấu hình bằng `COMPANY_EMAIL_DOMAIN`, mặc định là `jobbridge.com`.

## 3. API tài khoản

| Method | URL | Chức năng | Quyền |
|---|---|---|---|
| GET | `/api/accounts/login/` | Lấy CSRF token | Không cần đăng nhập |
| POST | `/api/accounts/login/` | Đăng nhập | Không cần đăng nhập |
| POST | `/api/accounts/register/` | Tạo tài khoản HR hoặc nhân viên | Super admin |
| POST | `/api/accounts/logout/` | Đăng xuất | Đã đăng nhập |
| GET | `/api/accounts/me/` | Xem tài khoản đang đăng nhập | Đã đăng nhập |

### Đăng nhập

```json
{
  "email": "admin@jobbridge.com",
  "password": ""
}
```

### Tạo tài khoản

`POST /api/accounts/register/` dành cho super admin đã đăng nhập.

| Trường | Bắt buộc | Ý nghĩa |
|---|---|---|
| `email` | Có | Email công ty, tối đa 254 ký tự, không trùng |
| `password` | Có | Mật khẩu |
| `employee_code` | Có | Mã nhân viên, tối đa 30 ký tự, không trùng |
| `full_name` | Có | Họ tên, tối đa 150 ký tự |
| `department` | Không | Bộ phận, tối đa 150 ký tự |
| `phone` | Không | Số điện thoại, tối đa 20 ký tự |
| `role` | Không | `HR` hoặc `EMPLOYEE`; mặc định `EMPLOYEE` |

Ví dụ tạo HR:

```json
{
  "email": "nhansu1@jobbridge.com",
  "password": "tintinA123",
  "employee_code": "NV100",
  "full_name": "Nhân sự 1",
  "department": "Nhân sự",
  "phone": "0901000001",
  "role": "HR"
}
```

Để tạo nhân viên, đổi `role` thành `EMPLOYEE` hoặc bỏ trường này:

```json
{
  "user": {
    "employee_code": "NV101",
    "email": "nhanvien1@jobbridge.com",
    "full_name": "Nhân viên 1",
    "department": "Kế toán",
    "phone": "0901000002",
    "role": "EMPLOYEE"
  }
}
```

## 4. API tin tuyển dụng

| Method | URL | Chức năng | Quyền |
|---|---|---|---|
| GET | `/api/recruitment/jobs/` | Danh sách tin tuyển dụng | HR, nhân viên |
| POST | `/api/recruitment/jobs/` | Tạo tin | HR |
| GET | `/api/recruitment/jobs/{id}/` | Chi tiết tin | HR, nhân viên |
| PUT | `/api/recruitment/jobs/{id}/` | Cập nhật tin | HR |
| PATCH | `/api/recruitment/jobs/{id}/` | Cập nhật một phần tin | HR |
| DELETE | `/api/recruitment/jobs/{id}/` | Xóa tin tuyển dụng | HR |
| POST | `/api/recruitment/jobs/{id}/open/` | Mở tin | HR |
| POST | `/api/recruitment/jobs/{id}/close/` | Đóng tin | HR |

Nhân viên chỉ xem được tin `OPEN`, chưa bị xóa và còn hạn. HR xem được các tin chưa bị xóa ở mọi trạng thái. Tin đã xóa có `is_deleted=True` và không còn xuất hiện trong các API tin tuyển dụng.

Body tạo tin hoặc cập nhật đầy đủ bằng PUT:

```json
{
  "title": "Lập trình viên Python",
  "department": "Công nghệ thông tin",
  "description": "Phát triển ứng dụng tuyển dụng nội bộ.",
  "requirements": "Có kiến thức Python, Django và SQL.",
  "number_of_positions": 2,
  "bonus": "3000000.00",
  "status": "OPEN",
  "deadline": "2027-12-31"
}
```

Các trường bắt buộc khi tạo/PUT: `title`, `department`, `description`, `requirements`, `deadline`. Khi tạo, `number_of_positions` mặc định 1, `bonus` mặc định 0, `status` mặc định `DRAFT`. Số lượng tuyển phải lớn hơn 0, tiền thưởng không âm. Trạng thái hợp lệ: `DRAFT`, `OPEN`, `CLOSED`.

Response gồm các trường trên và `id`, `created_by`, `created_at`, `updated_at`, `is_deleted`.

## 5. API ứng viên

| Method | URL | Chức năng | Quyền |
|---|---|---|---|
| GET | `/api/recruitment/candidates/` | Danh sách | HR |
| GET | `/api/recruitment/candidates/{id}/` | Chi tiết | HR |
| PUT | `/api/recruitment/candidates/{id}/` | Cập nhật | HR |
| PATCH | `/api/recruitment/candidates/{id}/` | Cập nhật một phần | HR |

Các trường cho phép sửa: `full_name`, `email`, `phone`, `address`, `dob`, `working_experience`, `note`. PUT bắt buộc `full_name` và `phone`; PATCH chỉ cần các trường muốn sửa. Response bổ sung `id`, `created_at`, `updated_at`.

Số điện thoại không được trùng ứng viên khác. `note` là ghi chú nội bộ. Ứng viên được tạo khi nhân viên gửi giới thiệu.

## 6. API hồ sơ giới thiệu

| Method | URL | Chức năng | Quyền |
|---|---|---|---|
| GET | `/api/recruitment/applications/` | Danh sách hồ sơ | HR: tất cả; nhân viên: của mình |
| POST | `/api/recruitment/applications/` | Giới thiệu ứng viên | Nhân viên |
| GET | `/api/recruitment/applications/{id}/` | Chi tiết hồ sơ | HR hoặc người giới thiệu |
| PUT | `/api/recruitment/applications/{id}/` | Lưu ghi chú nội bộ | HR |
| PATCH | `/api/recruitment/applications/{id}/` | Sửa ghi chú nội bộ | HR |
| GET | `/api/recruitment/applications/{id}/cv/` | Tải file CV | HR hoặc người giới thiệu |
| POST | `/api/recruitment/applications/{id}/upload-cv/` | Tải lên/thay CV | Người giới thiệu |
| POST | `/api/recruitment/applications/{id}/change-stage/` | Chuyển trạng thái | HR |
| GET | `/api/recruitment/applications/{id}/history/` | Xem lịch sử trạng thái | HR hoặc người giới thiệu |
| POST | `/api/recruitment/applications/{id}/confirm-reward/` | Xác nhận thưởng | HR |

### Giới thiệu ứng viên

Body JSON khi chưa gửi CV:

```json
{
  "job": 1,
  "full_name": "Ứng viên 1",
  "phone": "0902000002",
  "email": "ungvien1@example.com",
  "address": "Thành phố Hồ Chí Minh",
  "dob": "2003-05-20",
  "working_experience": "Đã thực tập lập trình Python."
}
```

`job`, `full_name`, `phone` là bắt buộc. Các trường còn lại và `cv` không bắt buộc trong API. Nếu có CV, gửi các trường này cùng file `cv` bằng multipart. CV hỗ trợ PDF, DOC, DOCX, tối đa 5 MB. API `upload-cv` yêu cầu trường file `cv`.

Quy tắc:

- Job phải đang mở, còn hạn và chưa xóa.
- Không được giới thiệu chính mình theo số điện thoại hoặc email.
- Nếu số điện thoại đã tồn tại, sử dụng ứng viên đã có.
- Một ứng viên chỉ có một hồ sơ cho cùng một job.
- `referrer` được lấy từ tài khoản đang đăng nhập. `bonus_amount` lưu mức thưởng của job tại thời điểm giới thiệu.

Response hồ sơ gồm `id`, `job`, thông tin `candidate`, `referrer`, URL tải `cv` , `current_stage`, `bonus_amount`, `applied_at`, `updated_at`. HR xem thêm `note` của hồ sơ và của ứng viên. Response tạo hồ sơ trả dữ liệu theo quyền nhân viên.

### Ghi chú và chuyển trạng thái

PUT/PATCH hồ sơ chỉ sửa `note`, ví dụ `{"note": "Đã liên hệ ứng viên."}`. Đổi trạng thái phải gọi API `change-stage`:

```json
{
  "to_stage": "SCREENING",
  "note": "Hồ sơ phù hợp, chuyển sang sàng lọc."
}
```

`to_stage` bắt buộc, `note` không bắt buộc. Các bước hợp lệ:

```text
APPLIED → SCREENING → INTERVIEW → HIRED
    ↓          ↓           ↓
  FAILED     FAILED      FAILED
```

`HIRED` và `FAILED` là trạng thái kết thúc. Mỗi lần chuyển trạng thái được lưu vào lịch sử. Lịch sử trả `id`, `application`, `from_stage`, `to_stage`, `changed_at`; HR xem thêm `changed_by` và ghi chú nội bộ `note`.

### Xác nhận thưởng

Gọi POST `confirm-reward`. Chỉ xác nhận khi hồ sơ ở trạng thái `HIRED` và chưa có thưởng. Số tiền lấy từ `bonus_amount` của hồ sơ; mỗi hồ sơ chỉ được xác nhận thưởng một lần.

## 7. API thưởng giới thiệu

| Method | URL | Chức năng | Quyền |
|---|---|---|---|
| GET | `/api/recruitment/rewards/` | Danh sách thưởng | HR: tất cả; nhân viên: của mình |
| GET | `/api/recruitment/rewards/{id}/` | Chi tiết thưởng | HR hoặc nhân viên nhận thưởng |
| GET | `/api/recruitment/rewards/summary/` | Tổng tiền và số khoản thưởng | HR: tất cả; nhân viên: của mình |

Bản ghi thưởng gồm `id`, `application`, `employee`, `total_amount`, `confirmed_by`, `created_at`. Tạo thưởng thông qua API `confirm-reward`.
