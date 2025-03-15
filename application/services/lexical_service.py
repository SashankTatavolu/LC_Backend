# from application.extensions import db
# from application.models.lexical_conceptual_model import LexicalConceptual
# from application.models.relational_model import Relational
# from application.models.construction_model import Construction

# class LexicalService:
#     @staticmethod
#     def get_lexicals_by_segment(segment_id):
#         return LexicalConceptual.query.filter_by(segment_id=segment_id).order_by(LexicalConceptual.lexical_conceptual_id).all()
    
#     @staticmethod
#     def create_lexicals(segment_id, lexicals_data):
#         created_lexicals = []
#         for data in lexicals_data:
#             lexical = LexicalConceptual(
#                 segment_id=segment_id,
#                 segment_index=data['segment_index'],
#                 index=data['index'],
#                 concept=data['concept'],
#                 semantic_category=data.get('semantic_category'),
#                 morpho_semantics=data.get('morpho_semantics'),
#                 speakers_view=data.get('speakers_view'),
#             )
#             db.session.add(lexical)
#             created_lexicals.append(lexical)
        
#         db.session.commit()
#         return created_lexicals

#     @staticmethod
#     def update_lexicals_by_segment(segment_id, lexicals_data, is_finalized):
#         # Fetch existing lexicals based on segment ID
#         existing_lexicals = LexicalConceptual.query.filter_by(segment_id=segment_id).all()
#         existing_lexicals_dict = {(lex.segment_index, lex.index): lex for lex in existing_lexicals}

#         for data in lexicals_data:
#             segment_index = data['segment_index']
#             new_index = data['index']
#             lexical_conceptual_id = data.get('lexical_conceptual_id')

#             if lexical_conceptual_id:
#                 # Update existing lexical concept
#                 lexical = LexicalConceptual.query.get(lexical_conceptual_id)
#                 if lexical and lexical.segment_id == segment_id:
#                     old_index = lexical.index
#                     lexical.segment_index = segment_index
#                     lexical.index = new_index
#                     lexical.concept = data['concept']
#                     lexical.semantic_category = data.get('semantic_category')
#                     lexical.morpho_semantics = data.get('morpho_semantics')
#                     lexical.speakers_view = data.get('speakers_view')

#                     # Update related relational entries
#                     related_relational_entries = Relational.query.filter_by(
#                         segment_id=segment_id,
#                         segment_index=segment_index,
#                         index=old_index
#                     ).all()
#                     for relational in related_relational_entries:
#                         relational.index = new_index

#                     # Update related construction entries
#                     related_construction_entries = Construction.query.filter_by(
#                         segment_id=segment_id,
#                         segment_index=segment_index,
#                         index=old_index
#                     ).all()
#                     for construction in related_construction_entries:
#                         construction.index = new_index
#                 else:
#                     return None  # Invalid `lexical_conceptual_id`
#             else:
#                 # Create a new lexical concept
#                 lexical = LexicalConceptual(
#                     segment_id=segment_id,
#                     segment_index=segment_index,
#                     index=new_index,
#                     concept=data['concept'],
#                     semantic_category=data.get('semantic_category'),
#                     morpho_semantics=data.get('morpho_semantics'),
#                     speakers_view=data.get('speakers_view'),
#                     isFinalized=is_finalized  # <-- Ensure new entries have the correct flag
#                 )
#                 db.session.add(lexical)
#                 db.session.flush()  # Ensure `lexical_conceptual_id` is generated before using it

#                 # Add corresponding relational entry
#                 relational_entry = Relational(
#                     segment_id=segment_id,
#                     segment_index=segment_index,
#                     index=new_index,
#                     component_type="default",  # Replace with actual logic
#                     concept_id=lexical.lexical_conceptual_id
#                 )
#                 db.session.add(relational_entry)

#                 # Add corresponding construction entry
#                 construction_entry = Construction(
#                     segment_id=segment_id,
#                     segment_index=segment_index,
#                     index=new_index,
#                     construction="default",  # Replace with actual logic
#                     cxn_index=0,  # Replace with actual logic
#                     component_type="default",  # Replace with actual logic
#                     concept_id=lexical.lexical_conceptual_id
#                 )
#                 db.session.add(construction_entry)

