# from application.models.project_model import Project
# from application.models.user_model import User
# from application.extensions import db
# from application.models.chapter_model import Chapter
# from application.models.project_model import project_user

# class ProjectService:
#     @staticmethod
#     def create_project(name, description, language, owner_id):
#         new_project = Project(
#             name=name,
#             description=description,
#             language=language,
#             owner_id=owner_id
#         )
#         db.session.add(new_project)
#         db.session.commit()
#         return new_project

#     @staticmethod
#     def get_all_projects():
#         return Project.query.all()

#     @staticmethod
#     def get_projects_by_language(language):
#         return Project.query.filter_by(language=language).all()
    
#     # @staticmethod
#     # def assign_user_to_project(project_id, user_id, chapter_id):
#     #     project = Project.query.get(project_id)
#     #     user = User.query.get(user_id)
#     #     chapter = Chapter.query.get(chapter_id)
#     #     if project and user and chapter and chapter.project_id == project.id:
#     #         db.session.execute(project_user.insert().values(
#     #             user_id=user.id,
#     #             project_id=project.id,
#     #             chapter_id=chapter.id
#     #         ))
#     #         db.session.commit()
#     #         return True
#     #     return False

#     @staticmethod
#     def assign_users_to_project(project_id, user_ids, chapter_id):
#         project = Project.query.get(project_id)
#         chapter = Chapter.query.get(chapter_id)
#         if not project or not chapter or chapter.project_id != project_id:
#             return False
#         users = User.query.filter(User.id.in_(user_ids)).all()
#         if len(users) != len(user_ids):
#             return False
#         try:
#             for user in users:
#                 db.session.execute(project_user.insert().values(
#                     user_id=user.id,
#                     project_id=project.id,
#                     chapter_id=chapter.id
#                 ))
#             db.session.commit()
#             return True
#         except Exception as e:
#             db.session.rollback()
#             print(f"Failed to assign users: {str(e)}")
#             return False

#     @staticmethod
#     def get_projects_by_user(user_id):
#         user = User.query.get(user_id)
#         if user:
#             return user.projects.all()
#         return []
    
#     @staticmethod
#     def get_projects_by_user_organization(organization):
#         return Project.query.join(User).filter(User.organization == organization).all()




from sqlalchemy.exc import SQLAlchemyError, OperationalError
from contextlib import contextmanager
from typing import List, Optional
import logging
from application.models.project_model import Project, project_user
from application.models.user_model import User
from application.extensions import db
from application.models.chapter_model import Chapter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectService:
    MAX_RETRIES = 3
    
    @contextmanager
    def session_scope():
        """Provide a transactional scope around a series of operations."""
        try:
            yield db.session
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error occurred: {str(e)}")
            raise
        finally:
            db.session.close()

    @staticmethod
    def _retry_operation(operation, *args, **kwargs):
        """Retry an operation with exponential backoff."""
        from time import sleep
        for attempt in range(ProjectService.MAX_RETRIES):
            try:
                return operation(*args, **kwargs)
            except OperationalError as e:
                if attempt == ProjectService.MAX_RETRIES - 1:
                    logger.error(f"Final retry attempt failed: {str(e)}")
                    raise
                sleep(2 ** attempt)  # Exponential backoff
                continue
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

    @staticmethod
    def create_project(name: str, description: str, language: str, owner_id: int) -> Optional[Project]:
        try:
            with ProjectService.session_scope():
                new_project = Project(
                    name=name,
                    description=description,
                    language=language,
                    owner_id=owner_id
                )
                db.session.add(new_project)
            return new_project
        except SQLAlchemyError as e:
            logger.error(f"Failed to create project: {str(e)}")
            return None

    @staticmethod
    def get_all_projects() -> List[Project]:
        def fetch_projects():
            return Project.query.all()
        
        try:
            return ProjectService._retry_operation(fetch_projects)
        except Exception as e:
            logger.error(f"Failed to fetch projects: {str(e)}")
            return []

    @staticmethod
    def get_projects_by_language(language: str) -> List[Project]:
        try:
            return Project.query.filter_by(language=language).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch projects by language: {str(e)}")
            return []

    @staticmethod
    def assign_users_to_project(project_id: int, user_ids: List[int], chapter_id: int) -> bool:
        try:
            with ProjectService.session_scope():
                project = Project.query.get(project_id)
                chapter = Chapter.query.get(chapter_id)
                
                if not project or not chapter or chapter.project_id != project_id:
                    logger.warning("Invalid project or chapter ID")
                    return False
                
                users = User.query.filter(User.id.in_(user_ids)).all()
                if len(users) != len(user_ids):
                    logger.warning("Not all users found")
                    return False
                
                for user in users:
                    db.session.execute(project_user.insert().values(
                        user_id=user.id,
                        project_id=project.id,
                        chapter_id=chapter.id
                    ))
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to assign users to project: {str(e)}")
            return False

    @staticmethod
    def get_projects_by_user(user_id: int) -> List[Project]:
        try:
            user = User.query.get(user_id)
            return user.projects.all() if user else []
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch projects for user {user_id}: {str(e)}")
            return []

    @staticmethod
    def get_projects_by_user_organization(organization: str) -> List[Project]:
        try:
            return Project.query.join(User).filter(User.organization == organization).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch projects for organization {organization}: {str(e)}")
            return []