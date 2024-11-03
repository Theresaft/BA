import os
from flask import Blueprint, jsonify, request, make_response
from werkzeug.security import check_password_hash, generate_password_hash
import uuid
from server.database import db
from server.models import User, Session
from server.auth.validation import validate_user_mail, validate_whitelist, validate_password, validate_login

# note: setting cookies requires https; for development ngrok can be used

auth_blueprint = Blueprint(
    "auth",
    __name__,
)


@auth_blueprint.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user_mail = data.get('user_mail', '').strip()
    password = data.get('password', '').strip()

    # Validation
    user_mail_error = validate_user_mail(user_mail)
    if user_mail_error:
        return jsonify({'message': user_mail_error[0]}), user_mail_error[1]

    whitelist_error = validate_whitelist(user_mail)
    if whitelist_error:
        return jsonify({'message': whitelist_error[0]}), whitelist_error[1]

    password_error = validate_password(password)
    if password_error:
        return jsonify({'message': password_error[0]}), password_error[1]


    # Hash password and save the user_password
    whitelisted_user = User(user_mail=user_mail, password_hash=generate_password_hash(password))

    session_token = str(uuid.uuid4())

    try:
        db.session.add(whitelisted_user)
        db.session.flush()  # Use flush to get user_id

        # Create new directory for user uploads
        user_id = whitelisted_user.user_id
        user_directory = os.path.join('/usr/src/image-repository', str(user_id)) 
        os.makedirs(user_directory, exist_ok=False) 

        # save session in db
        new_session = Session(session_token=session_token, user_id=whitelisted_user.user_id)
        db.session.add(new_session)
        db.session.flush()

        # add change to db
        db.session.commit()

        # set session cookie for user
        response = make_response(jsonify({'message': f'User {user_mail} created successfully!'}), 201)
        response.set_cookie(
            'session_token', 
            session_token, 
            httponly=False, # allows javaskript to access cookie
            samesite='None', # cookies allowed for cross-site
            secure=True # https-only (mandatory for cross-site cookies)
        )
        print("Setze Cookie: session_token =", session_token)
        return response

        return response


    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while creating the user: {str(e)}'}), 500
    

@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    #print("data: ", data)
    user_mail = data.get('user_mail', '').strip()
    password = data.get('password', '').strip()

    # are user_mail and password provided?
    login_error = validate_login(user_mail, password)
    if login_error:
        return jsonify({'message': login_error[0]}), login_error[1]

    # query the user by user_mail
    user = User.query.filter_by(user_mail=user_mail).first()

    if user and check_password_hash(user.password_hash, password):
        # generate session token
        session_token = str(uuid.uuid4())

        # TODO: only safe latest session
        new_session = Session(session_token=session_token, user_id=user.user_id)
        db.session.add(new_session)
        db.session.commit()

        response = make_response(jsonify({'message': 'Login successful'}), 200)
        response.set_cookie(
            'session_token', 
            session_token, 
            httponly=False, # allows javaskript to access cookie
            samesite='None', # cookies allowed for cross-site
            secure=True # https-only (mandatory for cross-site cookies)
        )
        print("Setze Cookie: session_token =", session_token)
        return response
    else:
        return jsonify({'message': 'Invalid credentials'}), 401
        