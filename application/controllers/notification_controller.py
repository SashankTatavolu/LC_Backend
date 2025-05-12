from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
from application.models.notification_model import Notification
from ..extensions import db
from application.models.feedback_model import Feedback
from application.models.user_model import User
from application.controllers.concept_controller import send_email
from application.models.project_model import Project
from application.models.segment_model import Segment
from application.models.chapter_model import Chapter

notification_blueprint = Blueprint('notifications', __name__)

@notification_blueprint.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        # Fetch user_id from claims
        claims = get_jwt()
        user_id = claims.get("user_id")

        # Ensure user_id is an integer
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user_id format'}), 400

        # Fetch detailed notifications with related segment, chapter, project info, and error details
        notifications = (
            db.session.query(
                Notification.id,
                Notification.user_id,
                Notification.segment_id,
                Notification.message,
                Notification.is_read,
                Notification.created_at,
                Segment.segment_index,
                Segment.chapter_id,
                Chapter.name.label('chapter_name'),
                Chapter.project_id,
                Project.name.label('project_name'),
                Feedback.has_error,
                Feedback.error_details
            )
            .join(Segment, Segment.segment_id == Notification.segment_id)
            .join(Chapter, Chapter.id == Segment.chapter_id)
            .join(Project, Project.id == Chapter.project_id)
            .outerjoin(Feedback, Feedback.segment_id == Segment.segment_id)  # Use outer join to handle cases with no feedback
            .filter(Notification.user_id == user_id)
            .all()
        )

        # Serialize the response
        notification_list = []
        for notif in notifications:
            notification_list.append({
                "id": notif.id,
                "user_id": notif.user_id,
                "segment_id": notif.segment_id,
                "segment_index": notif.segment_index,
                "chapter_id": notif.chapter_id,
                "chapter_name": notif.chapter_name,
                "project_id": notif.project_id,
                "project_name": notif.project_name,
                "message": notif.message,
                "is_read": notif.is_read,
                "created_at": notif.created_at,
                "has_error": notif.has_error if notif.has_error is not None else False,
                "error_details": notif.error_details if notif.error_details else ""
            })

        return jsonify(notification_list), 200

    except Exception as e:
        print(f"Error in get_notifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500



@notification_blueprint.route('/notifications/read/<int:notification_id>', methods=['PUT'])
@jwt_required()
def mark_notification_as_read(notification_id):
    data = request.get_json()
    comment = data.get('comment', None)

    user_id = get_jwt()["user_id"]

    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    # Mark as read
    notification.is_read = True

    segment_id = notification.segment_id

    # Fetch additional context information
    segment = Segment.query.get(segment_id)
    chapter_name = ""
    project_name = ""
    chapter_id = None

    if segment:
        chapter_id = segment.chapter_id
        chapter = Chapter.query.get(chapter_id)
        if chapter:
            chapter_name = chapter.name
            project = Project.query.get(chapter.project_id)
            if project:
                project_name = project.name

    # Find the reviewer who gave the original feedback
    feedback = Feedback.query.filter_by(segment_id=segment_id).order_by(Feedback.id.desc()).first()

    if feedback:
        reviewer = User.query.get(feedback.user_id)

        if reviewer:
            # Construct the notification message
            reviewer_message = (
                f"The assigned user has reviewed your feedback for Segment {segment.segment_index} "
                f"in Chapter '{chapter_name}' (ID: {chapter_id}) of Project '{project_name}' and left a comment."
            )

            # Check if a similar notification already exists for the reviewer
            existing_notification = (
                Notification.query.filter_by(
                    user_id=reviewer.id,
                    segment_id=segment_id,
                    sender_id=user_id,
                    message=reviewer_message
                ).first()
            )

            # Only send a new notification if a similar one does not already exist
            if not existing_notification:
                # Save notification for the reviewer
                reviewer_notification = Notification(
                    user_id=reviewer.id,
                    sender_id=user_id,
                    segment_id=segment_id,
                    message=reviewer_message
                )
                db.session.add(reviewer_notification)

                # Optional: Send email to the reviewer
                subject = f"Feedback Review for Segment {segment.segment_index}"
                body = (
                    f"Hello {reviewer.username},\n\n"
                    f"The assigned user has reviewed your feedback for Segment {segment.segment_index} in "
                    f"Chapter '{chapter_name}' (ID: {chapter_id}) of Project '{project_name}'.\n\n"
                    f"Comment: {comment}\n\n"
                    "Please check the application for further details.\n\n"
                    "Regards,\nReview Team"
                )
                send_email(subject, body, reviewer.email)

    # Commit the changes
    db.session.commit()

    return jsonify({
        'message': 'Notification marked as read and reviewer notified if applicable',
        'notification': {
            'id': notification.id,
            'segment_id': segment_id,
            'segment_index': segment.segment_index if segment else None,
            'chapter_id': chapter_id,
            'chapter_name': chapter_name,
            'project_name': project_name,
            'comment': comment,
            'is_read': notification.is_read
        }
    }), 200




@notification_blueprint.route('/notifications/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    try:
        user_id = get_jwt()['user_id']
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404

        db.session.delete(notification)
        db.session.commit()
        return jsonify({'message': 'Notification deleted successfully'}), 200
    except Exception as e:
        print(f"Error in delete_notification: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@notification_blueprint.route('/notifications', methods=['DELETE'])
@jwt_required()
def delete_all_notifications():
    try:
        user_id = get_jwt()['user_id']
        notifications = Notification.query.filter_by(user_id=user_id).all()

        if not notifications:
            return jsonify({'message': 'No notifications to delete'}), 200

        for notification in notifications:
            db.session.delete(notification)

        db.session.commit()
        return jsonify({'message': 'All notifications deleted successfully'}), 200
    except Exception as e:
        print(f"Error in delete_all_notifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500
