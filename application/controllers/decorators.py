from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify
from application.models.user_model import User

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if user and user.role == 'Admin':
            return fn(*args, **kwargs)
        else:
            return jsonify({"msg": "Admin access required"}), 403
    return wrapper