#         # **Update `isFinalized` flag for all lexicals under this segment**
#         LexicalConceptual.query.filter_by(segment_id=segment_id).update({"isFinalized": is_finalized})

#         db.session.commit()
#         return True  # Indicate that the update was successful



    


#     @staticmethod
#     def is_concept_generated(segment_id):
#         lexical_entries = LexicalConceptual.query.filter_by(segment_id=segment_id).all()
#         is_generated = any(entry.concept is not None for entry in lexical_entries)
#         column_count = len(lexical_entries)
#         return is_generated, column_count



from application.extensions import db
from application.models.lexical_conceptual_model import LexicalConceptual
from application.models.relational_model import Relational
from application.models.construction_model import Construction
from sqlalchemy.exc import IntegrityError

class LexicalService:
    @staticmethod
    def get_lexicals_by_segment(segment_id):
        return LexicalConceptual.query.filter_by(segment_id=segment_id).order_by(LexicalConceptual.lexical_conceptual_id).all()

    @staticmethod
    def create_lexicals(segment_id, lexicals_data):
        created_lexicals = []
        try:
            for data in lexicals_data:
                lexical = LexicalConceptual(
                    segment_id=segment_id,
                    segment_index=data['segment_index'],
                    index=data['index'],
                    concept=data['concept'],
                    semantic_category=data.get('semantic_category'),
                    morpho_semantics=data.get('morpho_semantics'),
                    speakers_view=data.get('speakers_view'),
                )
                db.session.add(lexical)
                created_lexicals.append(lexical)

            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return None
        return created_lexicals

    @staticmethod
    def update_lexicals_by_segment(segment_id, lexicals_data, is_finalized):
        try:
            existing_lexicals = LexicalConceptual.query.filter_by(segment_id=segment_id).with_for_update().all()
            existing_lexicals_dict = {(lex.segment_index, lex.index): lex for lex in existing_lexicals}

            for data in lexicals_data:
                segment_index = data['segment_index']
                new_index = data['index']
                lexical_conceptual_id = data.get('lexical_conceptual_id')

                if lexical_conceptual_id:
                    lexical = LexicalConceptual.query.get(lexical_conceptual_id)
                    if lexical and lexical.segment_id == segment_id:
                        old_index = lexical.index
                        lexical.segment_index = segment_index
                        lexical.index = new_index
                        lexical.concept = data['concept']
                        lexical.semantic_category = data.get('semantic_category')
                        lexical.morpho_semantics = data.get('morpho_semantics')
                        lexical.speakers_view = data.get('speakers_view')

                        # Update related relational entries
                        Relational.query.filter_by(
                            segment_id=segment_id,
                            segment_index=segment_index,
                            index=old_index
                        ).update({"index": new_index})

                        # Update related construction entries
                        Construction.query.filter_by(
                            segment_id=segment_id,
                            segment_index=segment_index,
                            index=old_index
                        ).update({"index": new_index})

                else:
                    lexical = LexicalConceptual(
                        segment_id=segment_id,
                        segment_index=segment_index,
                        index=new_index,
                        concept=data['concept'],
                        semantic_category=data.get('semantic_category'),
                        morpho_semantics=data.get('morpho_semantics'),
                        speakers_view=data.get('speakers_view'),
                        isFinalized=is_finalized
                    )
                    db.session.add(lexical)

            # Update `isFinalized` flag for all lexicals under this segment
            LexicalConceptual.query.filter_by(segment_id=segment_id).update({"isFinalized": is_finalized})

            db.session.commit()
            return True

        except IntegrityError:
            db.session.rollback()
            return False

    @staticmethod
    def is_concept_generated(segment_id):
        lexical_entries = LexicalConceptual.query.filter_by(segment_id=segment_id).all()
        is_generated = any(entry.concept is not None for entry in lexical_entries)
        column_count = len(lexical_entries)
        return is_generated, column_count
