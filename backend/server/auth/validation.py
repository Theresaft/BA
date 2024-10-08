# Validation functions for user input.
# Each function returns a tuple (error message, status code) if validation fails
# or None if successful.

def validate_username(username):
    if not username:
        return "Username is required!", 400
    if len(username) < 3 or len(username) > 255:
        return "Username must be between 3 and 255 characters!", 400
    if not username.isalnum():
        return "Username must contain only alphanumeric characters!", 400
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

def validate_login(username, password):
    if not username or not password:
        return "Username and password are required", 400
