# from application.extensions import db
# from application.models.domain_term_model import DomainTerm
# from application.models.lexical_conceptual_model import LexicalConceptual
# from application.models.segment_model import Segment

# class DomainTermService:
#     @staticmethod
#     def create_domain_term_by_segment(segment_id, domain_data):
#         created_domain_terms = []
#         for data in domain_data:
#             # Find the lexical_conceptual_id using the segment_id and index
#             lexical_concept = LexicalConceptual.query.filter_by(
#                 segment_id=segment_id,
#                 index=data['index']
#             ).first()

#             concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

#             domain_term = DomainTerm(
#                 segment_id=segment_id,
#                 segment_index=data['segment_index'],
#                 index=data['index'],
#                 domain_term=data['domain_term'],
#                 concept_id=concept_id
#             )
#             db.session.add(domain_term)
#             created_domain_terms.append(domain_term)
        
#         db.session.commit()

#         # After creating domain term entries, update the segment status to 'finalized'
#         # DomainTermService.finalize_segment(segment_id)
#         return created_domain_terms

#     @staticmethod
#     def update_domain_term_by_segment(segment_id, domain_data):
#         # Fetch existing domain term entries based on segment ID
#         existing_domain_terms = DomainTerm.query.filter_by(segment_id=segment_id).all()
#         existing_domain_dict = {domain.domain_term_id: domain for domain in existing_domain_terms}

#         for data in domain_data:
#             domain_term_id = data.get('domain_term_id')
#             segment_index = data['segment_index']
#             index = data['index']
#             domain_term_text = data['domain_term']
#             concept_id = data.get('concept_id')

#             if domain_term_id and domain_term_id in existing_domain_dict:
#                 # Update existing domain term entry
#                 domain_term = existing_domain_dict[domain_term_id]
#                 domain_term.segment_index = segment_index
#                 domain_term.index = index
#                 domain_term.domain_term = domain_term_text
#                 domain_term.concept_id = concept_id
#             elif domain_term_id:
#                 # If domain_term_id is provided but doesn't exist, return error or skip creation
#                 return False  # Handle this case according to your needs (e.g., throw an error)
#             else:
#                 # Skip creating new entries, ensure only existing records are updated
#                 continue

#         db.session.commit()
#         return True  # Indicate that the update was successful

#     @staticmethod
#     def finalize_segment(segment_id):
#         # Update the status of the segment to 'finalized'
#         segment = Segment.query.get(segment_id)
#         if segment:
#             segment.status = 'finalized'
#             db.session.commit()
