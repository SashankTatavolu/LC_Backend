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

    required_fields = ['username', 'role', 'password', 'organization', 'email', 'language']
    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": "username, role, password, email, organization, and language are required and cannot be empty"}), 400

    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "username", "message": "Username already exists. Please choose a different one."}), 400

    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "email", "message": "Email already exists. Please use a different email address."}), 400

    if not isinstance(data['role'], list):
        data['role'] = [role.strip() for role in data['role'].split(',')]

    if not isinstance(data['language'], list):
        data['language'] = [lang.strip() for lang in data['language'].split(',')]

    # Create user but mark as not approved
    data['is_approved'] = False
    user = UserService.create_user(data)

    if user:
        # Notify organization admin(s)
        admins = User.query.filter_by(organization=user.organization).all()

        for admin in admins:
            if isinstance(admin.role, list) and any(role.lower() == 'admin' for role in admin.role):
                subject = f"Approval Needed for New User: {user.username}"
                approval_link = f"{request.host_url}approve-user/{user.id}"
                body = f"""
        Hello {admin.username},

        A new user '{user.username}' has registered under your organization '{user.organization}'.

        Please log in to the platform to review and approve the request from pending user requests dashboard
        
        
        Thanks,
        Language Corpus Platform
        """
                print(f"Sending approval email to: {admin.email}")
                send_email(subject, body, admin.email)
        return jsonify({"message": "User created successfully. Awaiting admin approval."}), 201

    return jsonify({"error": "Failed to create user"}), 400


@user_blueprint.route('/approve-user/<int:user_id>', methods=['GET'])
@jwt_required(optional=True)
def approve_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.is_approved = True
    db.session.commit()

    # Notify user with a more detailed email
    subject = "Your Account Has Been Approved"
    body = f"""Hello {user.username},

Your account registration has been approved by the administrator. 

You can now log in to the platform using your credentials:
- Username: {user.username}
- Organization: {user.organization}

We look forward to seeing you on the platform!

Best regards,
The Platform Team
"""
    
    # Send the email
    if not send_email(subject, body, user.email):
        print(f"Failed to send approval email to {user.email}")
        return jsonify({"warning": "User approved but email failed to send"}), 200

    return jsonify({
        "message": f"User {user.username} approved successfully.",
        "email_sent": True
    }), 200


@user_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = UserService.authenticate_user(data['username'], data['password'])
    
    if user:
        if not user.is_approved:
            return jsonify({"error": "Your account is awaiting admin approval"}), 403

        # Ensure 'role' is a proper list
        roles = user.role if isinstance(user.role, list) else [user.role]
        roles = [role.replace("{", "").replace("}", "") for role in roles]
        
        # Ensure 'language' is a proper list
        languages = user.language if isinstance(user.language, list) else [user.language]
        
        additional_claims = {
            "username": user.username,
            "role": roles,
            "user_id": user.id,
            "language": languages,
            "organization": user.organization  # Include organization in JWT claims
        }

        access_token = create_access_token(
            identity=user.username, 
            additional_claims=additional_claims, 
            expires_delta=timedelta(hours=2)
        )

        return jsonify({
            "access_token": access_token,
            "role": roles,
            "languages": languages,
            "organization": user.organization  # Include organization in response
        }), 200
    
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
    users_data = [{
        "id": user.id, 
        "username": user.username, 
        "role": user.role, 
        "organization": user.organization, 
        "is_approved": user.is_approved,
        "language": user.language,  # Add language to response
        "created_at": user.created_at, 
        "updated_at": user.updated_at
    } for user in users]
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
            "roles": user.role,  # Already a list
            "organization": user.organization,
            "languages": user.language  # Already a list
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


@user_blueprint.route('/delete/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        claims = get_jwt()
        current_user_roles = claims.get('role', [])

        # Fix role check
        if not any(role.lower() == 'admin' for role in current_user_roles):
            return jsonify({"error": "Permission denied. Only admins can delete users."}), 403

        user_to_delete = User.query.get(user_id)
        if not user_to_delete:
            return jsonify({"error": "User not found"}), 404

        current_user_id = claims.get('user_id')
        if user_id == current_user_id:
            return jsonify({"error": "Cannot delete your own account"}), 400

        db.session.delete(user_to_delete)
        db.session.commit()

        return jsonify({"message": f"User {user_to_delete.username} deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[Delete User Error] {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to delete user"}), 500
