from application.models.project_model import Project
from application.extensions import db

class ProjectService:
    @staticmethod
    def create_project(name, description, language, owner_id):
        new_project = Project(
            name=name,
            description=description,
            language=language,
            owner_id=owner_id
        )
        db.session.add(new_project)
        db.session.commit()
        return new_project

    @staticmethod
    def get_all_projects():
        return Project.query.all()

    @staticmethod
    def get_projects_by_language(language):
        return Project.query.filter_by(language=language).all()
