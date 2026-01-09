import os
import aiosmtplib
from email.message import EmailMessage

# --- Configuration ---
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("MAILER_ACCOUNT")
SMTP_PASSWORD = os.getenv("MAILER_PASSWORD")

# --- Templates ---
# Copy nguyên văn HTML từ Node.js sang string của Python
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="vi" style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Xác minh Email</title>
  </head>
  <body style="margin: 0; padding: 8px; background-color: #faf8f2; color: #333; font-family: Arial, Helvetica, sans-serif;">
    <div style="max-width: 520px; margin: 0 auto; background: #ffffff; padding: 40px 30px; border-radius: 12px;">
      <div style="text-align: center; margin-bottom: 25px;">
        <p style="font-size: 26px; font-weight: bold; color: #000; letter-spacing: 2px; margin: 0;">NOMADO</p>
      </div>
      <div style="text-align: center; margin-top: 10px;">
        <p style="font-size: 40px; font-weight: bold; color: #061bff; letter-spacing: 8px; margin: 0;">{{CODE}}</p>
      </div>
      <h2 style="text-align: center; font-size: 26px; color: #333; margin-top: 30px; margin-bottom: 10px;">Xác minh địa chỉ email của bạn</h2>
      <p style="text-align: center; font-size: 15px; line-height: 22px;">
        Bạn sắp hoàn tất rồi! Hãy sử dụng mã xác minh dưới đây để tiếp tục hành trình cùng chúng tôi.
        Lưu ý rằng mã này chỉ có hiệu lực trong <b>2 phút</b>, vì vậy hãy sử dụng ngay nhé.
      </p>
      <p style="text-align: center; font-size: 13px; color: #777; line-height: 20px;">
        Nếu bạn có bất kỳ câu hỏi nào, vui lòng truy cập trang FAQ hoặc liên hệ với chúng tôi tại
        <a href="mailto:help@example.com" style="color:#061bffff;">help@example.com</a>.
      </p>
    </div>
  </body>
</html>"""

GOOGLE_SUCCESS_TEMPLATE = """<!DOCTYPE html>
<html lang="vi" style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;">
  <head>
    <meta charset="UTF-8" />
    <title>Chào mừng đến với Nomado</title>
  </head>
  <body style="margin: 0; padding: 8px; background-color: #faf8f2; color: #333; font-family: Arial, Helvetica, sans-serif;">
    <div style="max-width: 520px; margin: 0 auto; background: #ffffff; padding: 40px 30px; border-radius: 12px;">
      <div style="text-align: center; margin-bottom: 25px;">
        <p style="font-size: 26px; font-weight: bold; color: #000; letter-spacing: 2px; margin: 0;">NOMADO</p>
      </div>
      <h2 style="text-align: center; font-size: 26px; color: #333; margin-top: 24px; margin-bottom: 10px;">
        Tài khoản Nomado của bạn đã được tạo thành công 🎉
      </h2>
      <p style="text-align: center; font-size: 15px; line-height: 23px; color:#555">
        Xin chào <b>{{NAME}}</b>, <br/>
        Cảm ơn bạn đã đăng ký bằng Google! Tài khoản Nomado của bạn đã được kích hoạt và sẵn sàng sử dụng.
      </p>
      <p style="text-align: center; margin-top: 20px;">
        <a href="{{LOGIN_LINK}}" style="display:inline-block; background:#061bff; color:white; padding:12px 26px; text-decoration:none; border-radius:8px; font-weight:bold;">
          Bắt đầu hành trình
        </a>
      </p>
      <p style="text-align: center; font-size: 13px; color: #777; line-height: 20px; margin-top: 32px;">
        Nếu bạn không thực hiện hành động này, vui lòng bỏ qua email hoặc liên hệ với chúng tôi ngay tại
        <a href="mailto:help@example.com" style="color:#061bff;">help@example.com</a>.
      </p>
    </div>
  </body>
