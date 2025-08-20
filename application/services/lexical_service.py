from sqlite3 import OperationalError
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

    from sqlalchemy.exc import IntegrityError, OperationalError

    @staticmethod
    def update_lexicals_by_segment(segment_id, lexicals_data, is_finalized):
        try:
            existing_lexicals = LexicalConceptual.query \
                .filter_by(segment_id=segment_id) \
                .with_for_update() \
                .all()

            existing_lexicals_dict = {
                (lex.segment_index, lex.index): lex
                for lex in existing_lexicals
            }

            for data in lexicals_data:
                segment_index = data['segment_index']
                new_index = data['index']
                concept = data['concept']

                key = (segment_index, new_index)

                if key in existing_lexicals_dict:
                    # UPDATE existing
                    lexical = existing_lexicals_dict[key]
                    lexical.concept = concept
                    lexical.semantic_category = data.get('semantic_category')
                    lexical.morpho_semantics = data.get('morpho_semantics')
                    lexical.speakers_view = data.get('speakers_view')

                else:
                    # INSERT new
                    lexical = LexicalConceptual(
                        segment_id=segment_id,
                        segment_index=segment_index,
                        index=new_index,
                        concept=concept,
                        semantic_category=data.get('semantic_category'),
                        morpho_semantics=data.get('morpho_semantics'),
                        speakers_view=data.get('speakers_view'),
                        isFinalized=is_finalized
                    )
                    db.session.add(lexical)

            # Also update isFinalized on all rows under this segment
            LexicalConceptual.query \
                .filter_by(segment_id=segment_id) \
                .update({"isFinalized": is_finalized})

            db.session.commit()
            return True, "Lexicals Updated Successfully"

        except Exception as e:
            db.session.rollback()
            print("Error in update_lexicals_by_segment:", e)
            return False , "Failed to update"



    @staticmethod
    def is_concept_generated(segment_id):
        lexical_entries = LexicalConceptual.query.filter_by(segment_id=segment_id).all()
        is_generated = any(entry.concept is not None for entry in lexical_entries)
        column_count = len(lexical_entries)
        return is_generated, column_count
