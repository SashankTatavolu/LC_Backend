from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
from application.extensions import db
from application.models.feedback_model import Feedback
from application.models.notification_model import Notification
from application.models.segment_model import Segment
from application.models.chapter_model import Chapter
from application.models.project_model import Project

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
                Feedback.timestamp,
                Segment.segment_index,
                Segment.chapter_id,
                Chapter.name.label('chapter_name'),
                Chapter.project_id,
                Project.name.label('project_name'),
                Notification.message.label('notification_message'),  # Use 'message' from Notification
                Notification.is_read,
                Notification.created_at.label('notification_timestamp')
            )
            .join(Segment, Segment.segment_id == Feedback.segment_id)
            .join(Chapter, Chapter.id == Segment.chapter_id)
            .join(Project, Project.id == Chapter.project_id)
            .outerjoin(Notification, (Notification.segment_id == Feedback.segment_id) & (Notification.user_id != reviewer_id))
            .filter(Feedback.user_id == reviewer_id)
            .all()
        )

        feedback_list = []
        for feedback in feedback_query:
            feedback_list.append({
                "feedback_id": feedback.id,
                "segment_id": feedback.segment_id,
                "segment_index": feedback.segment_index,
                "chapter_id": feedback.chapter_id,
                "chapter_name": feedback.chapter_name,
                "project_id": feedback.project_id,
                "project_name": feedback.project_name,
                "has_error": feedback.has_error,
                "error_details": feedback.error_details,
                "timestamp": feedback.timestamp,
                "is_corrected": bool(feedback.error_details),  # If error_details is present, we can assume it was corrected
                "notification_message": feedback.notification_message,
                "is_notification_read": feedback.is_read,
                "notification_timestamp": feedback.notification_timestamp,
            })

        return jsonify(feedback_list), 200

    except Exception as e:
        print(f"Error in get_feedback_for_reviewer: {e}")
        return jsonify({"error": "Internal server error"}), 500
