from application.extensions import db
from application.models.revision_history_model import RevisionHistory

class RevisionHistoryService:
    @staticmethod
    def log_revision(project_id, chapter_id, segment_id, user_id, change_type, old_data=None, new_data=None):
        revision = RevisionHistory(
            project_id=project_id,
            chapter_id=chapter_id,
            segment_id=segment_id,
            user_id=user_id,
            change_type=change_type,
            old_data=old_data,
            new_data=new_data
        )
        db.session.add(revision)
        db.session.commit()

    @staticmethod
    def get_revisions_by_segment(segment_id):
        return RevisionHistory.query.filter_by(segment_id=segment_id).order_by(RevisionHistory.timestamp.desc()).all()
