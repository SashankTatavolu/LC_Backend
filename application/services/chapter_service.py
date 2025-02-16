from application.models.chapter_model import Chapter
from application.models.project_model import Project
from application.models.segment_model import Segment
from application.models.sentence_model import Sentence
from application.models.user_model import User
from application.extensions import db
from application.extensions import mail 
from flask_mail import Message

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
    
    @staticmethod
    def get_chapters_by_chapter_id(chapter_id):
        return Chapter.query.filter_by(id=chapter_id).all()
    
    @staticmethod
    def get_chapters_by_chapter_id(chapter_id):
        return Chapter.query.filter_by(id=chapter_id).first()

    @staticmethod
    def notify_users(user_ids, project_id, chapter_name):
        users = User.query.filter(User.id.in_(user_ids)).all()
        project = Project.query.get(project_id)  
        
        if not project:
            print(f'Project with ID {project_id} not found.')
            return
        
        project_name = project.name
        
        for user in users:
            # ChapterService.send_email(user.email, project_name, chapter_name)
            ChapterService.send_email(user.email, project_name, chapter_name, doc_path="application/docs/LC_Document.pdf", url="http://localhost:5000/")
            
    # @staticmethod
    # def send_email(user_email, project_name, chapter_name):
    #     print(user_email,project_name,chapter_name)
    #     sender_email = "eswarkartheekgrandhi@gmail.com"
    #     sender_password = "twdx pidz jgea rsza"
        
    #     msg = Message(f'New Chapter Assigned: {chapter_name}',
    #                   sender=sender_email,
    #                   recipients=[user_email])
    #     msg.body = f'You have been assigned to the chapter "{chapter_name}" in the project "{project_name}".'
        
    #     try:
    #         mail.send(msg)
    #         print(f'Email sent to {user_email}')
    #     except Exception as e:
    #         print(f'Failed to send email to {user_email}: {e}')

    @staticmethod
    def send_email(user_email, project_name, chapter_name, doc_path=None, url=None):
        print(user_email, project_name, chapter_name)
        sender_email = "sashanktatavolu@gmail.com"
        sender_password = "twdx pidz jgea rsza"

        subject = f'New Chapter Assigned: "{chapter_name}"'

        body = (
            f"<p>Dear {user_email.split('@')[0].capitalize()},</p>"
            f"<p>We are excited to inform you that you have been assigned to a new chapter in the project <strong>{project_name}</strong>.</p>"
            f"<p><strong>Chapter Name</strong>: {chapter_name}</p>"
        )
        
        if url:
            body += f"<p>You can access the platform using the following link:<br><a href='{url}'>{url}</a></p>"
        
        if doc_path:
            body += (
                "<p>Please refer to the attached PDF document for instructions on how to access the tool.</p>"
            )

        body += (
            "<p>If you have any questions or need further assistance, please don't hesitate to reach out to our support team:</p>"
            "<ul>"
            "<li>Sashank Tatavolu: sashank.tatavolu@research.iiit.ac.in</li>"
            "<li>Kartheek Grandhi: kartheek.grandhi@research.iiit.ac.in</li>"
            "</ul>"
            "<p>Best regards,<br>The Project Team</p>"
        )

        msg = Message(subject,
                    sender=sender_email,
                    recipients=[user_email])
        msg.html = body  

        if doc_path:
            with open(doc_path, 'rb') as f:
                msg.attach(
                    filename=doc_path.split("/")[-1],
                    content_type="application/octet-stream",
                    data=f.read()
                )

        try:
            mail.send(msg)
            print(f'Email sent to {user_email}')
        except Exception as e:
            print(f'Failed to send email to {user_email}: {e}')

    @staticmethod
    def get_users_assigned_to_chapter(chapter_id):
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return None
        
        assigned_users = chapter.assigned_users
        assigned_users_data = [{
            # 'id': user.id,
            'username': user.username,
            'email': user.email  ,
            'role': user.role
        } for user in assigned_users]
        
        return assigned_users_data
        
    # @staticmethod
    # def get_segments_by_chapter_id(chapter_id):
    #     segments = Segment.query.join(Sentence).filter(Sentence.chapter_id == chapter_id).all()
    #     return segments

    # @staticmethod
    # def get_sentences_by_chapter_id(chapter_id):
    #     return Sentence.query.filter_by(chapter_id=chapter_id).all()
    @staticmethod
    def get_sentences_by_chapter_id(chapter_id):
        return Sentence.query.filter_by(chapter_id=chapter_id).order_by(Sentence.sentence_id).all()


    @staticmethod
    def get_segments_by_sentence_ids(sentence_ids):
        return Segment.query.filter(Segment.sentence_id.in_(sentence_ids)).all()

    @staticmethod
    def get_segment_indices_by_chapter(chapter_id):
        segments = (
            db.session.query(Segment.segment_index)
            .join(Sentence, Segment.sentence_id == Sentence.id)
            .filter(Sentence.chapter_id == chapter_id)
            .all()
        )
        segment_indices = [segment.segment_index for segment in segments]
        
        return segment_indices

        
