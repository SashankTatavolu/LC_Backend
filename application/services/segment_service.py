from application.extensions import db
from application.models.segment_model import Segment
from application.models.assignment_model import Assignment
from application.services.chapter_service import ChapterService
from application.models.lexical_conceptual_model import LexicalConceptual
from application.models.relational_model import Relational
from application.models.discourse_model import Discourse
from application.models.construction_model import Construction
from application.models.chapter_model import Chapter

class SegmentService:
    @staticmethod
    def get_segment_by_id(segment_id):
        return Segment.query.filter_by(segment_id=segment_id).first()

    @staticmethod
    def create_segment(data):
        segment = Segment(
            sentence_id=data['sentence_id'],
            chapter_id=data['chapter_id'],  # Added chapter_id
            segment_index=data['segment_index'],
            segment_text=data['segment_text'],
            english_text=data.get('english_text'),  # Added english_text
            wx_text=data.get('wx_text'),  # Added wx_text
            segment_type=data['segment_type'],
            index_type=data['index_type'],
            status=data.get('status', 'pending')  # Default status as pending
        )
        db.session.add(segment)
        db.session.commit()
        return segment

    @staticmethod
    def update_segment(segment_id, data):
        segment = Segment.query.filter_by(segment_id=segment_id).first()
        if segment:
            segment.sentence_id = data.get('sentence_id', segment.sentence_id)
            segment.chapter_id = data.get('chapter_id', segment.chapter_id)
            segment.segment_index = data.get('segment_index', segment.segment_index)
            segment.segment_text = data.get('segment_text', segment.segment_text)
            segment.english_text = data.get('english_text', segment.english_text)
            segment.wx_text = data.get('wx_text', segment.wx_text)
            segment.segment_type = data.get('segment_type', segment.segment_type)
            segment.index_type = data.get('index_type', segment.index_type)
            segment.status = data.get('status', segment.status)
            db.session.commit()
        return segment

    
    
    
    @staticmethod
    def delete_segment(segment_id):
        try:
            # Get the exact segment with all its relationships
            segment = db.session.query(Segment).filter_by(segment_id=segment_id).first()
            if not segment:
                return False

            # Check for any dependencies
            has_dependencies = (
                db.session.query(LexicalConceptual)
                .filter_by(segment_id=segment_id)
                .first() is not None or
                db.session.query(Relational)
                .filter_by(segment_id=segment_id)
                .first() is not None or
                db.session.query(Discourse)
                .filter_by(segment_id=segment_id)
                .first() is not None or
                db.session.query(Construction)
                .filter_by(segment_id=segment_id)
                .first() is not None
            )

            if has_dependencies:
                raise ValueError("Cannot delete segment with existing dependencies")

            # Delete assignments first
            Assignment.query.filter_by(segment_id=segment_id).delete()

            # Now delete the segment
            db.session.delete(segment)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting segment {segment_id}: {e}")
            return False


    @staticmethod
    def create_segments(sentence_id, chapter_id, segments_data):
        segments = []
        for data in segments_data:
            segment = Segment(
                sentence_id=sentence_id,
                chapter_id=chapter_id,  # Ensure chapter_id is included
                segment_index=data.get('segment_index'),
                segment_text=data.get('segment_text'),
                english_text=data.get('english_text'),
                wx_text=data.get('wx_text'),
                segment_type=data.get('segment_type'),
                index_type=data.get('index_type'),
                status=data.get('status', 'pending')
            )
            db.session.add(segment)
            segments.append(segment)
        db.session.commit()
        return segments

    @staticmethod
    def update_segments_by_sentence(sentence_id, segments_data):
        existing_segments = Segment.query.filter_by(sentence_id=sentence_id).all()
        existing_segments_dict = {seg.segment_index: seg for seg in existing_segments}

        for data in segments_data:
            segment_index = data['segment_index']
            
            if segment_index in existing_segments_dict:
                segment = existing_segments_dict[segment_index]
            else:
                segment = Segment(sentence_id=sentence_id, chapter_id=data['chapter_id'])
                db.session.add(segment)

            segment.segment_index = data['segment_index']
            segment.segment_text = data['segment_text']
            segment.english_text = data.get('english_text', segment.english_text)
            segment.wx_text = data.get('wx_text', segment.wx_text)
            segment.segment_type = data['segment_type']
            segment.index_type = data['index_type']
            segment.status = data.get('status', segment.status)

        db.session.commit()
        return Segment.query.filter_by(sentence_id=sentence_id).all()

    @staticmethod
    def get_segments_count_by_chapter(chapter_id):
        return Segment.query.filter_by(chapter_id=chapter_id).count()

    @staticmethod
    def get_is_finalized_status(segment_id):
        lexical = db.session.query(LexicalConceptual.isFinalized).filter_by(segment_id=segment_id).all()
        relational = db.session.query(Relational.isFinalized).filter_by(segment_id=segment_id).all()
        discourse = db.session.query(Discourse.isFinalized).filter_by(segment_id=segment_id).all()
        construction = db.session.query(Construction.isFinalized).filter_by(segment_id=segment_id).all()

        return {
            "lexical_conceptual": [status[0] for status in lexical],
            "relational": [status[0] for status in relational],
            "discourse": [status[0] for status in discourse],
            "construction": [status[0] for status in construction]
        }
         
    @staticmethod
    def create_segments_bulk(segments_data):
        """
        Bulk insert segments into the database.
        :param segments_data: List of segment dictionaries
        :return: List of created segments
        """
        created_segments = []
        try:
            for segment in segments_data:
                new_segment = Segment(
                    sentence_id=segment['sentence_id'],
                    chapter_id=segment['chapter_id'],
                    segment_index=segment['segment_index'],
                    segment_text=segment['segment_text'],
                    wx_text=segment.get('wx_text'),
                    english_text=segment.get('english_text'),
                    segment_type=segment.get('segment_type', " "),
                    index_type=segment.get('index_type', "type"),
                )
                db.session.add(new_segment)
                created_segments.append(new_segment)

            db.session.commit()
            return created_segments

        except Exception as e:
            db.session.rollback()
            print(f"Error inserting segments: {e}")
            return []
    
    @staticmethod
    def assign_user_to_tab(user_id, segment_id, tab_name):
        # Check if this segment + tab is already assigned
        existing_assignment = Assignment.query.filter_by(
            segment_id=segment_id,
            tab_name=tab_name
        ).first()

        if existing_assignment:
            assigned_user = existing_assignment.user
            segment = Segment.query.get(segment_id)

            return {
                'error': f"This segment (ID: {segment_id}) is already assigned.",
                'details': {
                    'assigned_user': assigned_user.username,
                    'user_id': assigned_user.id,
                    'tab_name': tab_name,
                    'segment_index': segment.segment_index if segment else None
                }
            }

        segment = Segment.query.get(segment_id)
        if not segment:
            return {'error': 'Segment not found.'}

        assignment = Assignment(
            user_id=user_id,
            segment_id=segment_id,
            tab_name=tab_name,
            chapter_id=segment.chapter_id  # assuming the Segment model has this field
        )
        db.session.add(assignment)
        db.session.commit()

        return assignment



    

    @staticmethod
    def get_assigned_users(segment_id, tab_name):
        """
        Get users assigned to a specific tab of a segment.
        """
        assignments = Assignment.query.filter_by(segment_id=segment_id, tab_name=tab_name).all()
        return [assignment.serialize() for assignment in assignments]
    
    @staticmethod
    def get_is_finalized_status(segment_id):
        lexical = db.session.query(LexicalConceptual.isFinalized).filter_by(segment_id=segment_id).all()
        relational = db.session.query(Relational.isFinalized).filter_by(segment_id=segment_id).all()
        discourse = db.session.query(Discourse.isFinalized).filter_by(segment_id=segment_id).all()
        construction = db.session.query(Construction.isFinalized).filter_by(segment_id=segment_id).all()

        lexical_finalized = all(status[0] for status in lexical) if lexical else False
        relational_finalized = all(status[0] for status in relational) if relational else False
        discourse_finalized = all(status[0] for status in discourse) if discourse else False
        construction_finalized = all(status[0] for status in construction) if construction else False

        is_completed = lexical_finalized and relational_finalized and discourse_finalized and construction_finalized

        return {
            "lexical_conceptual": lexical_finalized,
            "relational": relational_finalized,
            "discourse": discourse_finalized,
            "construction": construction_finalized,
            "is_completed": is_completed
        }

    @staticmethod
    def get_completed_segments_count_by_chapter(chapter_id):
        """
        Count how many segments in a chapter are fully finalized.
        A segment is considered finalized if all four categories are marked as True.
        """
        from sqlalchemy.sql import exists

        completed_count = (
            db.session.query(Segment.segment_id)
            .filter(Segment.chapter_id == chapter_id)
            .filter(
                exists().where(
                    LexicalConceptual.segment_id == Segment.segment_id
                ).where(LexicalConceptual.isFinalized == True),
                exists().where(
                    Relational.segment_id == Segment.segment_id
                ).where(Relational.isFinalized == True),
                exists().where(
                    Discourse.segment_id == Segment.segment_id
                ).where(Discourse.isFinalized == True),
                exists().where(
                    Construction.segment_id == Segment.segment_id
                ).where(Construction.isFinalized == True)
            )
            .count()
        )

        return completed_count

    @staticmethod
    def get_finalized_counts_by_chapter(chapter_id):
        """
        Get the count of segments in a chapter that have finalized lexical_conceptual, relational, 
        construction, and discourse components. Also includes fully finalized and pending segments.
        """
        from sqlalchemy.sql import func

        # Get chapter name
        chapter = db.session.query(Chapter).filter_by(id=chapter_id).first()
        chapter_name = chapter.name if chapter else None

        # Get all segment IDs in this chapter
        all_segment_ids = db.session.query(Segment.segment_id).filter(Segment.chapter_id == chapter_id).all()
        all_segment_ids = {s[0] for s in all_segment_ids}
        total_segments = len(all_segment_ids)

        # Query finalized segment IDs per component
        lexical_set = {
            s[0] for s in db.session.query(LexicalConceptual.segment_id)
            .join(Segment, Segment.segment_id == LexicalConceptual.segment_id)
            .filter(Segment.chapter_id == chapter_id, LexicalConceptual.isFinalized == True)
            .distinct().all()
        }

        relational_set = {
            s[0] for s in db.session.query(Relational.segment_id)
            .join(Segment, Segment.segment_id == Relational.segment_id)
            .filter(Segment.chapter_id == chapter_id, Relational.isFinalized == True)
            .distinct().all()
        }

        construction_set = {
            s[0] for s in db.session.query(Construction.segment_id)
            .join(Segment, Segment.segment_id == Construction.segment_id)
            .filter(Segment.chapter_id == chapter_id, Construction.isFinalized == True)
            .distinct().all()
        }

        discourse_set = {
            s[0] for s in db.session.query(Discourse.segment_id)
            .join(Segment, Segment.segment_id == Discourse.segment_id)
            .filter(Segment.chapter_id == chapter_id, Discourse.isFinalized == True)
            .distinct().all()
        }

        # Fully finalized = intersection of all sets
        fully_finalized_segments = lexical_set & relational_set & construction_set & discourse_set
        fully_finalized_count = len(fully_finalized_segments)

        # Pending segments = all segments - fully finalized ones
        pending_segments = all_segment_ids - fully_finalized_segments
        pending_count = len(pending_segments)

        return {
            "chapter_name": chapter_name,
            "total_segments": total_segments,
            "lexical_finalized": len(lexical_set),
            "relational_finalized": len(relational_set),
            "construction_finalized": len(construction_set),
            "discourse_finalized": len(discourse_set),
            "fully_finalized": fully_finalized_count,
            "pending_segments": pending_count
        }

