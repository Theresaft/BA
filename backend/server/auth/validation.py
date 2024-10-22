import re
from server.models import User

# Validation functions for user input.
# Each function returns a tuple (error message, status code) if validation fails
# or None if successful.

def validate_user_mail(user_mail):
    if not user_mail:
        return "Email is required!", 400
    
    # check if user_mail follows general email format
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    
    if not re.match(email_regex, user_mail):
        return "Invalid email format", 400
    
    # check if user_mail is from UzL
    if not user_mail.endswith('uni-luebeck.de'):
        return "Email must be from uni-luebeck.de", 400

    return None

def validate_whitelist(user_mail):
    # check for user_mail in database
    existing_user = User.query.filter_by(user_mail=user_mail).first()
    
    if not existing_user:
        return "Email not whitelisted, contact Jan to get access", 400
    
    # if a password is set for user, email is in use already
    if existing_user.password_hash:
        return "Email is already in use", 400
    
    return None

def validate_password(password):
    if not password:
        return "Password is required!", 400
    if len(password) < 8:
        return "Password must be at least 8 characters long.", 400
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one digit.", 400
    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter.", 400
    return None

def validate_login(user_mail, password):
    if not user_mail or not password:
        return "Email and password are required", 400
