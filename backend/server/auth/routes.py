# TODO: Add authentification endpoints
import os
from flask import Blueprint, jsonify, request, make_response
from werkzeug.security import check_password_hash, generate_password_hash
import uuid
from server.database import db
from server.models import User, Session
from server.auth.validation import validate_username, validate_password, validate_login

# readme datenbankclient

auth_blueprint = Blueprint(
    "auth",
    __name__,
)


@auth_blueprint.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    # Validation
    username_error = validate_username(username)
    if username_error:
        return jsonify({'message': username_error[0]}), username_error[1]

    password_error = validate_password(password)
    if password_error:
        return jsonify({'message': password_error[0]}), password_error[1]

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists!'}), 400

    # Hash password and create the user
    password_hash = generate_password_hash(password)
    new_user = User(username=username, password_hash=password_hash)

    # TODO: Generate Session-Cookie for new user
    session_token = str(uuid.uuid4())


    try:
        db.session.add(new_user)
        db.session.flush()  # Use flush to get user_id

        # Create new directory for user uploads
        user_id = new_user.user_id
        user_directory = os.path.join('/usr/src/image-repository', str(user_id)) 
        os.makedirs(user_directory, exist_ok=False) 

        # save session in db
        new_session = Session(session_token=session_token, user_id=user_id)
        db.session.add(new_session)
        db.session.flush()

        # add change to db
        db.session.commit()

        # set session cookie for user
        response = make_response(jsonify({'message': f'User {username} created successfully!'}), 201)
        response.set_cookie('session_token', session_token, httponly=True, samesite='Strict')

        return response


    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while creating the user: {str(e)}'}), 500
    

@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    # are username and password provided?
    login_error = validate_login(username, password)
    if login_error:
        return jsonify({'message': login_error[0]}), login_error[1]

    # query the user by username
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        # generate session token
        session_token = str(uuid.uuid4())

        # TODO: only safe latest session
        new_session = Session(session_token=session_token, user_id=user.user_id)
        db.session.add(new_session)
        db.session.commit()

        response = make_response(jsonify({'message': 'Login successful'}), 200)
        response.set_cookie('session_token', session_token, httponly=True, samesite='Strict')

        return response
    else:
        return jsonify({'message': 'Invalid credentials'}), 401
        

# def get_users_collection():
#     return db.users

# @auth_blueprint.route('/login', methods=['POST'])
# def login():
#     try:
#         data = request.get_json()
#         email = data.get('email')
#         password = data.get('password')

#         # check if email and pw are submitted
#         # note: should always be true, since mail and password are mandatory to submit
#         if not email or not password:
#             return jsonify({'message': 'Email und Passwort erforderlich'}), 400

#         # check whether user exists in db
#         user = get_users_collection().find_one({'email': email})

#         if user and check_password_hash(user['password'], password):
#             # generate the session_id, to verify the user
#             session_token = str(uuid.uuid4())
#             db.sessions.insert_one({'session_token': session_token, 'user_id': str(user['_id'])})

#             # set sessioncookie for user
#             # documentation on set_cookie: https://flask.palletsprojects.com/en/1.1.x/quickstart/
#             response = make_response(jsonify({'redirect_url': 'http://localhost:5173/segmentation'}), 200)
#             response.set_cookie('session_token', session_token)
#             return response
#         else:
#             return jsonify({'message': 'Ungültig  e Anmeldeinformationen'}), 401

#     except Exception as e:
#         print(f"Fehler bei der Login-Anfrage: {e}")
#         return jsonify({'message': 'Interner Serverfehler'}), 500


# @auth_blueprint.route('/create_account', methods=['POST'])
# def create_account():
#     data = request.get_json()
#     email = data.get('email')

#     # Check if email already exists in the database
#     existing_user = db.users.find_one({'email': email})
#     if existing_user:
#         return jsonify({'message': 'Die E-Mail-Adresse wird bereits verwendet'}), 400

#     hashed_password = generate_password_hash(data['password'])
#     user = {
#         'firstName': data['firstName'],
#         'lastName': data['lastName'],
#         'email': email,
#         'password': hashed_password
#     }

#     # insert user into db
#     db.users.insert_one(user)

#     # generate session cookie
#     session_token = str(uuid.uuid4())
#     db.sessions.insert_one({'session_token': session_token, 'user_id': str(user['_id'])})

#     # set sessioncookie for user
#     # documentation on set_cookie: https://flask.palletsprojects.com/en/1.1.x/quickstart/
#     response = make_response(jsonify({'redirect_url': 'http://localhost:5173/info'}), 200)
#     response.set_cookie('session_token', session_token)
#     return response