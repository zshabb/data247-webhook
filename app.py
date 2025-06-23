from flask import Flask, request, jsonify
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA247_API_KEY = "YOUR_DATA247_API_KEY"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "your.email@gmail.com"
EMAIL_PASSWORD = "your_app_password"

MESSAGE_TEMPLATES = {
    "locksmith": "For locksmith service, call: (877) 772-3322",
    "hvac": "For AC service, call: (877) 700-1122"
}

app = Flask(__name__)

def get_mms_gateway(phone_number):
    url = "https://api.data247.com/v3.0"
    params = {"key": DATA247_API_KEY, "api": "MT", "phone": phone_number}
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("mmsGateway") if data.get("status") == "OK" else None
    except Exception as e:
        print("Gateway error:", e)
        return None

def send_email(to_address, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_address
        msg['Subject'] = ""
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Email error:", e)
        return False

@app.route("/send-text", methods=["POST"])
def webhook_handler():
    data = request.get_json()
    phone = data.get("phone_number")
    msg_type = data.get("message_type", "").lower().strip()
    if not phone or msg_type not in MESSAGE_TEMPLATES:
        return jsonify({"success": False, "error": "Invalid input"}), 400

    message = MESSAGE_TEMPLATES[msg_type]
    gateway = get_mms_gateway(phone)
    if not gateway:
        return jsonify({"success": False, "error": "Could not get gateway"}), 500

    success = send_email(gateway, message)
    return jsonify({"success": success}), 200 if success else 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
