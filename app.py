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
    "locksmith": "For Locksmith Service, call: (877) 406-1684",
    "hvac": "For AC Service, call: (855) 539-0127",
    "plumbing": "For Plumbing Service, call: (844) 655-8383",
    "electrician": "For Electrician Service, call: (773) 337-2221 ",
    "roofing": "For Roofing service, call: (773) 337-2298",
    "garage door": "For Garage Door Service, call: (855) 583-7986",
    "dumpster": "For Dumpster Rental, call: (855) 482 0825"
}

# Map carrier names to their MMS gateways
CARRIER_GATEWAY_MAP = {
    "Verizon Wireless": "vzwpix.com",
    "AT&T": "mms.att.net",
    "AT&T Wireless": "mms.att.net",
    "T-Mobile": "tmomail.net",
    "T-Mobile USA, Inc.": "tmomail.net",
    "Sprint": "pm.sprint.com",
    "US Cellular": "mms.uscc.net",
    "Boost Mobile": "myboostmobile.com",
    "Cricket": "mms.cricketwireless.net",
    "Google Fi": "msg.fi.google.com",
    "MetroPCS": "mymetropcs.com",
    "Republic Wireless": "text.republicwireless.com",
    "Straight Talk": "vzwpix.com",  # Typically uses Verizon’s gateway
    "Tracfone": "mmst5.tracfone.com",
    "Virgin Mobile": "vmobl.com",
    "Xfinity Mobile": "vzwpix.com",  # Uses Verizon's network
    "Consumer Cellular": "mailmymobile.net",
    "C Spire": "cspire1.com",
    "Page Plus": "vzwpix.com",
    "Ting": "message.ting.com",
    "FreedomPop": "txt.att.net",  # Network dependent
    "Net10": "mms.att.net",       # Network dependent
    "Visible": "vzwpix.com"
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
