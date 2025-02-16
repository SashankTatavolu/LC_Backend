from functools import wraps
from flask_jwt_extended import get_jwt, verify_jwt_in_request, get_jwt_identity
from flask import jsonify
from application.models.user_model import User

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if 'admin' in claims.get('role', []):  # Assuming 'role' is a list in claims
            return fn(*args, **kwargs)
        else:
            return jsonify({"msg": "Admin access required"}), 403
    return wrapper


