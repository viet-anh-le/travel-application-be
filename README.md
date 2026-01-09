# Travel Application Backend (Nomado)

Đây là backend server cho ứng dụng hỗ trợ du lịch Nomado, cung cấp các tính năng quản lý thông tin du lịch, lập kế hoạch lịch trình thông minh bằng AI (RAG), và tích hợp các công cụ tiện ích như nhận diện giọng nói và tổng hợp tiếng nói (TTS).

## Tính Năng Chính

- **Quản lý dữ liệu du lịch**: CRUD cho các thực thể: Thành phố, Địa điểm, Món ăn, Lễ hội, Cơ sở lưu trú.
- **Lập kế hoạch du lịch AI (RAG Agent)**:
  - Tự động tạo lịch trình du lịch dựa trên yêu cầu người dùng.
  - Sử dụng LangChain và mô hình ngôn ngữ lớn (LLM) để truy xuất thông tin từ cơ sở dữ liệu kiến thức (Vector Store).
  - Hỗ trợ trò chuyện, hỏi đáp về du lịch.
- **Xác thực & Người dùng**:
  - Đăng ký/Đăng nhập qua Email (JWT) và Google OAuth2.
  - Xác thực email qua OTP.
  - Quản lý thông tin cá nhân, đổi mật khẩu.
- **Tích hợp Google Calendar**: Đồng bộ lịch trình du lịch trực tiếp vào lịch cá nhân của người dùng.
- **Tiện ích giọng nói**:
  - **Wake Word Detection**: Phát hiện từ khóa đánh thức (sử dụng `openWakeWord`).
  - **Speech-to-Text (STT)**: Chuyển giọng nói thành văn bản.
- **Dự báo thời tiết**: Tích hợp API dự báo thời tiết cho các địa điểm du lịch.

## Công Nghệ Sử Dụng

- **Ngôn ngữ**: Python 3.10+
- **Framework**: FastAPI
- **Database**:
  - MongoDB (lưu trữ dữ liệu chính) - Driver: `motor`, ODM: `beanie`
  - ChromaDB (Vector Database cho RAG)
  - Redis (Caching & Chat History)
- **AI & LLM**:
  - LangChain (Framework cho ứng dụng LLM)
  - Google Gemini / Groq / Ollama (LLM Providers)
  - HuggingFace Embeddings
- **Khác**: Docker, Docker Compose, Google Auth Library.

## Cài Đặt & Chạy Ứng Dụng

### Yêu cầu tiên quyết

- Python 3.10 trở lên
- MongoDB (đang chạy)
- Redis (đang chạy)
- Tài khoản và API Key của các dịch vụ bên thứ 3 (Google Cloud, Groq, WeatherAPI, v.v.)

### Chạy ứng dụng

1.  **Clone repository:**

    ```bash
    git clone <your-repo-url>
    cd viet-anh-le-travel-application-be
    ```

2.  **Tạo môi trường ảo (khuyến nghị):**

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Cài đặt dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    _Lưu ý: cần cài đặt các dependencies cho module RAG:_

    ```bash
    pip install -r RAG/requirements.txt
    ```

4.  **Cấu hình biến môi trường:**
    Tạo file `.env` tại thư mục gốc và điền các thông tin sau:

    ```env
    # Database
    MONGO_URL=mongodb://localhost:27017

    # Authentication
    DEV_JWT_SECRET_KEY=your_secret_key
    CORS_ALLOW_ORIGINS=http://localhost:3000

    # Mailer (Gmail SMTP)
    MAILER_ACCOUNT=your_email@gmail.com
    MAILER_PASSWORD=your_app_password

    # Google OAuth & Calendar
    CALENDAR_CLIENT_ID=your_google_client_id
    CALENDAR_CLIENT_SECRET=your_google_client_secret
    CALENDAR_REDIRECT_URI=http://localhost:8000/auth/google-calendar/redirect

    # AI & RAG Keys
    GEMINI_API_KEY=your_gemini_key
    GROQ_API_KEY=your_groq_key
    WEATHER_API_KEY=your_weather_api_key
    OPEN_WEATHER_API_KEY=your_open_weather_key
    ```

5.  **Khởi chạy server:**
    ```bash
    # Chạy trực tiếp script
    bash run.sh
    ```
