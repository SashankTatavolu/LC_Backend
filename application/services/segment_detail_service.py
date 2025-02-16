from application.extensions import db
from application.models.segment_model import Segment
from application.models.sentence_model import Sentence
from application.models.chapter_model import Chapter
from application.models.lexical_conceptual_model import LexicalConceptual
from application.models.relational_model import Relational
from application.models.discourse_model import Discourse
from application.models.construction_model import Construction
# from application.models.domain_term_model import DomainTerm
from application.segment_repository.sentence_chunker import SentenceChunkerMain
from application.segment_repository.segmentor import Segmentor
from io import BytesIO
import os
import subprocess
import re
import xml.etree.ElementTree as ET
from sqlalchemy.sql import text

class SegmentDetailService:
    
    @staticmethod
    def process_sentences(sentences, chapter_id):
        chunker_outputs = SentenceChunkerMain.main(sentences)
        sentence_id = 1
        processed_results = []
        
        for chunks in chunker_outputs:
            segmentor = Segmentor(chunks)
            segmentor.process()
            segmented_sentences = segmentor.arr
            sentences_with_full_stop = Segmentor.add_purnaviram(segmented_sentences)
            segmentor.arr = sentences_with_full_stop
            output = segmentor.write_output(sentence_id)
            print("o: ",output)
            print(output['sentence_text'])

            # Create or update the sentence in the database
            # sentence_index = Sentence.next_sentence_index(chapter_id)
            sentence = Sentence(
                chapter_id=chapter_id,
                sentence_index=str(sentence_id),
                sentence_id=str(sentence_id),  
                text=output['sentence_text']
            )
            db.session.add(sentence)
            db.session.commit()

            # Create segments and associate them with the sentence
            for segment in output['segments']:
                segment_entry = Segment(
                    sentence_id=sentence.id,
                    segment_index=segment['segment_id'],
                    segment_text=segment['segment_text'],
                    segment_type=segment.get('segment_type', ''),  
                    index_type=segment.get('index_type', ''),
                    status='pending'  # Default status
                )
                db.session.add(segment_entry)

            db.session.commit() 

            # Add the processed sentence result to the list
            processed_results.append({
                "sentence_id": sentence_id,
                "segments": output['segments'],
                "sentence_text": output['sentence_text'],
                "sentence_index": sentence_id
            })
            sentence_id += 1
        
        return processed_results

    @staticmethod
    def get_segment_details(segment_id):
        segment = Segment.query.filter_by(segment_id=segment_id).first()
        if not segment:
            return None
        
        # # Query to get the chapter_id through the sentence
        # sentence = Sentence.query.filter_by(id=segment.sentence_id).first()
        # if not sentence:
        #     return None

        # chapter = Chapter.query.filter_by(id=sentence.chapter_id).first()
        # if not chapter:
        #     return None

        lexico_conceptual = [
            lc.serialize() for lc in LexicalConceptual.query.filter_by(segment_id=segment_id).order_by(LexicalConceptual.lexical_conceptual_id).all()
        ]
        relational = [
            rel.serialize() for rel in Relational.query.filter_by(segment_id=segment_id).order_by(Relational.relational_id).all()
        ]
        discourse = [
            disc.serialize() for disc in Discourse.query.filter_by(segment_id=segment_id).order_by(Discourse.discourse_id).all()
        ]
        construction = [
            con.serialize() for con in Construction.query.filter_by(segment_id=segment_id).order_by(Construction.construction_id).all()
        ]
        # domain_term = [
        #     dt.serialize() for dt in DomainTerm.query.filter_by(segment_id=segment_id).order_by(DomainTerm.domain_term_id).all()
        # ]

        return {
            "segment_text": segment.segment_text,
            "english_text": segment.english_text,
            # "chapter_id": chapter.id, 
            "segment_type": segment.segment_type,
            "lexico_conceptual": lexico_conceptual,
            "status": segment.status,
            "relational": relational,
            "discourse": discourse,
            "construction": construction,
            # "domain_term": domain_term  
        }
        
    @staticmethod
    def get_previous_segment_details(segment_id):
        # Retrieve the current segment
        segment = Segment.query.filter_by(segment_id=segment_id).first()
        if not segment:
            return None
        
        # Get the previous segment by ordering based on segment_id or a logical field
        previous_segment = Segment.query.filter(Segment.segment_id < segment_id).order_by(Segment.segment_id.desc()).first()
        if not previous_segment:
            return None
        
        # Fetch related details for the previous segment
        lexico_conceptual = [
            lc.serialize() for lc in LexicalConceptual.query.filter_by(segment_id=previous_segment.segment_id).order_by(LexicalConceptual.lexical_conceptual_id).all()
        ]
        relational = [
            rel.serialize() for rel in Relational.query.filter_by(segment_id=previous_segment.segment_id).order_by(Relational.relational_id).all()
        ]
        discourse = [
            disc.serialize() for disc in Discourse.query.filter_by(segment_id=previous_segment.segment_id).order_by(Discourse.discourse_id).all()
        ]
        construction = [
            con.serialize() for con in Construction.query.filter_by(segment_id=previous_segment.segment_id).order_by(Construction.construction_id).all()
        ]
        
        # domain_term = [
        #     dt.serialize() for dt in DomainTerm.query.filter_by(segment_id=previous_segment.segment_id).order_by(DomainTerm.domain_term_id).all()
        # ]

        return {
            "segment_text": previous_segment.segment_text,
            "english_text": previous_segment.english_text,
            "segment_type": previous_segment.segment_type,
            "lexico_conceptual": lexico_conceptual,
            "status": previous_segment.status,
            "relational": relational,
            "discourse": discourse,
            "construction": construction,
            # "domain_term": domain_term
        }
    
    @staticmethod
    def get_segment_details_as_text(segment_id):
        segment = Segment.query.filter_by(segment_id=segment_id).first()
        if not segment:
            return None

        rows = []

        segment_type = segment.segment_type
        
        for lc in segment.lexical_concepts:
            main_index_relation = "-"
            head_index_relation = "-"
            cxn_index_component_type = "-"
            scope = "-"  # Adding the new "scope" column with "-" as the default value
            # domain_term = "-"
            concept = re.sub(r"\(.*?\)", "", lc.concept).strip()
            # Relational
            if lc.relational:
                for rel in lc.relational:
                    if rel.head_index == "-" or rel.dep_relation == "-":
                        main_index_relation = "-"
                    else:
                        main_index_relation = f"{rel.head_index}:{rel.dep_relation}"

            # Discourse
            if lc.discourse:
                for disc in lc.discourse:
                    if disc.head_index == "-" or disc.relation == "-":
                        head_index_relation = "-"
                    else:
                        head_index_relation = f"{disc.head_index}:{disc.relation}"

            # Construction
            if lc.constructions:
                for con in lc.constructions:
                    if con.cxn_index == "-" or con.component_type == "-":
                        cxn_index_component_type = "-"
                    else:
                        cxn_index_component_type = f"{con.cxn_index}:{con.component_type}"

            # if lc.domain_terms:
            #     for dt in lc.domain_terms:
            #         if dt.domain_term == "-":
            #             domain_term = "-"
            #         else:
            #             domain_term = f"{dt.domain_term}"

            rows.append([
                concept,                    # Concept
                lc.index,                      # Index
                lc.semantic_category,          # Semantic category
                lc.morpho_semantics,    # Morphological semantics
                main_index_relation,           # Relational: main_index:relation
                head_index_relation,           # Discourse: head_index:relation
                lc.speakers_view,              # Speaker's view
                scope,                         # Scope column
                cxn_index_component_type,      # Construction: cxn_index:component_type
                # domain term
            ])

        output = f"<segment_id={segment.segment_index}>\n"
        output += f"#{segment.segment_text}\n"
        output += "\n".join(["\t".join(map(str, row)) for row in rows])
        output += f"\n{segment_type}\n" 
        output += f"</segment_id>"
        return output

    @staticmethod
    def get_segment_details_as_csv(segment_id):
    # Query the main segment
        segment = Segment.query.filter_by(segment_id=segment_id).first()
        if not segment:
            return None

        # Query the previous five segments (if they exist)
        previous_segments = Segment.query.filter(Segment.segment_index < segment.segment_index).order_by(Segment.segment_index.desc()).limit(1).all()

        # Combine the previous segments and the current segment
        all_segments = previous_segments[::-1] + [segment]  # Reverse previous_segments to maintain ascending order

        output = ""

        for segment in all_segments:
            rows = []

            # Header for segment metadata
            segment_header = f"<sent_id={segment.segment_index}>\n#{segment.segment_text}\n"

            for lc in segment.lexical_concepts:
                # Initialize default values for each column
                main_index_relation = "-"
                head_index_relation = "-"
                cxn_index_component_type = "-"
                scope = "-"  # Adding the new "scope" column with "-" as the default value

                # Relational
                if lc.relational:
                    for rel in lc.relational:
                        main_index_relation = f"{rel.head_index}:{rel.dep_relation}" if rel.head_index != "-" and rel.dep_relation != "-" else "-"

                # Discourse
                if lc.discourse:
                    for disc in lc.discourse:
                        head_index_relation = f"{disc.head_index}:{disc.relation}" if disc.head_index != "-" and disc.relation != "-" else "-"

                # Construction
                if lc.constructions:
                    for con in lc.constructions:
                        cxn_index_component_type = f"{con.cxn_index}:{con.component_type}" if con.cxn_index != "-" and con.component_type != "-" else "-"

                # Append lexical concept details as a tab-separated row
                rows.append(
                    f"{lc.concept}\t{lc.index}\t{lc.semantic_category}\t{lc.morpho_semantics}\t"
                    f"{main_index_relation}\t{head_index_relation}\t{lc.speakers_view}\t{scope}\t"
                    f"{cxn_index_component_type}"
                )

            # Footer for segment type
            segment_footer = f"\n{segment.segment_type}\n</sent_id>"

            # Combine header, rows, and footer for this segment
            output += segment_header + "\n".join(rows) + segment_footer + "\n\n"

        return output

    
    @staticmethod
    def get_segment_details_as_csv_single(segment_id):
        segment = Segment.query.filter_by(segment_id=segment_id).first()
        if not segment:
            return None

        rows = []

        # Header for segment metadata
        segment_header = f"<sent_id={segment.segment_index}>\n#{segment.segment_text}\n"

        for lc in segment.lexical_concepts:
            # Initialize default values for each column
            main_index_relation = "-"
            head_index_relation = "-"
            cxn_index_component_type = "-"
            scope = "-"  # Adding the new "scope" column with "-" as the default value
            # domain_term = "-"

            # Relational
            if lc.relational:
                for rel in lc.relational:
                    main_index_relation = f"{rel.head_index}:{rel.dep_relation}" if rel.head_index != "-" and rel.dep_relation != "-" else "-"

            # Discourse
            if lc.discourse:
                for disc in lc.discourse:
                    head_index_relation = f"{disc.head_index}:{disc.relation}" if disc.head_index != "-" and disc.relation != "-" else "-"

            # Construction
            if lc.constructions:
                for con in lc.constructions:
                    cxn_index_component_type = f"{con.cxn_index}:{con.component_type}" if con.cxn_index != "-" and con.component_type != "-" else "-"

            # Domain terms
            # if lc.domain_terms:
            #     for dt in lc.domain_terms:
            #         domain_term = dt.domain_term if dt.domain_term != "-" else "-"

            # Append lexical concept details as a tab-separated row
            rows.append(
                f"{lc.concept}\t{lc.index}\t{lc.semantic_category}\t{lc.morpho_semantics}\t"
                f"{main_index_relation}\t{head_index_relation}\t{lc.speakers_view}\t{scope}\t"
                f"{cxn_index_component_type}"
            )

        # Footer for segment type
        segment_footer = f"\n{segment.segment_type}\n</sent_id>"

        # Combine header, rows, and footer
        output = segment_header + "\n".join(rows) + segment_footer
        return output
    
    
    @staticmethod
    def create_segment_details(data):
        segment_id = data.get('segment_id')

        segment = Segment.query.filter_by(segment_id=segment_id).first()

        if not segment:
            # If the segment doesn't exist, create a new one
            segment = Segment(
                segment_id=segment_id,
                segment_text=data.get('segment_text'),
                segment_type=data.get('segment_type'),
                status=data.get('status', 'pending')
            )
            db.session.add(segment)
            db.session.flush()  
        else:
            # If the segment exists, delete related data first
            segment.status = data.get('status', segment.status)
            Discourse.query.filter_by(segment_id=segment_id).delete()
            Construction.query.filter_by(segment_id=segment_id).delete()
            Relational.query.filter_by(segment_id=segment_id).delete()
            LexicalConceptual.query.filter_by(segment_id=segment_id).delete()
            # DomainTerm.query.filter_by(segment_id=segment_id).delete()  

        # Create new LexicalConceptual entries
        for lc_data in data.get('lexico_conceptual', []):
            lexical_concept = LexicalConceptual(
                segment_id=segment.segment_id,
                segment_index=lc_data['segment_index'],
                index=lc_data['index'],
                concept=lc_data['concept'],
                semantic_category=lc_data.get('semantic_category'),
                morpho_semantics=lc_data.get('morpho_semantics'),
                speakers_view=lc_data.get('speakers_view')
            )
            db.session.add(lexical_concept)
            db.session.flush()

            # Create related Relational entries
            for rel_data in lc_data.get('relational', []):
                relational = Relational(
                    segment_id=segment.segment_id,
                    segment_index=rel_data['segment_index'],
                    index=rel_data['index'],
                    head_relation=rel_data['head_relation'],
                    head_index=rel_data.get('head_index'),
                    dep_relation=rel_data.get('dep_relation'),
                    is_main=rel_data.get('is_main', False),
                    concept_id=lexical_concept.lexical_conceptual_id
                )
                db.session.add(relational)

            # Create related Construction entries
            for con_data in lc_data.get('construction', []):
                construction = Construction(
                    segment_id=segment.segment_id,
                    segment_index=con_data['segment_index'],
                    index=con_data['index'],
                    construction=con_data['construction'],
                    cxn_index=con_data['cxn_index'],
                    component_type=con_data['component_type'],
                    concept_id=lexical_concept.lexical_conceptual_id
                )
                db.session.add(construction)

            # Create related Discourse entries
            for disc_data in lc_data.get('discourse', []):
                discourse = Discourse(
                    segment_id=segment.segment_id,
                    segment_index=disc_data['segment_index'],
                    index=disc_data['index'],
                    head_index=disc_data.get('head_index'),
                    relation=disc_data.get('relation'),
                    concept_id=lexical_concept.lexical_conceptual_id,
                    discourse=disc_data['discourse']
                )
                db.session.add(discourse)

            # Create related DomainTerm entries
            # for domain_data in lc_data.get('domain_term', []):
            #     domain_term = DomainTerm(
            #         segment_id=segment.segment_id,
            #         segment_index=domain_data['segment_index'],
            #         index=domain_data['index'],
            #         domain_term=domain_data['domain_term'],
            #         concept_id=lexical_concept.lexical_conceptual_id  
            #     )
            #     db.session.add(domain_term)

        db.session.commit()
        return segment.segment_id
    
    @staticmethod
    def get_segment_details_as_dict(segment_id):
        segment = Segment.query.filter_by(segment_id=segment_id).first()
        if not segment:
            return None
        
        segment_details = {
            'segment_index': segment.segment_index,
            'segment_text': segment.segment_text,
            'lexical_concepts': []
        }
        
        # Process each lexical concept
        for lc in segment.lexical_concepts:
            lc_data = {
                'concept': lc.concept,
                'index': lc.index,
                'semantic_category': lc.semantic_category,
                'morpho_semantics': lc.morpho_semantics,
                'speakers_view': lc.speakers_view,
                'dependency': '-',
                'discourse': '-',
                'construction': '-',
                # 'domain_term': '-'
            }
            
            # Relational (Dependency)
            if lc.relational:
                for rel in lc.relational:
                    relation_value = f"{rel.head_index}:{rel.relation}"
                    lc_data['dependency'] = relation_value if relation_value != "-:-" else "-"

            # Discourse
            if lc.discourse:
                for disc in lc.discourse:
                    discourse_value = f"{disc.head_index}:{disc.relation}"
                    lc_data['discourse'] = discourse_value if discourse_value != "-:-" else "-"

            # Construction
            if lc.constructions:
                for con in lc.constructions:
                    construction_value = f"{con.cxn_index}:{con.component_type}"
                    lc_data['construction'] = construction_value if construction_value != "-:-" else "-"
                    
            # Domain Term 
            # if lc.domain_terms:
            #     for dt in lc.domain_terms:
            #         domain_term_value = dt.domain_term
            #         lc_data['domain_term'] = domain_term_value if domain_term_value else "-"
            
            # Append the lexical concept data to the segment details
            segment_details['lexical_concepts'].append(lc_data)
        
        return segment_details

    @staticmethod
    def generate_segment_details_xml(segment_details):
        # Create root element
        root = ET.Element("segment")
        
        segment_elem = ET.SubElement(root, "segment_info", {
            "index": segment_details['segment_index'],
            "text": segment_details['segment_text']
        })

        usr_data_elem = ET.SubElement(root, "usr_data")  

        for lc in segment_details['lexical_concepts']:
            lc_elem = ET.SubElement(usr_data_elem, "lexical_concept", {
                "concept": lc['concept'],
                "index": str(lc['index']),
                "semantic_category": lc['semantic_category'],
                "morpho_semantics": lc['morpho_semantics'],
                "speakers_view": lc['speakers_view']
            })

            # Add dependency, discourse, construction, and domain term details
            ET.SubElement(lc_elem, "dependency", {
                "value": lc.get('dependency', '-')
            })
            ET.SubElement(lc_elem, "discourse", {
                "value": lc.get('discourse', '-')
            })
            ET.SubElement(lc_elem, "construction", {
                "value": lc.get('construction', '-')
            })
            # ET.SubElement(lc_elem, "domain_term", {
            #     "value": lc.get('domain_term', '-')
            # })

        # Convert the entire tree to an XML string
        return ET.tostring(root, encoding='unicode', method='xml')
    


    @staticmethod
    def get_all_segments_for_chapter_as_text(chapter_id):
        sentences = Sentence.query.filter_by(chapter_id=chapter_id).all()
        if not sentences:
            return None

        output = ""
        
        for sentence in sentences:
            segments = Segment.query.filter_by(sentence_id=sentence.id).all()
            
            print(segments)
            
            for segment in segments:
                output += f"<segment_id={segment.segment_index}>\n"
                output += f"#{segment.segment_text}\n"
                rows = []
                segment_type = segment.segment_type
                for lc in segment.lexical_concepts:
                    main_index_relation = "-"
                    head_index_relation = "-"
                    cxn_index_component_type = "-"
                    scope = "-"
                    # domain_term = "-"

                    # Remove any text inside parentheses in the concept
                    concept = re.sub(r"\(.*?\)", "", lc.concept).strip()

                    # Relational
                    if lc.relational:
                        for rel in lc.relational:
                            head_index = rel.head_index if rel.head_index != "-" else ""
                            relation = rel.relation if rel.relation != "-" else ""
                            
                            # Replace with "-" if either part is missing
                            if not head_index or not relation:
                                main_index_relation = "-"
                            else:
                                main_index_relation = f"{head_index}:{relation}"

                    # Discourse
                    if lc.discourse:
                        for disc in lc.discourse:
                            head_index = disc.head_index if disc.head_index != "-" else ""
                            relation = disc.relation if disc.relation != "-" else ""

                            # Replace with "-" if either part is missing
                            if not head_index or not relation:
                                head_index_relation = "-"
                            else:
                                head_index_relation = f"{head_index}:{relation}"

                    # Construction
                    if lc.constructions:
                        for con in lc.constructions:
                            cxn_index = con.cxn_index if con.cxn_index != "-" else ""
                            component_type = con.component_type if con.component_type != "-" else ""

                            # Replace with "-" if either part is missing
                            if not cxn_index or not component_type:
                                cxn_index_component_type = "-"
                            else:
                                cxn_index_component_type = f"{cxn_index}:{component_type}"

                    # if lc.domain_terms:
                    #     for dt in lc.domain_terms:
                    #         domain_term = f"{dt.domain_term}" if dt.domain_term != "-" else "-"

                    rows.append([
                        concept,                      # Concept without text inside parentheses
                        lc.index,                      # Index
                        lc.semantic_category,          # Semantic category
                        lc.morpho_semantics,    # Morphological semantics
                        main_index_relation,           # Relational: main_index:relation
                        head_index_relation,           # Discourse: head_index:relation
                        lc.speakers_view,              # Speaker's view
                        scope,                         # Scope column
                        cxn_index_component_type,      # Construction: cxn_index:component_type
                    ])
                
                output += "\n".join(["\t".join(map(str, row)) for row in rows])
                output += f"\n{segment_type}\n" 
                output += f"\n</segment_id>\n"
        
        return output
    
    
    
    
    @staticmethod
    def get_segment_id_by_index(segment_index):
        result = db.session.execute(
            text("SELECT segment_id FROM segments WHERE segment_index = :segment_index LIMIT 1"),
            {"segment_index": segment_index}
        ).fetchone()
        
        return result[0] if result else None    


    
    


