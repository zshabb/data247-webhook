import os
from flask import Flask, request, jsonify
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load from environment
DATA247_API_KEY = os.getenv("DATA247_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

MESSAGE_TEMPLATES = {
    "locksmith": "For locksmith service, call: (877) 772-3322",
    "hvac": "For AC service, call: (877) 700-1122"
}

app = Flask(__name__)

def get_mms_gateway(phone_number):
    url = "https://api.data247.com/v3.0"
    params = {"key": DATA247_API_KEY, "api": "MT", "phone": phone_number}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data.get("mmsGateway") if data.get("status") == "OK" else None

def send_email(to_address, body):
    msg = MIMEText(body, 'plain')
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_address
    msg['Subject'] = ""

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

@app.route("/send-text", methods=["POST"])
def webhook_handler():
    data = request.get_json()
    phone = data.get("phone_number")
    msg_type = data.get("message_type", "").lower().strip()
    if not phone or msg_type not in MESSAGE_TEMPLATES:
        return jsonify({"success": False, "error": "Invalid input"}), 400

    gateway = get_mms_gateway(phone)
    if not gateway:
        return jsonify({"success": False, "error": "Could not get gateway"}), 500

    try:
        send_email(gateway, MESSAGE_TEMPLATES[msg_type])
        return jsonify({"success": True, "gateway": gateway}), 200
    except Exception:
        return jsonify({"success": False, "error": "Email send failed"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
