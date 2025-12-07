# backend/router/auth.py

from fastapi import APIRouter, BackgroundTasks, status
from pydantic import EmailStr, BaseModel
import sys
import os

# Add parent directory to path to import email_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from email_service import send_welcome_email

router = APIRouter(prefix="/auth", tags=["authentication"])


class UserSignup(BaseModel):
    email: EmailStr
    name: str
    provider: str


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_user(
        user_data: UserSignup,
        background_tasks: BackgroundTasks
):
    """
    Handle user signup and send welcome email
    """
    try:
        # Send welcome email in background
        await send_welcome_email(
            email=user_data.email,
            name=user_data.name,
            background_tasks=background_tasks
        )

        return {
            "status": "success",
            "message": "Account created successfully",
            "email": user_data.email,
            "email_queued": True
        }

    except Exception as e:
        print(f"Email error (non-fatal): {e}")
        return {
            "status": "success",
            "message": "Account created successfully",
            "email": user_data.email,
            "email_queued": False
        }


@router.post("/resend-welcome")
async def resend_welcome_email(
        email: EmailStr,
        name: str,
        background_tasks: BackgroundTasks
):
    """Resend welcome email"""
    await send_welcome_email(email, name, background_tasks)
    return {"status": "success"}