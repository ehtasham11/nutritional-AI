from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select
import bcrypt
import uvicorn
from dotenv import load_dotenv
from smtplib import SMTP, SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import secrets
load_dotenv()

from config.db import create_tables, engine
from models.signup import User, UserRegistration

# FastAPI application
app = FastAPI()

# Function to hash passwords
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Function to validate the password
def validate_password(password: str) -> bool:
    # Minimum length requirement
    if len(password) < 8:
        return False

    # Flags to check for required character types
    has_uppercase = False
    has_digit = False
    has_special = False

    # List of special characters
    special_characters = set("!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~")

    for char in password:
        if char.isupper():
            has_uppercase = True
        elif char.isdigit():
            has_digit = True
        elif char in special_characters:
            has_special = True

        # If all conditions are met, no need to continue checking
        if has_uppercase and has_digit and has_special:
            return True

    return False

# Function to send a confirmation email
def send_confirmation_email(email: str, First_name: str, token: str):
    try:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        # Create email content
        subject = "Email Confirmation for Your Registration"
        body = f"""
        Hi {First_name},
        
        Thank you for registering on our platform. Please click the link below to confirm your email address:
        
        http://127.0.0.1:8070/confirm-email/{token}
        
        Best regards,
        The Team
        """

        # Create email message
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send the email
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
        # Check if the email is already registered
        if is_email_registered(user.email, session):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )

        # Validate password strength
        if not validate_password(user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long, include an uppercase letter, a number, and a special character."
            )

        # Check if password and confirm_password match
        if user.password != user.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

        # Hash the password
        hashed_password = hash_password(user.password)

        # Generate confirmation token
        confirmation_token = secrets.token_urlsafe(32)

        # Create a new user record (set active=False until email confirmation)
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

        # Send confirmation email in the background
        background_tasks.add_task(send_confirmation_email, user.email, user.First_Name, user.Last_Name, confirmation_token)

    return {"message": "Registration successful! Please check your email to confirm your registration."}

@app.get("/confirm-email/{token}")
async def confirm_email(token: str):
    with Session(engine) as session:
        # Find the user by confirmation token
        statement = select(User).where(User.confirmation_token == token)
        user = session.exec(statement).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired confirmation token"
            )

        # Activate the user and clear the confirmation token
        user.is_active = True
        user.confirmation_token = None
        session.add(user)
        session.commit()

    return {"message": "Email confirmed successfully! You can now log in."}

# Start the FastAPI app
def start():
    create_tables()
    uvicorn.run("logout.main:app", host="127.0.0.1", port=8070)

