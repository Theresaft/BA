import os
from flask import Blueprint, jsonify, request, make_response
from werkzeug.security import check_password_hash, generate_password_hash
import uuid
import json
from server.database import db
from server.models import User, Session, UserSettings
from server.auth.validation import validate_user_mail, validate_whitelist, validate_password, validate_login

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

        # save session in db
        new_session = Session(session_token=session_token, user_id=whitelisted_user.user_id)
        db.session.add(new_session)
        db.session.flush()

        # Add settings entry for user
        settings_for_user = UserSettings(user_id=whitelisted_user.user_id, confirm_delete_entry=True, number_displayed_recent_segmentations=1000000)
        db.session.add(settings_for_user)
        db.session.flush()

        # add change to db
        db.session.commit()

        # set session cookie for user
        response = make_response(jsonify({'message': f'User {user_mail} created successfully!', 'session_token': session_token}), 201)
        return response


    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while creating the user: {str(e)}'}), 500
    

@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
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

        response = make_response(jsonify({'message': 'Login erfolgreich', 'session_token': session_token}), 200)
        return response
    else:
        return jsonify({'message': 'Ungültige Anmeldedaten'}), 401
        

@auth_blueprint.route('/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Missing or invalid Authorization header'}), 401

    # extract session_token
    session_token = auth_header.replace('Bearer ', '').strip()

    # find corresponding session
    session = Session.query.filter_by(session_token=session_token).first()

    # check for valid session_token
    if not session:
            return jsonify({'message': 'Invalid session_token'}), 401

    try:
        # delete session
        db.session.delete(session)
        db.session.commit()

        # successful logout (client-side removal of token)
        return jsonify({'message': 'Logout of session ' + session_token + 'successful'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error with logout: {str(e)}'}), 500
    
     
# This function receives a session_token and returns the userID bound to that session_token
@auth_blueprint.route('/userID', methods=['POST'])
def getUserID():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Missing or invalid Authorization header'}), 401

    # extract session_token
    session_token = auth_header.replace('Bearer ', '').strip()

    # validate session token
    session = Session.query.filter_by(session_token=session_token).first()
    if session is None:
        return jsonify({'message': 'Invalid session token'}), 401

    # successfull validation
    return jsonify({'message': 'Valid session token', 'user_id': session.user_id}), 200