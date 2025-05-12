from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mailbox import Message
import smtplib
import traceback
from flask import Blueprint, Config, current_app, request, jsonify
from flask_jwt_extended import create_access_token,jwt_required, get_jwt
from application.controllers.concept_controller import send_email
from ..services.user_service import UserService
from datetime import timedelta
from ..services.measure_time import measure_response_time
from ..extensions import mail
from application.extensions import db
from application.models.user_model import User



# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'tat.iiith2025@gmail.com'
SENDER_PASSWORD = 'noal fndb ucip aiui'  # Consider using environment variables for this

user_blueprint = Blueprint('users', __name__)

def send_email(subject, body, to, from_=None):
    try:
        # Set up the email server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Start TLS encryption
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Determine the "From" address
        sender_email = from_ if from_ else SENDER_EMAIL

        # Create the email with UTF-8 headers and body
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to
        msg['Subject'] = subject

        # Attach the body with UTF-8 encoding
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Send the email
        server.sendmail(sender_email, to, msg.as_string())
        server.quit()

        print(f"Email sent successfully from {sender_email} to {to}.")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        traceback.print_exc()
        return False

@user_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('username') or not data.get('role') or not data.get('password') or not data.get('organization') or not data.get('email'):
        return jsonify({"error": "username, role, password, email, and organization are required and cannot be empty"}), 400

    # Ensure role is stored as a list
    if not isinstance(data['role'], list):
        data['role'] = [role.strip() for role in data['role'].split(',')]

    user = UserService.create_user(data)
    if user:
        return jsonify({"message": "User created successfully"}), 201
    return jsonify({"error": "Failed to create user"}), 400


@user_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = UserService.authenticate_user(data['username'], data['password'])
    if user:
        # Ensure 'role' is a proper list
        roles = user.role if isinstance(user.role, list) else [user.role]
        
        # Clean up roles if needed (e.g., remove curly braces)
        roles = [role.replace("{", "").replace("}", "") for role in roles]
        
        additional_claims = {
            "username": user.username,
            "role": roles,  # Use the cleaned-up role list
            "user_id": user.id
        }
        access_token = create_access_token(
            identity=user.username, 
            additional_claims=additional_claims, 
            expires_delta=timedelta(hours=2)
        )
        return jsonify(access_token=access_token, role=roles), 200
    return jsonify({"error": "Invalid credentials"}), 401



@user_blueprint.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        username = data.get('username')  # Now accepts username instead of email

        if not username:
            return jsonify({"error": "Username is required"}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"message": "If that username exists, you will receive a reset link shortly"}), 200

        token = user.get_reset_token()
        if not token:
            return jsonify({"error": "Failed to generate reset token"}), 500

        reset_url = f"{request.host_url}reset-password?token={token}"
        subject = "Password Reset Request"
        body = f"Click to reset your password: {reset_url}\n\nIf you didn't request this, ignore it."
        
        if not send_email(subject, body, user.email):
            return jsonify({"error": "Failed to send email"}), 500

        return jsonify({"message": "If the username exists, you'll receive a reset link shortly"}), 200
    except Exception as e:
        print(f"[Forgot Password Error] {e}")
        return jsonify({"error": "Failed to process request"}), 500



@user_blueprint.route('/direct-reset-password', methods=['POST'])
def direct_reset_password():
    try:
        data = request.get_json()
        username = data.get('username')
        new_password = data.get('new_password')

        if not username or not new_password:
            return jsonify({"error": "Username and new password are required"}), 400

        # Find the user by username
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update the password directly
        user.set_password(new_password)
        db.session.commit()

        return jsonify({"message": "Password reset successfully"}), 200
    except Exception as e:
        print(f"[Direct Reset Password Error] {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to reset password"}), 500

@user_blueprint.route('/login/guest', methods=['POST'])
def login_guest():
    guest_claims = {"role": "guest"}
    access_token = create_access_token(identity="guest", additional_claims=guest_claims)
    return jsonify(access_token=access_token), 200

