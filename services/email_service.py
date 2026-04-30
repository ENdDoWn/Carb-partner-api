import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings

class EmailService:
    def __init__(self):
        self.smtp_email = settings.SMTP_EMAIL
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def generate_verification_code(self) -> str:
        """Generate a 6-digit verification code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    async def send_verification_email(self, to_email: str, code: str) -> bool:
        """Send verification code to user's email"""
        try:
            message = MIMEMultipart()
            message["From"] = self.smtp_email
            message["To"] = to_email
            message["Subject"] = "ยืนยันตัวตนของคุณ - Carb Partner"

            html_body = f"""
            <html dir="rtl">
                <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #333;">ยืนยันตัวตนของคุณ</h2>
                        <p style="color: #666; font-size: 16px;">
                            คุณได้ขอการยืนยันตัวตนสำหรับบัญชี Carb Partner
                        </p>
                        <p style="color: #666; font-size: 16px;">
                            กรุณากรอกรหัสยืนยันด้านล่างในแอพพลิเคชัน:
                        </p>
                        <div style="background-color: #f0f0f0; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                            <p style="font-size: 36px; font-weight: bold; color: #6CD2D9; letter-spacing: 5px; margin: 0;">
                                {code}
                            </p>
                        </div>
                        <p style="color: #999; font-size: 14px;">
                            รหัสนี้จะหมดอายุใน 10 นาที
                        </p>
                        <p style="color: #999; font-size: 14px;">
                            หากคุณไม่ได้ขอสิ่งนี้ โปรดละเว้นข้อความนี้
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="color: #999; font-size: 12px;">
                            © 2026 Carb Partner. All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """

            message.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(message)

            return True
        except Exception as e:
            print(f"Failed to send verification email: {str(e)}")
            return False
