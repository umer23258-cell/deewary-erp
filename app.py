import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email_report(receiver_email, dataframe, report_title):
    try:
        # 1. Setup Email Credentials (from secrets)
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]

        # 2. Create PDF buffer
        pdf_buffer = export_to_pdf(dataframe, report_title)
        
        # 3. Create Email Message
        message = MIMEMultipart()
        message["From"] = f"Deewary.com ERP <{sender_email}>"
        message["To"] = receiver_email
        message["Subject"] = f"🚀 Deewary.com - {report_title} ({datetime.now().strftime('%d %b %Y')})"

        # Email Body (A bit of style)
        body = f"""
        <html>
            <body>
                <h2 style='color: #FF4B4B;'>Deewary.com Construction Management</h2>
                <p>Hello,</p>
                <p>Please find the requested <b>{report_title}</b> attached below in PDF format.</p>
                <hr>
                <p><b>Summary:</b><br>
                Total Records: {len(dataframe)}<br>
                Total Amount: PKR {dataframe['amount'].sum():,.0f}</p>
                <br>
                <p><i>This is an automated report from Deewary.com ERP System.</i></p>
            </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        # 4. Attach PDF
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={report_title}.pdf")
        message.attach(part)

        # 5. Send Email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        return True
    except Exception as e:
        st.error(f"Email Error: {e}")
        return False
