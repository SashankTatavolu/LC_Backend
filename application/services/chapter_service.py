from application.models.chapter_model import Chapter
from application.extensions import db

class ChapterService:
    @staticmethod
    def create_chapter(project_id, name, uploaded_by_id, text):
        chapter = Chapter(
            project_id=project_id,
            name=name,
            uploaded_by_id=uploaded_by_id,
            text=text
        )
        db.session.add(chapter)
        db.session.commit()
        return chapter

    @staticmethod
    def get_chapters_by_project(project_id):
        return Chapter.query.filter_by(project_id=project_id).all()