</html>"""

GOOGLE_ADD_SCHEDULE_SUCCESS = """<!DOCTYPE html>
<html lang="vi" style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;">
  <head>
    <meta charset="UTF-8" />
    <title>Lịch trình đã được thêm vào Google Calendar</title>
  </head>
  <body style="margin: 0; padding: 8px; background-color: #faf8f2; color: #333; font-family: Arial, Helvetica, sans-serif;">
    <div style="max-width: 520px; margin: 0 auto; background: #ffffff; padding: 40px 30px; border-radius: 12px;">
      <div style="text-align: center; margin-bottom: 25px;">
        <p style="font-size: 26px; font-weight: bold; color: #000; letter-spacing: 2px; margin: 0;">NOMADO</p>
      </div>
      <h2 style="text-align: center; font-size: 24px; color: #333; margin-top: 10px; margin-bottom: 14px;">
        Lịch trình của bạn đã được thêm vào Google Calendar
      </h2>
      <p style="text-align: center; font-size: 15px; line-height: 23px; color:#555">
        Xin chào <b>{{NAME}}</b>, <br/>
        Lịch trình <b>{{TRIP_TITLE}}</b> đã được đồng bộ thành công với Google Calendar.
      </p>
      <div style="background:#f6f6ff; border-left:4px solid #061bff; padding:14px 18px; border-radius:8px; margin-top: 22px; font-size:14px; line-height:22px;">
        <p><b>Tên lịch trình:</b> Khám phá du lịch tại {{TRIP_TITLE}} cùng Nomado</p>
        <p><b>Thời gian:</b> {{START_DATE}} – {{END_DATE}}</p>
        <p><b>Tổng số hoạt động:</b> {{TOTAL_EVENTS}}</p>
      </div>
      <p style="text-align: center; margin-top: 24px;">
        <a href="{{CALENDAR_LINK}}" style="display:inline-block; background:#061bff; color:white; padding:12px 26px; text-decoration:none; border-radius:8px; font-weight:bold;">
          Mở Google Calendar
        </a>
      </p>
      <p style="text-align: center; font-size: 13px; color: #777; line-height: 20px; margin-top: 32px;">
        Nếu bạn không yêu cầu thêm lịch trình này, vui lòng bỏ qua email hoặc liên hệ ngay với chúng tôi tại
        <a href="mailto:help@example.com" style="color:#061bff;">help@example.com</a>.
      </p>
    </div>
  </body>
</html>"""

# --- Helper Function ---
async def _send_email_core(to_email: str, subject: str, text_content: str, html_content: str, from_email: str = None):
    """Hàm nội bộ để gửi email xử lý kết nối SMTP"""
    message = EmailMessage()
    
    # Xử lý sender name: "Nomado <no-reply@nomado.com>"
    sender = from_email or f"Nomado <{SMTP_USER}>"
    
    message["From"] = sender
    message["To"] = to_email
    message["Subject"] = subject
    
    # Thiết lập nội dung Text (fallback)
    message.set_content(text_content)
    # Thiết lập nội dung HTML
    message.add_alternative(html_content, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            use_tls=True  
        )
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")

async def mail_template(payload: dict):
    """
    payload: {from_email, to, subject, text, code}
    """
    html = HTML_TEMPLATE.replace("{{CODE}}", payload['code'])
    
    await _send_email_core(
        from_email=payload.get('from'),
        to_email=payload['to'],
        subject=payload['subject'],
        text_content=payload['text'],
        html_content=html
    )

async def send_google_success_email(payload: dict):
    """
    payload: {to, name, loginLink}
    """
    html = GOOGLE_SUCCESS_TEMPLATE \
        .replace("{{NAME}}", payload['name']) \
        .replace("{{LOGIN_LINK}}", payload['login_link'])

    await _send_email_core(
        to_email=payload['to'],
        subject=f"Welcome to Nomado, {payload['name']}!",
        text_content="Your Nomado account has been created successfully.",
        html_content=html
    )

async def send_google_add_schedule_email(payload: dict):
    """
    payload: {to, name, tripTitle, startDate, endDate, totalEvents, calendarLink}
    """
    # Python str.replace() mặc định thay thế tất cả (giống replaceAll của JS)
    html = GOOGLE_ADD_SCHEDULE_SUCCESS \
        .replace("{{NAME}}", payload['name']) \
        .replace("{{TRIP_TITLE}}", payload['tripTitle']) \
        .replace("{{START_DATE}}", payload['startDate']) \
        .replace("{{END_DATE}}", payload['endDate']) \
        .replace("{{TOTAL_EVENTS}}", str(payload['totalEvents'])) \
        .replace("{{CALENDAR_LINK}}", payload['calendarLink'])

    await _send_email_core(
        to_email=payload['to'],
        subject=f'Lịch trình "{payload["tripTitle"]}" đã được thêm vào Google Calendar',
        text_content=f'Lịch trình "{payload["tripTitle"]}" đã được đồng bộ thành công với Google Calendar.',
        html_content=html
    )