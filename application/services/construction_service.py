
from application.extensions import db
from application.models.construction_model import Construction
from application.models.lexical_conceptual_model import LexicalConceptual

class ConstructionService:
    @staticmethod
    def create_construction_by_segment(segment_id, construction_data):
        created_construction = []
        try:
            for data in construction_data:
                # Find the lexical_conceptual_id using the segment_id and index
                lexical_concept = LexicalConceptual.query.with_for_update().filter_by(
                    segment_id=segment_id,
                    index=data['index']
                ).first()

                concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

                construction = Construction(
                    segment_id=segment_id,
                    segment_index=data['segment_index'],
                    index=data['index'],
                    cxn_index=data['cxn_index'],
                    component_type=data['component_type'],
                    concept_id=concept_id,
                    construction=data['construction']
                )
                db.session.add(construction)
                db.session.flush()
                created_construction.append(construction)

            db.session.commit()
            return created_construction
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update_construction_by_segment(segment_id, construction_data, is_finalized):
        try:
            existing_construction = Construction.query.with_for_update().filter_by(segment_id=segment_id).all()
            existing_construction_dict = {con.construction_id: con for con in existing_construction}

            for data in construction_data:
                construction_id = data.get('construction_id')
                segment_index = data['segment_index']
                index = data['index']
                cxn_index = data['cxn_index']
                component_type = data['component_type']
                concept_id = data.get('concept_id')
                construction_text = f"{cxn_index}:{component_type}"

                if construction_id and construction_id in existing_construction_dict:
                    # Update existing construction
                    construction = existing_construction_dict[construction_id]
                    construction.segment_index = segment_index
                    construction.index = index
                    construction.cxn_index = cxn_index
                    construction.component_type = component_type
                    construction.concept_id = concept_id
                    construction.construction = construction_text
                else:
                    # Create a new construction entry if not found
                    construction = Construction(
                        segment_id=segment_id,
                        segment_index=segment_index,
                        index=index,
                        cxn_index=cxn_index,
                        component_type=component_type,
                        concept_id=concept_id,
                        construction=construction_text
                    )
                    db.session.add(construction)

            # ✅ Ensure all construction records for this segment are finalized
            Construction.query.filter_by(segment_id=segment_id).update({"isFinalized": is_finalized})

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
