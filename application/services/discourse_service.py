# from application.extensions import db
# from application.models.discourse_model import Discourse
# from application.models.lexical_conceptual_model import LexicalConceptual
# from application.models.segment_model import Segment 

# class DiscourseService:
#     @staticmethod
#     def create_discourse_by_segment(segment_id, discourse_data):
#         created_discourse = []
#         for data in discourse_data:
#             lexical_concept = LexicalConceptual.query.filter_by(
#                 segment_id=segment_id,
#                 index=data['index']
#             ).first()

#             concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

#             discourse = Discourse(
#                 segment_id=segment_id,
#                 segment_index=data['segment_index'],
#                 index=data['index'],
#                 head_index=data.get('head_index'),
#                 relation=data.get('relation'),
#                 concept_id=concept_id,
#                 discourse=data['discourse']
#             )
#             db.session.add(discourse)
#             created_discourse.append(discourse)
        
#         db.session.commit()
#         return created_discourse


#     @staticmethod
#     def update_discourse_by_segment(segment_id, discourse_data, is_finalized):
#         existing_discourse = Discourse.query.filter_by(segment_id=segment_id).all()
#         existing_discourse_dict = {discourse.discourse_id: discourse for discourse in existing_discourse}

#         for data in discourse_data:
#             discourse_id = data.get('discourse_id')
#             segment_index = data['segment_index']
#             index = data['index']
#             head_index = data.get('head_index')
#             relation = data.get('relation')
#             concept_id = data.get('concept_id')
#             discourse_text = data['discourse']

#             if discourse_id and discourse_id in existing_discourse_dict:
#                 discourse = existing_discourse_dict[discourse_id]
#                 discourse.segment_index = segment_index
#                 discourse.index = index
#                 discourse.head_index = head_index
#                 discourse.relation = relation
#                 discourse.concept_id = concept_id
#                 discourse.discourse = discourse_text
#             else:
#                 discourse = Discourse(
#                     segment_id=segment_id,
#                     segment_index=segment_index,
#                     index=index,
#                     head_index=head_index,
#                     relation=relation,
#                     concept_id=concept_id,
#                     discourse=discourse_text
#                 )
#                 db.session.add(discourse)

#         # ✅ Ensure all discourse records for this segment are finalized
#         Discourse.query.filter_by(segment_id=segment_id).update({"isFinalized": is_finalized})

#         db.session.commit()
#         return True

    
#     @staticmethod
#     def finalize_segment(segment_id):
#         segment = Segment.query.get(segment_id)
#         if segment:
#             segment.status = 'finalized' 
#             db.session.commit()


from application.extensions import db
from application.models.discourse_model import Discourse
from application.models.lexical_conceptual_model import LexicalConceptual
from application.models.segment_model import Segment
from sqlalchemy.exc import SQLAlchemyError

class DiscourseService:
    @staticmethod
    def create_discourse_by_segment(segment_id, discourse_data):
        created_discourse = []
        try:
            for data in discourse_data:
                # Find the lexical_conceptual_id using the segment_id and index
                lexical_concept = LexicalConceptual.query.filter_by(
                    segment_id=segment_id,
                    index=data['index']
                ).first()

                concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

                discourse = Discourse(
                    segment_id=segment_id,
                    segment_index=data['segment_index'],
                    index=data['index'],
                    head_index=data.get('head_index'),
                    relation=data.get('relation'),
                    concept_id=concept_id,
                    discourse=data['discourse']
                )
                db.session.add(discourse)
                created_discourse.append(discourse)
            
            db.session.commit()
            return created_discourse
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error creating discourse data: {str(e)}")
            return []

    @staticmethod
    def update_discourse_by_segment(segment_id, discourse_data, is_finalized):
        try:
            # Fetch and lock existing discourse records for the segment
            existing_discourse = Discourse.query.filter_by(segment_id=segment_id).with_for_update().all()
            existing_discourse_dict = {discourse.discourse_id: discourse for discourse in existing_discourse}

            for data in discourse_data:
                discourse_id = data.get('discourse_id')
                segment_index = data['segment_index']
                index = data['index']
                head_index = data.get('head_index')
                relation = data.get('relation')
                concept_id = data.get('concept_id')
                discourse_text = data['discourse']

                if discourse_id and discourse_id in existing_discourse_dict:
                    # Update existing discourse record
                    discourse = existing_discourse_dict[discourse_id]
                    discourse.segment_index = segment_index
                    discourse.index = index
                    discourse.head_index = head_index
                    discourse.relation = relation
                    discourse.concept_id = concept_id
                    discourse.discourse = discourse_text
                else:
                    # Create a new discourse record if not found
                    discourse = Discourse(
                        segment_id=segment_id,
                        segment_index=segment_index,
                        index=index,
                        head_index=head_index,
                        relation=relation,
                        concept_id=concept_id,
                        discourse=discourse_text
                    )
                    db.session.add(discourse)

            # ✅ Ensure all discourse records for this segment are finalized
            Discourse.query.filter_by(segment_id=segment_id).update({"isFinalized": is_finalized})

            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating discourse data: {str(e)}")
            return False

    @staticmethod
    def finalize_segment(segment_id):
        try:
            segment = Segment.query.get(segment_id)
            if segment:
                segment.status = 'finalized'
                db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error finalizing segment: {str(e)}")
