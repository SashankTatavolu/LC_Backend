from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
from application.extensions import db
from application.models.feedback_model import Feedback
from application.models.notification_model import Notification
from application.models.segment_model import Segment
from application.models.chapter_model import Chapter
from application.models.project_model import Project
from application.models.assignment_model import Assignment
from application.models.user_model import User

reviewer_blueprint = Blueprint('reviewer', __name__)

@reviewer_blueprint.route('/feedback', methods=['GET'])
@jwt_required()
def get_feedback_for_reviewer():
    try:
        # Get the reviewer user ID
        claims = get_jwt()
        reviewer_id = claims.get("user_id")

        # Fetch feedback given by the reviewer
        feedback_query = (
            db.session.query(
                Feedback.id,
                Feedback.segment_id,
                Feedback.has_error,
                Feedback.error_details,
                Feedback.tab_name,
                Feedback.timestamp,
                Segment.segment_index,
                Segment.chapter_id,
                Chapter.name.label('chapter_name'),
                Chapter.project_id,
                Project.name.label('project_name'),
                # Notifications related to this feedback (both assigned user and feedback giver notifications)
                Notification.message.label('notification_message'),
                Notification.is_read,
                Notification.created_at.label('notification_timestamp'),
                Notification.user_id.label('notification_recipient_id'),
                # Get assignment info to see who was assigned
                Assignment.user_id.label('assigned_user_id'),
                User.username.label('assigned_user_name')
            )
            .join(Segment, Segment.segment_id == Feedback.segment_id)
            .join(Chapter, Chapter.id == Segment.chapter_id)
            .join(Project, Project.id == Chapter.project_id)
            .outerjoin(Notification, Notification.segment_id == Feedback.segment_id)
            .outerjoin(Assignment, Assignment.segment_id == Feedback.segment_id)
            .outerjoin(User, User.id == Assignment.user_id)
            .filter(Feedback.user_id == reviewer_id)
            .order_by(Feedback.timestamp.desc())
            .all()
        )

        feedback_list = []
        processed_segments = set()
        
        for feedback in feedback_query:
            if feedback.segment_id in processed_segments:
                continue  # Skip duplicates
                
            processed_segments.add(feedback.segment_id)
            
            # Get all notifications related to this feedback
            notifications = Notification.query.filter_by(segment_id=feedback.segment_id).all()
            
            notification_details = []
            for notif in notifications:
                notification_details.append({
                    "message": notif.message,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at,
                    "recipient_id": notif.user_id,
                    "sender_id": notif.sender_id
                })
            
            feedback_list.append({
                "feedback_id": feedback.id,
                "segment_id": feedback.segment_id,
                "segment_index": feedback.segment_index,
                "chapter_id": feedback.chapter_id,
                "chapter_name": feedback.chapter_name,
                "project_id": feedback.project_id,
                "project_name": feedback.project_name,
                "tab_name": feedback.tab_name,
                "has_error": feedback.has_error,
                "error_details": feedback.error_details,
                "timestamp": feedback.timestamp,
                "assigned_to": {
                    "user_id": feedback.assigned_user_id,
                    "username": feedback.assigned_user_name
                },
                "notifications": notification_details,
                "status": "completed" if any(n.is_read for n in notifications) else "pending"
            })

        return jsonify(feedback_list), 200

    except Exception as e:
        print(f"Error in get_feedback_for_reviewer: {e}")
        return jsonify({"error": "Internal server error"}), 500

@reviewer_blueprint.route('/feedback/<int:feedback_id>', methods=['DELETE'])
@jwt_required()
def delete_feedback(feedback_id):
    try:
        claims = get_jwt()
        current_user_id = claims.get("user_id")  # Correct way if using additional_claims

        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            return jsonify({"error": "Feedback not found"}), 404

        if feedback.user_id != current_user_id:
            return jsonify({"error": "You are not authorized to delete this feedback"}), 403

        db.session.delete(feedback)
        db.session.commit()

        return jsonify({"message": "Feedback deleted successfully"}), 200

    except Exception as e:
        print(f"Error deleting feedback: {e}")
        return jsonify({"error": "Internal server error"}), 500