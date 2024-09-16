# TODO: Add authentification endpoints
from flask import Blueprint, jsonify, request, make_response
from werkzeug.security import check_password_hash, generate_password_hash
import uuid
from server.database import db


auth_blueprint = Blueprint(
    "auth",
    __name__,
)



def get_users_collection():
    return db.users

@auth_blueprint.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # check if email and pw are submitted
        # note: should always be true, since mail and password are mandatory to submit
        if not email or not password:
            return jsonify({'message': 'Email und Passwort erforderlich'}), 400

        # check whether user exists in db
        user = get_users_collection().find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            # generate the session_id, to verify the user
            session_token = str(uuid.uuid4())
            db.sessions.insert_one({'session_token': session_token, 'user_id': str(user['_id'])})

            # set sessioncookie for user
            # documentation on set_cookie: https://flask.palletsprojects.com/en/1.1.x/quickstart/
            response = make_response(jsonify({'redirect_url': 'http://localhost:5173/segmentation'}), 200)
            response.set_cookie('session_token', session_token)
            return response
        else:
            return jsonify({'message': 'Ungültige Anmeldeinformationen'}), 401

    except Exception as e:
        print(f"Fehler bei der Login-Anfrage: {e}")
        return jsonify({'message': 'Interner Serverfehler'}), 500


@auth_blueprint.route('/create_account', methods=['POST'])
def create_account():
    data = request.get_json()
    email = data.get('email')

    # Check if email already exists in the database
    existing_user = db.users.find_one({'email': email})
    if existing_user:
        return jsonify({'message': 'Die E-Mail-Adresse wird bereits verwendet'}), 400

    hashed_password = generate_password_hash(data['password'])
    user = {
        'firstName': data['firstName'],
        'lastName': data['lastName'],
        'email': email,
        'password': hashed_password
    }

    # insert user into db
    db.users.insert_one(user)

    # generate session cookie
    session_token = str(uuid.uuid4())
    db.sessions.insert_one({'session_token': session_token, 'user_id': str(user['_id'])})

    # set sessioncookie for user
    # documentation on set_cookie: https://flask.palletsprojects.com/en/1.1.x/quickstart/
    response = make_response(jsonify({'redirect_url': 'http://localhost:5173/info'}), 200)
    response.set_cookie('session_token', session_token)
    return response