@user_blueprint.route('/all', methods=['GET'])
@jwt_required()
@measure_response_time
def get_all_users():
    users = UserService.get_all_users()
    users_data = []
    for user in users:
        # Ensure 'role' is a proper list
        roles = user.role if isinstance(user.role, list) else [user.role]
        
        # Clean up roles if needed (e.g., remove curly braces or unwanted characters)
        roles = [role.replace("{", "").replace("}", "") for role in roles]
        
        users_data.append({
            "id": user.id,
            "username": user.username,
            "role": roles,  # Return role as a JSON array
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "organization": user.organization,
            "email": user.email
        })
    return jsonify(users_data), 200


@user_blueprint.route('/by_organization/<organization>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_users_by_organization(organization):
    users = UserService.get_users_by_organization(organization)
    users_data = [{"id": user.id, "username": user.username, "role": user.role, "organization": user.organization, "created_at": user.created_at, "updated_at": user.updated_at} for user in users]
    return jsonify(users_data), 200

@user_blueprint.route('/by_role/<role>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_users_by_role(role):
    users = UserService.get_users_by_role(role)
    users_data = [{"id": user.id, "username": user.username, "role": user.role, "organization": user.organization, "created_at": user.created_at, "updated_at": user.updated_at} for user in users]
    return jsonify(users_data), 200



@user_blueprint.route('/details/<int:user_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_user_details(user_id):
    user = UserService.get_user_by_id(user_id)
    if user:
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": [user.role],  # Changed from "role" to "roles" as a list
            "organization": user.organization
        }

        if user.role in ['annotator', 'reviewer']:
            user_data["projects_assigned"] = user.total_assigned_projects()
        elif user.role == 'admin':
            user_data["projects_uploaded"] = user.total_uploaded_projects()
        
        return jsonify(user_data), 200
    return jsonify({"error": "User not found"}), 404


@user_blueprint.route('/contact', methods=['POST'])
def contact_us():
    data = request.get_json()
    name = data.get('name', 'Anonymous')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    if not email or not subject or not message:
        return jsonify({"error": "Email, subject, and message are required"}), 400

    try:
        # Use your custom send_email function
        subject = f"Contact Us - {subject}"
        body = f"From: {name}\nEmail: {email}\n\nMessage:\n{message}"
        
        # Send email to both your email and Somapaul's email
        to_emails = ['sashank.tatavolu@research.iiit.ac.in']
        
        # Call send_email function for each recipient
        for to_email in to_emails:
            send_email(subject, body, to_email, email)

        return jsonify({"message": "Your message has been sent successfully!"}), 200
    except Exception as e:
        print(f"[Contact Us Error] {e}")
        return jsonify({"error": "Failed to send message"}), 500

@user_blueprint.route('/update/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    claims = get_jwt()
    current_user_id = claims.get('user_id')
    current_user_roles = claims.get('role', [])

    # Ensure only the user or an admin can update the details
    if current_user_id != user_id and 'admin' not in current_user_roles:
        return jsonify({"error": "Permission denied"}), 403

    try:
        data = request.get_json()

        # Check for required fields
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Restrict certain fields if the user is not an admin
        if 'admin' not in current_user_roles:
            restricted_fields = ['role']
            for field in restricted_fields:
                if field in data:
                    return jsonify({"error": f"You are not allowed to update '{field}'"}), 403

        # Update user details
        updated_user = UserService.update_user(user_id, data)

        if updated_user:
            return jsonify({
                "message": "User updated successfully",
                "user": {
                    "id": updated_user.id,
                    "username": updated_user.username,
                    "email": updated_user.email,
                    "organization": updated_user.organization,
                    "role": updated_user.role
                }
            }), 200

        return jsonify({"error": "User not found"}), 404

    except Exception as e:
        print(f"[Update User Error] {e}")
        return jsonify({"error": "An error occurred while updating user details"}), 500
