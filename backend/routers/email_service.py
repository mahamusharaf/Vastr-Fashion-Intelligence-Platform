import resend
import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time

# Load environment variables
load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

print(f" Email Service - API Key loaded: {' YES' if resend.api_key else ' NO'}")

# Create router
router = APIRouter(prefix="/api/v1", tags=["email"])


# Request model
class WelcomeEmailRequest(BaseModel):
    email: str
    name: str
    website_url: str = "http://127.0.0.1:5500"


# Clean HTML email template with plain text version
def get_welcome_email_html(name: str, website_url: str) -> str:
    """Generate HTML email with proper URL formatting"""
    # Use simple string concatenation to avoid template issues
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Vastr</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #f6f6f6;
            margin: 0;
            padding: 40px 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        .logo {
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -1px;
            margin-bottom: 1rem;
            color: #000;
        }
        h1 {
            color: #000;
            font-size: 2.2rem;
            font-weight: 300;
            margin-bottom: 1rem;
            line-height: 1.3;
        }
        p {
            color: #333;
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        .button {
            display: inline-block;
            background: #000;
            color: white !important;
            padding: 16px 40px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            margin: 2rem 0;
        }
        .features {
            background: #f8f8f8;
            border-radius: 8px;
            padding: 2rem;
            margin: 2rem 0;
            text-align: left;
        }
        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            gap: 1rem;
        }
        .feature-icon {
            font-size: 1.5rem;
        }
        .footer {
            color: #666;
            font-size: 0.9rem;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">VASTR</div>
        <h1>Welcome to Vastr, """ + name + """! ✨</h1>
        <p>You've just joined Pakistan's most curated fashion platform with 9,000+ products from top brands.</p>

        <div class="features">
            <div class="feature-item">
                <span class="feature-icon">🛍️</span>
                <div>
                    <strong>Shop from 9,000+ Products</strong><br>
                    <small>Curated selection from Pakistan's best brands</small>
                </div>
            </div>
            <div class="feature-item">
                <span class="feature-icon">💝</span>
                <div>
                    <strong>Create Your Wishlist</strong><br>
                    <small>Save your favorite items in one place</small>
                </div>
            </div>
            <div class="feature-item">
                <span class="feature-icon">🔔</span>
                <div>
                    <strong>Get Early Access</strong><br>
                    <small>Be first to know about new arrivals and sales</small>
                </div>
            </div>
        </div>

        <p>Ready to explore?</p>
        <a href=\"""" + website_url + """\" class="button" style="color: white; text-decoration: none;">Get Started</a>

        <div class="footer">
            <p>If you didn't create this account, you can safely ignore this email.</p>
            <p><strong>— The Vastr Team</strong></p>
        </div>
    </div>
</body>
</html>
"""
    return html


def get_welcome_email_text(name: str, website_url: str) -> str:
    """Plain text version"""
    return f"""
Welcome to Vastr, {name}! ✨

You've just joined Pakistan's most curated fashion platform with 9,000+ products from top brands.

What's waiting for you:

🛍️ Shop from 9,000+ Products
   Curated selection from Pakistan's best brands

💝 Create Your Wishlist
   Save your favorite items in one place

🔔 Get Early Access
   Be first to know about new arrivals and sales

Ready to explore? Visit us at: {website_url}

If you didn't create this account, you can safely ignore this email.

— The Vastr Team
"""


def send_welcome_email_sync(email: str, name: str, website_url: str):
    """Send welcome email with clickable link"""
    try:
        print(f" Sending email to: {email}")
        print(f" Website URL: {website_url}")

        params = {
            "from": "Vastr <onboarding@resend.dev>",
            "to": [email],
            "subject": "Welcome to Vastr — Your Fashion Journey Starts Now ",
            "html": get_welcome_email_html(name, website_url),
            "text": get_welcome_email_text(name, website_url)
        }

        start_time = time.time()
        response = resend.Emails.send(params)
        duration = time.time() - start_time

        print(f" EMAIL SENT SUCCESSFULLY!")
        print(f"    ID: {response.get('id', 'unknown')}")
        print(f"     Time: {duration:.2f}s")
        print(f"    Button links to: {website_url}")
        return {"success": True, "email_id": response.get('id')}

    except Exception as e:
        print(f" EMAIL FAILED: {str(e)}")
        print(f"   📋 Error Type: {type(e).__name__}")
        return {"success": False, "error": str(e)}

@router.get("/debug/resend-status")
async def debug_status():
    """Debug endpoint - TEST THIS FIRST!"""
    return {
        "status": " Email Service Working!",
        "api_key_loaded": bool(resend.api_key),
        "endpoints": {
            "send_email": "/api/v1/auth/welcome-email",
            "debug": "/api/v1/debug/resend-status",
            "test_email": "/api/v1/debug/test-email"
        },
        "timestamp": time.time()
    }


@router.post("/auth/welcome-email")
async def send_welcome_email(request: WelcomeEmailRequest):
    """Send welcome email endpoint"""
    print(f"\n{'=' * 60}")
    print(f"  NEW EMAIL REQUEST")
    print(f"   To: {request.email}")
    print(f"   Name: {request.name}")
    print(f"    URL: {request.website_url}")
    print(f"{'=' * 60}")

    result = send_welcome_email_sync(
        email=request.email,
        name=request.name,
        website_url=request.website_url
    )

    if result["success"]:
        print(f"🎉 EMAIL SENT TO {request.email}")
        return {
            "message": "Welcome email sent successfully!",
            "sent": True,
            "email_id": result.get("email_id")
        }
    else:
        print(f" FAILED TO SEND EMAIL")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {result.get('error', 'Unknown error')}"
        )


@router.post("/debug/test-email")
async def test_email(email: str, name: str = "Test User"):
    """Test endpoint to send a sample email"""
    return await send_welcome_email(
        WelcomeEmailRequest(
            email=email,
            name=name,
            website_url="http://127.0.0.1:5500"
        )
    )


print(" Email Service Router Loaded Successfully!")
