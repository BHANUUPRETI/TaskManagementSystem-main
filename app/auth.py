import jwt
import datetime
from flask import current_app
from functools import wraps
from flask import request, jsonify


def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            bearer = request.headers['Authorization']
            token = bearer.split(" ")[1] if " " in bearer else bearer
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        user_id = decode_token(token)
        if not user_id:
            return jsonify({'error': 'Token is invalid or expired!'}), 401

        return f(user_id, *args, **kwargs)
    return decorated