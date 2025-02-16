# from application.extensions import db
# from application.models.relational_model import Relational

# class RelationalService:
#     @staticmethod
#     def create_relational_by_segment(segment_id, relational_data):
#         created_relational = []
#         for data in relational_data:
#             relational = Relational(
#                 segment_id=segment_id,
#                 segment_index=data['segment_index'],
#                 # cxn_index=data['cxn_index'],
#                 component_type=data['component_type']
#             )
#             db.session.add(relational)
#             created_relational.append(relational)
        
#         db.session.commit()
#         return created_relational

#     # @staticmethod
#     # def update_relational_by_segment(segment_id, relational_data):
#     #     existing_relational = Relational.query.filter_by(segment_id=segment_id).all()
#     #     existing_relational_dict = {rel.relational_id: rel for rel in existing_relational}

#     #     updated_relational = []

#     #     for data in relational_data:
#     #         relational_id = data.get('relational_id')
#     #         segment_index = data['segment_index']
#     #         cxn_index = data['cxn_index']

#     #         if relational_id and relational_id in existing_relational_dict:
#     #             relational = existing_relational_dict[relational_id]
#     #         else:
#     #             # If no relational_id or not found, create a new entry
#     #             relational = Relational(segment_id=segment_id)
#     #             db.session.add(relational)

#     #         relational.segment_index = segment_index
#     #         relational.cxn_index = cxn_index
#     #         relational.component_type = data['component_type']
#     #         updated_relational.append(relational)

#     #     db.session.commit()
#     #     return updated_relational

#     @staticmethod
#     def update_relational_by_segment(segment_id, relational_data):
#         existing_relational = Relational.query.filter_by(segment_id=segment_id).all()
#         existing_relational_dict = {rel.relational_id: rel for rel in existing_relational}

#         updated_relational = []

#         for data in relational_data:
#             relational_id = data.get('relational_id')
#             segment_index = data['segment_index']
#             # cxn_index = data['cxn_index']
#             index = data['index']
#             main_index = data['main_index']
#             relation = data['relation']
#             is_main = data['is_main']
#             concept_id = data.get('concept_id')  

#             if relational_id and relational_id in existing_relational_dict:
#                 relational = existing_relational_dict[relational_id]
#             else:
#                 # If no relational_id or not found, create a new entry
#                 relational = Relational(
#                     segment_id=segment_id,
#                     segment_index=segment_index,
#                     # cxn_index=cxn_index,
#                     index=index,
#                     main_index=main_index,
#                     relation=relation,
#                     is_main=is_main,
#                     concept_id=concept_id
#                 )
#                 db.session.add(relational)

#             # Update the relational attributes
#             relational.segment_index = segment_index
#             # relational.cxn_index = cxn_index
#             relational.index = index
#             relational.main_index = main_index
#             relational.relation = relation
#             relational.is_main = is_main
#             relational.concept_id = concept_id
            
#             updated_relational.append(relational)

#         db.session.commit()
#         return updated_relational


from application.extensions import db
from application.models.relational_model import Relational

class RelationalService:
    @staticmethod
    def create_relational_by_segment(segment_id, relational_data):
        created_relational = []
        for data in relational_data:
            relational = Relational(
                segment_id=segment_id,
                segment_index=data['segment_index'],
                index=data['index'],  
                head_relation=data['head_relation'],
                head_index=data['head_index'], 
                relation=data['dep_relation'],  
                is_main=data.get('is_main', False),  
                concept_id=data.get('concept_id') 
            )
            db.session.add(relational)
            created_relational.append(relational)
        
        db.session.commit()
        return created_relational
    
    @staticmethod
    def update_relational_by_segment(segment_id, relational_data, is_finalized):
        existing_relational = Relational.query.filter_by(segment_id=segment_id).all()
        existing_relational_dict = {rel.relational_id: rel for rel in existing_relational}
        
        for data in relational_data:
            relational_id = data.get('relational_id')
            segment_index = data['segment_index']
            index = data['index']
            head_relation = data['head_relation']
            head_index = data['head_index']
            dep_relation = data['dep_relation']
            is_main = data['is_main']
            concept_id = data.get('concept_id')
            
            relational_text = f"{head_index}:{dep_relation}"

            if relational_id and relational_id in existing_relational_dict:
                # Update existing relational record
                relational = existing_relational_dict[relational_id]
                relational.segment_index = segment_index
                relational.index = index
                relational.head_relation = relational_text
                relational.head_index = head_index
                relational.dep_relation = dep_relation
                relational.is_main = is_main
                relational.concept_id = concept_id
            else:
                # Create a new relational record if not found
                relational = Relational(
                    segment_id=segment_id,
                    segment_index=segment_index,
                    index=index,
                    head_relation=head_relation,
                    head_index=head_index,
                    dep_relation=dep_relation,
                    is_main=is_main,
                    concept_id=concept_id
                )
                db.session.add(relational)

        # ✅ Ensure all relational records for this segment are finalized
        Relational.query.filter_by(segment_id=segment_id).update({"isFinalized": is_finalized})

        db.session.commit()
        return True

    # @staticmethod
    # def update_relational_by_segment(segment_id, relational_data):
    #     existing_relational = Relational.query.filter_by(segment_id=segment_id).all()
    #     existing_relational_dict = {rel.relational_id: rel for rel in existing_relational}

    #     updated_relational = []

    #     for data in relational_data:
    #         relational_id = data.get('relational_id')
    #         segment_index = data['segment_index']
    #         index = data['index']
    #         component_type = data['component_type']
    #         main_index = data['main_index']
    #         relation = data['relation']
    #         is_main = data['is_main']
    #         concept_id = data.get('concept_id')  

    #         if relational_id and relational_id in existing_relational_dict:
    #             relational = existing_relational_dict[relational_id]
    #         else:
    #             # If no relational_id or not found, it create a new entry
    #             relational = Relational(
    #                 segment_id=segment_id,
    #                 segment_index=segment_index,
    #                 index=index,
    #                 component_type=component_type,
    #                 main_index=main_index,
    #                 relation=relation,
    #                 is_main=is_main,
    #                 concept_id=concept_id
    #             )
    #             db.session.add(relational)
    #         # Update the relational attributes
    #         relational.segment_index = segment_index
    #         relational.index = index
    #         relational.component_type = component_type
    #         relational.main_index = main_index
    #         relational.relation = relation
    #         relational.is_main = is_main
    #         relational.concept_id = concept_id
            
    #         updated_relational.append(relational)

    #     db.session.commit()
    #     return updated_relational
