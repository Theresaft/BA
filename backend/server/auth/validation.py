import re
from server.models import User, Whitelist

# Validation functions for user input.
# Each function returns a tuple (error message, status code) if validation fails
# or None if successful.

def validate_user_mail(user_mail):
    if not user_mail:
        return "E-Mail wird benötigt!", 400
    
    # check if user_mail follows general email format
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    
    if not re.match(email_regex, user_mail):
        return "Ungültiges E-Mail Format.", 400
    
    # check if user_mail is from UzL oder uksh.de
    if not user_mail.endswith('uni-luebeck.de') and not user_mail.endswith('uksh.de'):
        return "E-Mail muss von uni-luebeck.de oder uksh.de kommen.", 400
    
    # check if user_mail is already bound to an account
    if User.query.filter_by(user_mail=user_mail).first():
        return "Ein Account mit dieser E-Mail Adresse existiert bereits.", 400

    return None

def validate_whitelist(user_mail):
    # check if user_mail is whitelisted
    whitelisted_user = Whitelist.query.filter_by(user_mail=user_mail).first()
    
    if not whitelisted_user:
        return "E-Mail ist nicht freigeschaltet, kontaktieren Sie einen Administrator", 400
    
    return None

def validate_password(password):
    if not password:
        return "Ein Passwort wird benötigt!", 400
    if len(password) < 8:
        return "Das Passwort muss mindestens 8 Zeichen lang sein.", 400
    if not any(char.isdigit() for char in password):
        return "Das Passwort muss mindestens eine Ziffer beinhalten.", 400
    if not any(char.isupper() for char in password):
        return "Das Passwort muss mindestens einen Großbuchstaben beinhalten.", 400
    return None

def validate_login(user_mail, password):
    if not user_mail or not password:
        return "E-Mail und Passwort sind benötigt.", 400
