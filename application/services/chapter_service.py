from flask import current_app
from application.models.chapter_model import Chapter
from application.models.project_model import Project
from application.models.segment_model import Segment
from application.models.sentence_model import Sentence
from application.models.construction_model import Construction
from application.models.lexical_conceptual_model import LexicalConceptual
from application.models.relational_model import Relational
from application.models.feedback_model import Feedback
from application.models.assignment_model import Assignment
from application.models.discourse_model import Discourse
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
            ChapterService.send_email(user.email, project_name, chapter_name, doc_path="application/docs/LC_Document.pdf", url="https://canvas.iiit.ac.in/lc/")
            
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
        sender_email = "swethapoppoppu@gmail.com"
        sender_password = "ufec wkhp syss ynqa"

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

    
    @classmethod
    def delete_chapter_and_related_data(cls, chapter_id):
        try:
            # Get the chapter first
            chapter = Chapter.query.get(chapter_id)
            if not chapter:
                return False

            # Delete chapter-level assignments first
            Assignment.query.filter_by(chapter_id=chapter_id).delete()
            db.session.flush()

            # Get all sentences for this chapter
            sentences = Sentence.query.filter_by(chapter_id=chapter_id).all()
            
            # For each sentence, delete related data
            for sentence in sentences:
                # Get all segments for this sentence
                segments = Segment.query.filter_by(sentence_id=sentence.id).all()
                
                for segment in segments:
                    # Delete related data
                    Assignment.query.filter_by(segment_id=segment.segment_id).delete()
                    Feedback.query.filter_by(segment_id=segment.segment_id).delete()
                    Discourse.query.filter_by(segment_id=segment.segment_id).delete()
                    Relational.query.filter_by(segment_id=segment.segment_id).delete()
                    Construction.query.filter_by(segment_id=segment.segment_id).delete()
                    LexicalConceptual.query.filter_by(segment_id=segment.segment_id).delete()
                    
                    # Delete the segment itself
                    db.session.delete(segment)
                    db.session.flush()
                
                # Delete the sentence
                db.session.delete(sentence)
                db.session.flush()
            
            # Finally delete the chapter
            db.session.delete(chapter)
            
            # Commit all changes
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting chapter {chapter_id}: {str(e)}")
            raise e