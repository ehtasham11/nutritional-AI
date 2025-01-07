from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select
import bcrypt
import uvicorn
from dotenv import load_dotenv
from smtplib import SMTP, SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi.middleware.cors import CORSMiddleware
import os
import secrets

# Load environment variables
load_dotenv()

from config.db import create_tables, engine
from models.signup import User, UserRegistration

# FastAPI application
app = FastAPI()

# Allow requests from the frontend (Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to hash passwords
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Function to validate the password
def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False

    has_uppercase = any(char.isupper() for char in password)
    has_digit = any(char.isdigit() for char in password)
    special_characters = set("!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~")
    has_special = any(char in special_characters for char in password)

    return has_uppercase and has_digit and has_special

# Function to send a confirmation email
def send_confirmation_email(email: str, first_name: str, token: str):
    try:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        subject = "Email Confirmation for Your Registration"
        body = f"""
        Hi {first_name},
        
        Thank you for registering on our platform. Please click the link below to confirm your email address:
        
        http://127.0.0.1:8055/confirm-email/{token}
        
        Best regards,
        The Team
        """

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

    except SMTPException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

# Function to check if the email is already registered
def is_email_registered(email: str, session: Session) -> bool:
    statement = select(User).where(User.email == email)
    result = session.exec(statement).first()
    return result is not None

@app.post("/register/")
async def register_user(user: UserRegistration, background_tasks: BackgroundTasks):
    with Session(engine) as session:
        if is_email_registered(user.email, session):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )

        if not validate_password(user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long, include an uppercase letter, a number, and a special character."
            )

        if user.password != user.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

        hashed_password = hash_password(user.password)
        confirmation_token = secrets.token_urlsafe(32)

        db_user = User(
            First_Name=user.First_Name,
            Last_Name=user.Last_Name,
            email=user.email,
            password=hashed_password,
            is_active=False,  # User will be inactive until email is confirmed
            confirmation_token=confirmation_token
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        background_tasks.add_task(send_confirmation_email, user.email, user.First_Name, confirmation_token)

    return {"message": "Registration successful! Please check your email to confirm your registration."}

@app.get("/confirm-email/{token}")
async def confirm_email(token: str):
    with Session(engine) as session:
        statement = select(User).where(User.confirmation_token == token)
        user = session.exec(statement).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired confirmation token"
            )

        user.is_active = True
        user.confirmation_token = None
        session.add(user)
        session.commit()

    return {"message": "Email confirmed successfully! You can now log in."}

# Start the FastAPI app
def start():
    create_tables()
    uvicorn.run("main:app", host="127.0.0.1", port=8055)

if __name__ == "__main__":
    start()
