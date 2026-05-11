from twilio.rest import Client

def send_otp(phone, otp):
    print("📱 WhatsApp function called with:", phone, otp)

    try:
        client = Client(
            'ACc0397e0f7b10190dc09e35903741261e',   
            'e4a055e29f58076c1a74cad9dcf7bb5c'        
        )

        message = client.messages.create(
            from_="whatsapp:+14155238886",
            to=f"whatsapp:{phone}",
            body=f"🔐 Your verification code is: {otp}"
        )

        print("✅ Message sent:", message.sid)
        return message.sid

    except Exception as e:
        print("❌ WhatsApp send failed:", e)
        return None