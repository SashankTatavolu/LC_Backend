from application.extensions import db
from application.models.segment_model import Segment
import os 
import subprocess
from application.extensions import db
from application.models.lexical_conceptual_model import LexicalConceptual
from application.models.relational_model import Relational
from application.models.discourse_model import Discourse
from application.models.construction_model import Construction
from application.models.user_model import User

class SegmentService:
    @staticmethod
    def get_segment_by_id(segment_id):
        return Segment.query.filter_by(segment_id=segment_id).first()

    @staticmethod
    def create_segment(data):
        segment = Segment(
            sentence_id=data['sentence_id'],
            segment_index=data['segment_index'],
            segment_text=data['segment_text'],
            segment_type=data['segment_type'],
            index_type = data['index_type']
        )
        db.session.add(segment)
        db.session.commit()
        return segment

    @staticmethod
    def update_segment(segment_id, data):
        segment = Segment.query.filter_by(segment_id=segment_id).first()
        if segment:
            segment.sentence_id = data.get('sentence_id', segment.sentence_id)
            segment.segment_index = data.get('segment_index', segment.segment_index)
            segment.segment_text = data.get('segment_text', segment.segment_text)
            segment.segment_type = data.get('segment_type', segment.segment_type)
            segment.index_type = data.get('index_type', segment.index_type)
            db.session.commit()
        return segment

    @staticmethod
    def delete_segment(segment_id):
        segment = Segment.query.filter_by(segment_id=segment_id).first()
        if segment:
            db.session.delete(segment)
            db.session.commit()
        return segment

    @staticmethod
    def create_segments(sentence_id, segments_data):
        segments = []
        for data in segments_data:
            segment = Segment(
                sentence_id=sentence_id,
                segment_index=data.get('segment_index'),
                segment_text=data.get('segment_text'),
                segment_type=data.get('segment_type'),
                index_type=data.get('index_type')
            )
            db.session.add(segment)
            segments.append(segment)
        db.session.commit()
        return segments

    @staticmethod
    def update_segments_by_sentence(sentence_id, segments_data):
        existing_segments = Segment.query.filter_by(sentence_id=sentence_id).all()
        existing_segments_dict = {seg.segment_index: seg for seg in existing_segments}

        new_indices = {data['segment_index'] for data in segments_data}

        for data in segments_data:
            segment_index = data['segment_index']
            
            # Update existing segment if found, otherwise create a new one
            if segment_index in existing_segments_dict:
                segment = existing_segments_dict[segment_index]
            else:
                segment = Segment(sentence_id=sentence_id)
                db.session.add(segment)

            segment.segment_index = data['segment_index']
            segment.segment_text = data['segment_text']
            segment.segment_type = data['segment_type']
            segment.index_type = data['index_type']

        db.session.commit()
        
        return Segment.query.filter_by(sentence_id=sentence_id).all()
    
    @staticmethod
    # Function to convert text to WX format using utf8_wx script
    def text_to_wx(input_text):
        try:
            with open('temp_input.txt', 'w') as f:
                f.write(input_text)
            
            # Execute the utf8_wx shell script with the input file
            result = subprocess.run(
                ["/bin/bash", "utf8_wx", "temp_input.txt"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                try:
                    return result.stdout.decode('utf-8')
                except UnicodeDecodeError:
                    return result.stdout.decode('utf-8', errors='replace')
            else:
                # Log or return stderr output in case of error
                return f"Error during conversion: {result.stderr.decode('utf-8', errors='replace')}"
        
        finally:
            # Clean up the temporary file
            if os.path.exists('temp_input.txt'):
                os.remove('temp_input.txt')
                
                
    @staticmethod
    def get_segments_count_by_chapter(chapter_id):
        """
        Get the number of segments in a specific chapter.
        
        :param chapter_id: ID of the chapter to count segments for.
        :return: Number of segments in the chapter.
        """
        return Segment.query.filter_by(chapter_id=chapter_id).count()

 
    @staticmethod
    def get_is_finalized_status(segment_id):
        """
        Fetches the isFinalized status for all related tables based on segment_id.
        """
        lexical = db.session.query(LexicalConceptual.isFinalized).filter_by(segment_id=segment_id).all()
        relational = db.session.query(Relational.isFinalized).filter_by(segment_id=segment_id).all()
        discourse = db.session.query(Discourse.isFinalized).filter_by(segment_id=segment_id).all()
        construction = db.session.query(Construction.isFinalized).filter_by(segment_id=segment_id).all()

        return {
            "lexical_conceptual": [status[0] for status in lexical],  # Extracting only values
            "relational": [status[0] for status in relational],
            "discourse": [status[0] for status in discourse],
            "construction": [status[0] for status in construction]
        }

