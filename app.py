from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables from .env
load_dotenv()

# Twilio credentials from .env
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

MESSAGE_TEMPLATES = {
    "locksmith": "For locksmith service, call: (877) 772-3322",
    "hvac": "For AC service, call: (877) 700-1122"
}

# Map carrier names to their MMS gateways
CARRIER_GATEWAY_MAP = {
    "Verizon Wireless": "vzwpix.com",
    "AT&T": "mms.att.net",
    "T-Mobile": "tmomail.net",
    "Sprint": "pm.sprint.com",
    "US Cellular": "mms.uscc.net"
}

app = Flask(__name__)

def get_mms_gateway(phone_number):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        number = client.lookups.phone_numbers(phone_number).fetch(type='carrier')
        carrier_name = number.carrier.get('name')
        print(f"Detected carrier: {carrier_name}")

        if not carrier_name or carrier_name not in CARRIER_GATEWAY_MAP:
            return None

        local_number = phone_number.replace("+1", "")  # Remove +1 country code
        domain = CARRIER_GATEWAY_MAP[carrier_name]
        return f"{local_number}@{domain}"
    except Exception as e:
        print("Carrier lookup error:", e)
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
