from flask import Flask, request, jsonify, send_file, Response
from graphviz import Digraph
import re
import requests
import os

class VisualizerService:
    
    @staticmethod
    def process_usr_data(usrs_text):
        def parse_inter_relations(data, source_token, source_sentence, sentences):
            inter_relations = []
            if not data or data == "-":
                return inter_relations
                
            for relation in data.split("|"):
                if ":" not in relation:
                    continue
                    
                target_sentence_id, relation_type = relation.split(":")
                
                # Parse target information
                if target_sentence_id.isdigit():
                    target_sentence = source_sentence
                    target_token = target_sentence_id
                elif '.' in target_sentence_id:
                    target_sentence, target_token = target_sentence_id.split(".")
                else:
                    target_sentence, target_token = target_sentence_id, None
                
                # Find target word
                target_sentence_found = None
                target_word = None
                
                if target_sentence == source_sentence:
                    target_sentence_found = source_sentence
                    if target_token and sentences.get(source_sentence):
                        for token in sentences[source_sentence].get("tokens", []):
                            if str(token["id"]) == str(target_token):
                                target_word = token["word"]
                                break
                else:
                    for sentence_id in sentences:
                        if str(target_sentence) in str(sentence_id):
                            target_sentence_found = sentence_id
                            if target_token and sentences.get(sentence_id):
                                for token in sentences[sentence_id].get("tokens", []):
                                    if str(token["id"]) == str(target_token):
                                        target_word = token["word"]
                                        break
                            break
                
                inter_relations.append({
                    "source_token": source_token,
                    "target_token": target_token,
                    "target_word": target_word,
                    "source_sentence": source_sentence,
                    "target_sentence": target_sentence_found if target_sentence_found else target_sentence,
                    "relation": relation_type
                })
            
            return inter_relations

        def create_json(tokens, main_token_info, inter_relations):
            # Create mappings
            index_to_word = {str(token["id"]): token["word"] for token in tokens}
            index_to_token = {str(token["id"]): token for token in tokens}
            
            updated_tokens = []
            for token in tokens:
                updated_relations = []
                for relation in token.get("relations", []):
                    target_index = str(relation["target"])
                    if target_index in index_to_word:
                        updated_relations.append({
                            "target": index_to_word[target_index],
                            "target_id": target_index,
                            "label": relation["label"]
                        })
                updated_tokens.append({
                    "id": str(token["id"]),
                    "word": token["word"],
                    "relations": updated_relations,
                    "info": token.get("info", {})
                })
            
            # Handle main token
            main_token_combined = None
            if main_token_info:
                main_token_word, main_token_id = main_token_info
                main_token_combined = f"{main_token_word}_{main_token_id}"
            
            return {
                "tokens": updated_tokens,
                "main": main_token_combined,
                "inter_relations": inter_relations
            }
            
        sentences = {}
        current_sentence_id = None
        current_tokens = []
        main_token_info = None
        inter_relations = []

        for line in usrs_text.strip().splitlines():
            line = line.strip()
            
            # Handle sentence ID
            if line.startswith("<sent_id="):
                if current_sentence_id:
                    sentences[current_sentence_id] = create_json(current_tokens, main_token_info, inter_relations)
                current_sentence_id = re.search(r"<sent_id=\s*(\S+)>", line).group(1)
                current_tokens = []
                main_token_info = None
                inter_relations = []
                continue
            
            # Skip empty lines or comments
            if not line or line.startswith(("#", "<", "%")) or len(line.split("\t")) == 1:
                continue
            
            # Process token line
            line = re.sub(r'\s+', '\t', line).strip()
            token_data = line.split("\t")
            
            word = token_data[0]
            token_id = token_data[1]
            
            # Create token info
            info = {
                "semantic_category": token_data[2] if len(token_data) > 2 else "-",
                "morpho_semantic": token_data[3] if len(token_data) > 3 else "-",
                "speakers_view": token_data[6] if len(token_data) > 6 else "-",
                "additional_info": token_data[5] if len(token_data) > 5 else "-"
            }
            
            # Handle relations
            relations = []
            dependency_info = token_data[4] if len(token_data) > 4 else "-"
            construction_info = token_data[8] if len(token_data) > 8 else "-"
        
            # Check through the token's dependency info
            if dependency_info:
                # First, check for "0:main" in the dependency info
                if "0:main" in dependency_info:
                    # If found, assign this token as the main token and skip checking for "rc" relation
                    main_token_info = (word, token_id)
                
                # If "0:main" isn't found, only then check for "rc"
                elif not main_token_info and any(dep.split(":")[1].startswith("rc") for dep in dependency_info.split("|") if ":" in dep):
                    # If no main token is found yet, consider the first "rc" relation as the main token
                    main_token_info = (word, token_id)

            print(main_token_info);

            
            # Process dependency relations
            if dependency_info and dependency_info != "-":
                for dep in dependency_info.split("|"):
                    if ":" in dep:
                        target, label = dep.split(":")
                        relations.append({"target": target, "label": label})
            
            # Process construction relations
            if construction_info and construction_info != "-":
                for dep in construction_info.split("|"):
                    if ":" in dep:
                        target, label = dep.split(":")
                        relations.append({"target": target, "label": label})
            
            current_tokens.append({
                "id": token_id,
                "word": word,
                "relations": relations,
                "info": info
            })
            
            # Process inter-relations
            if info["additional_info"] != "-":
                inter_relations.extend(
                    parse_inter_relations(
                        info["additional_info"],
                        token_id,
                        current_sentence_id,
                        sentences
                    )
                )
        
        # Process final sentence
        if current_sentence_id:
            sentences[current_sentence_id] = create_json(current_tokens, main_token_info, inter_relations)
        
        # Create visualization
        dot = Digraph(comment='USR Representation')
        dot.attr(node='*', width='1.5', height='1.75', fontsize='6')
        
        for sent_id, sentence in sentences.items():
            sent_node = f'sent_{sent_id}'
            dot.node(sent_node, f'Sentence {sent_id}', shape='ellipse', color='blue', fillcolor='lightblue', style='filled')
            
            if sentence['main']:
                dot.node(sentence['main'], label=sentence['main'], shape='ellipse', fillcolor='lightgray')
                dot.edge(sent_node, sentence['main'], label='main', fontsize='8')
            
            # Handle tokens and relations
            special_construction_clusters = {}
            
            for token in sentence['tokens']:
                token_node = f'{token["word"]}_{token["id"]}'
                label = f"{token['word']}:{token['id']}"
                tooltip_info = (
                    f"semCat: {token['info']['semantic_category']}\n"
                    f"morphSem: {token['info']['morpho_semantic']}\n"
                    f"speakersView: {token['info']['speakers_view']}\n"
                    f"Additional Info: {token['info']['additional_info']}"
                )
                
                if '[' in token['word'] and ']' in token['word']:
                    special_construction_clusters[token_node] = {
                        "concept": label,
                        "connected_nodes": set()
                    }
                    dot.node(token_node, label=label, shape='box', tooltip=tooltip_info)
                else:
                    dot.node(token_node, label=label, tooltip=tooltip_info)
            
            # Add edges
            for token in sentence['tokens']:
                token_node = f'{token["word"]}_{token["id"]}'
                for relation in token['relations']:
                    if 'target' in relation and 'target_id' in relation:
                        target_node = f'{relation["target"]}_{relation["target_id"]}'
                        dot.edge(target_node, token_node, label=relation['label'], fontcolor="blue")
                        
                        if '[' in target_node and ']' in target_node:
                            if target_node in special_construction_clusters:
                                if relation['label'] in {
                                    "op1", "op2", "op3", "op4", "op5", "op7", "op8","op9","op10",
                                    "start", "end", "mod", "head", "count", "unit","begin",
                                    "component1", "component2", "component3", "component4",
                                    "component5", "component6", "unit_value", "unit_every",
                                    "whole", "part", "kriyAmUla", "verbalizer"
                                }:
                                    special_construction_clusters[target_node]["connected_nodes"].add(token_node)
            
            # Create construction clusters
            for cluster_token, cluster_data in special_construction_clusters.items():
                with dot.subgraph(name=f'cluster_{cluster_token}') as cluster:
                    cluster.attr(
                        style='filled,dashed',
                        color='black',
                        fillcolor='lightgray',
                        label=f'Construction: {cluster_data["concept"]}'
                    )
                    cluster.node(cluster_token, label=cluster_data["concept"], shape='box')
                    for node in cluster_data["connected_nodes"]:
                        cluster.node(node)
                        
            for inter_rel in sentence.get("inter_relations", []):
                source_token = inter_rel["source_token"]
                target_token = inter_rel["target_token"]
                source_sentence = inter_rel["source_sentence"]
                target_sentence = inter_rel["target_sentence"]
                relation = inter_rel["relation"]
                
                # Find the actual nodes by matching token IDs with words
                source_node = None
                target_node = None
                
                for token in sentences.get(source_sentence, {}).get("tokens", []):
                    if str(token["id"]) == str(source_token):
                        source_node = f'{token["word"]}_{token["id"]}'
                        break

                for token in sentences.get(target_sentence, {}).get("tokens", []):
                    if str(token["id"]) == str(target_token):
                        target_node = f'{token["word"]}_{token["id"]}'
                        break
                
                # If both nodes exist, create the edge
                if source_node and target_node:
                    dot.edge(source_node, target_node, label=relation, color="red", style="dashed")

        
        return sentences, dot
        



    @staticmethod
    def process_usr_data_multiple(usrs_text):
        # Modified inter-relations logic in parse_inter_relations function
        def parse_inter_relations(data, source_token, source_sentence, sentences):
            inter_relations = []
            if not data or data == "-":
                return inter_relations
                
            for relation in data.split("|"):
                if ":" not in relation:
                    continue
                    
                target_sentence_id, relation_type = relation.split(":")
                
                # Skip if this is a coref relation
                if relation_type.strip().lower() == "coref":
                    continue
                    
                # Parse target information
                if target_sentence_id.isdigit():
                    target_sentence = source_sentence
                    target_token = target_sentence_id
                elif '.' in target_sentence_id:
                    target_sentence, target_token = target_sentence_id.split(".")
                else:
                    target_sentence, target_token = target_sentence_id, None
                
                # Find target word
                target_sentence_found = None
                target_word = None
                
                if target_sentence == source_sentence:
                    target_sentence_found = source_sentence
                    if target_token and sentences.get(source_sentence):
                        for token in sentences[source_sentence].get("tokens", []):
                            if str(token["id"]) == str(target_token):
                                target_word = token["word"]
                                break
                else:
                    for sentence_id in sentences:
                        if str(target_sentence) in str(sentence_id):
                            target_sentence_found = sentence_id
                            if target_token and sentences.get(sentence_id):
                                for token in sentences[sentence_id].get("tokens", []):
                                    if str(token["id"]) == str(target_token):
                                        target_word = token["word"]
                                        break
                            break
                
                inter_relations.append({
                    "source_token": source_token,
                    "target_token": target_token,
                    "target_word": target_word,
                    "source_sentence": source_sentence,
                    "target_sentence": target_sentence_found if target_sentence_found else target_sentence,
                    "relation": relation_type
                })
            
            print(inter_relations)
            return inter_relations

        def create_json(tokens, main_token_info, inter_relations):
            # Create mappings
            index_to_word = {str(token["id"]): token["word"] for token in tokens}
            index_to_token = {str(token["id"]): token for token in tokens}
            
            updated_tokens = []
            for token in tokens:
                updated_relations = []
                for relation in token.get("relations", []):
                    target_index = str(relation["target"])
                    if target_index in index_to_word:
                        updated_relations.append({
                            "target": index_to_word[target_index],
                            "target_id": target_index,
                            "label": relation["label"]
                        })
                updated_tokens.append({
                    "id": str(token["id"]),
                    "word": token["word"],
                    "relations": updated_relations,
                    "info": token.get("info", {})
                })
            
            # Handle main token
            main_token_combined = None
            if main_token_info:
                main_token_word, main_token_id = main_token_info
                main_token_combined = f"{main_token_word}_{main_token_id}"
            
            return {
                "tokens": updated_tokens,
                "main": main_token_combined,
                "inter_relations": inter_relations
            }
            
        sentences = {}
        current_sentence_id = None
        current_tokens = []
        main_token_info = None
        inter_relations = []

        for line in usrs_text.strip().splitlines():
            line = line.strip()
            
            # Handle sentence ID
            if line.startswith("<sent_id="):
                if current_sentence_id:
                    sentences[current_sentence_id] = create_json(current_tokens, main_token_info, inter_relations)
                current_sentence_id = re.search(r"<sent_id=\s*(\S+)>", line).group(1)
                current_tokens = []
                main_token_info = None
                inter_relations = []
                continue
            
            # Skip empty lines or comments
            if not line or line.startswith(("#", "<", "%")) or len(line.split("\t")) == 1:
                continue
            
            # Process token line
            line = re.sub(r'\s+', '\t', line).strip()
            token_data = line.split("\t")
            
            word = token_data[0]
            token_id = token_data[1]
            
            # Create token info
            info = {
                "semantic_category": token_data[2] if len(token_data) > 2 else "-",
                "morpho_semantic": token_data[3] if len(token_data) > 3 else "-",
                "speakers_view": token_data[6] if len(token_data) > 6 else "-",
                "additional_info": token_data[5] if len(token_data) > 5 else "-"
            }
            
            # Handle relations
            relations = []
            dependency_info = token_data[4] if len(token_data) > 4 else "-"
            construction_info = token_data[8] if len(token_data) > 8 else "-"
            
           

            # Check through the token's dependency info
            if dependency_info:
                # First, check for "0:main" in the dependency info
                if "0:main" in dependency_info:
                    # If found, assign this token as the main token and skip checking for "rc" relation
                    main_token_info = (word, token_id)
                
                # If "0:main" isn't found, only then check for "rc"
                elif not main_token_info and any(dep.split(":")[1].startswith("rc") for dep in dependency_info.split("|") if ":" in dep):
                    # If no main token is found yet, consider the first "rc" relation as the main token
                    main_token_info = (word, token_id)



            
            # Process dependency relations
            if dependency_info and dependency_info != "-":
                for dep in dependency_info.split("|"):
                    if ":" in dep:
                        target, label = dep.split(":")
                        relations.append({"target": target, "label": label})
            
            # Process construction relations
            if construction_info and construction_info != "-":
                for dep in construction_info.split("|"):
                    if ":" in dep:
                        target, label = dep.split(":")
                        relations.append({"target": target, "label": label})
            
            current_tokens.append({
                "id": token_id,
                "word": word,
                "relations": relations,
                "info": info
            })
            
            # Process inter-relations
            if info["additional_info"] != "-":
                inter_relations.extend(
                    parse_inter_relations(
                        info["additional_info"],
                        token_id,
                        current_sentence_id,
                        sentences
                    )
                )
        
        # Process final sentence
        if current_sentence_id:
            sentences[current_sentence_id] = create_json(current_tokens, main_token_info, inter_relations)
        
        # Create visualization
        dot = Digraph(comment='USR Representation')
        dot.attr(node='*', width='1.5', height='1.75', fontsize='6')
        
        for sent_id, sentence in sentences.items():
            sent_node = f'sent_{sent_id}'
            dot.node(sent_node, f'Sentence {sent_id}', shape='ellipse', color='blue', fillcolor='lightblue', style='filled')

            if sentence['main']:
                main_token = sentence['main']
                # Ensure main token is uniquely identified by including sentence ID
                main_token_node = f'{main_token}_{sent_id}'  # Unique by including sentence ID
                dot.node(main_token_node, label=main_token, shape='ellipse', fillcolor='lightgray')
                dot.edge(sent_node, main_token_node, label='main', fontsize='8')

            # Handle tokens and relations
            special_construction_clusters = {}

            for token in sentence['tokens']:
                # Use sentence ID in the token node to ensure uniqueness across sentences
                token_node = f'{token["word"]}_{token["id"]}_{sent_id}'  # Unique by including sentence ID
                label = f"{token['word']}:{token['id']}"
                tooltip_info = (
                    f"semCat: {token['info']['semantic_category']}\n"
                    f"morphSem: {token['info']['morpho_semantic']}\n"
                    f"speakersView: {token['info']['speakers_view']}\n"
                    f"Additional Info: {token['info']['additional_info']}"
                )

                if '[' in token['word'] and ']' in token['word']:
                    special_construction_clusters[token_node] = {
                        "concept": label,
                        "connected_nodes": set()
                    }
                    dot.node(token_node, label=label, shape='box', tooltip=tooltip_info)
                else:
                    dot.node(token_node, label=label, tooltip=tooltip_info)

            # Add edges for token relations
            for token in sentence['tokens']:
                token_node = f'{token["word"]}_{token["id"]}_{sent_id}'
                for relation in token['relations']:
                    if 'target' in relation and 'target_id' in relation:
                        target_node = f'{relation["target"]}_{relation["target_id"]}_{sent_id}'
                        dot.edge(target_node, token_node, label=relation['label'], fontcolor="blue")

                        if '[' in target_node and ']' in target_node:
                            if target_node in special_construction_clusters:
                                if relation['label'] in {
                                    "op1", "op2", "op3", "op4", "op5", "op7", "op8", "op9", "op10",
                                    "start", "end", "mod", "head", "count", "unit", "begin","inside",
                                    "component1", "component2", "component3", "component4",
                                    "component5", "component6", "unit_value", "unit_every",
                                    "whole", "part", "kriyAmUla", "verbalizer"
                                }:
                                    special_construction_clusters[target_node]["connected_nodes"].add(token_node)
            
          
            # Handle inter-relations between tokens in different sentences
            for inter_rel in sentence.get("inter_relations", []):
                if inter_rel["relation"].strip().lower() == "coref":
                    continue

                source_token = inter_rel["source_token"]
                target_token = inter_rel["target_token"]
                source_sentence = inter_rel["source_sentence"]
                target_sentence = inter_rel["target_sentence"]
                relation = inter_rel["relation"]

                # Find the actual nodes by matching token IDs with words
                source_node = None
                target_node = None

                for token in sentences.get(source_sentence, {}).get("tokens", []):
                    if str(token["id"]) == str(source_token):
                        source_node = f'{token["word"]}_{token["id"]}_{source_sentence}'
                        break

                for token in sentences.get(target_sentence, {}).get("tokens", []):
                    if str(token["id"]) == str(target_token):
                        target_node = f'{token["word"]}_{token["id"]}_{target_sentence}'
                        break

                # If both nodes exist, create the edge
                if source_node and target_node:
                    dot.edge(source_node, target_node, label=relation, color="red", style="dashed")

            
            # Create construction clusters
            for cluster_token, cluster_data in special_construction_clusters.items():
                with dot.subgraph(name=f'cluster_{cluster_token}') as cluster:
                    cluster.attr(
                        style='filled,dashed',
                        color='black',
                        fillcolor='lightgray',
                        label=f'Construction: {cluster_data["concept"]}'
                    )
                    cluster.node(cluster_token, label=cluster_data["concept"], shape='box')
                    for node in cluster_data["connected_nodes"]:
                        cluster.node(node)
            


        return sentences, dot
    
    
    

    # @staticmethod
    @staticmethod
    def process_usr_data_coref(usrs_text):
        """Process USR data and generate styled dependency tree visualization with coreference links."""
        from graphviz import Digraph
        import re

        def get_node_id(sent_id, word, token_id):
            return f'{sent_id}__{word}_{token_id}'

        def parse_inter_relations(data, source_token, source_sentence, segment_lookup=None):
            inter_relations = []
            if not data or data == "-":
                return inter_relations

            for relation in data.split("|"):
                if ":" not in relation:
                    continue
                    
                target_ref, relation_type = relation.split(":")
                relation_type = relation_type.strip().lower()
                
                if relation_type != "coref":
                    continue

                # Parse target reference
                if '.' in target_ref:
                    if target_ref[0].isdigit():
                        # Format: "token.sent" (e.g., "4.2")
                        target_sentence = source_sentence
                        target_token = target_ref.split('.')[1]
                    else:
                        # Format: "segment_id.token" (e.g., "Geo_ncert_7stnd_1ch_0003.4")
                        parts = target_ref.split('.')
                        target_sentence = parts[0]
                        target_token = parts[1] if len(parts) > 1 else None
                elif target_ref.isdigit():
                    # Format: "token" (current sentence)
                    target_sentence = source_sentence
                    target_token = target_ref
                else:
                    # Format: "segment_id" (whole segment)
                    target_sentence = target_ref
                    target_token = None

                # Try to resolve the target segment
                resolved_target = None
                if segment_lookup:
                    # First try exact match
                    if target_sentence in segment_lookup:
                        resolved_target = target_sentence
                    else:
                        # Try partial matches (for cases like "0003" vs "0003a")
                        # 1. Try matching base segment ID (without suffix)
                        base_segment = re.sub(r'[a-z]$', '', target_sentence)
                        if base_segment in segment_lookup:
                            resolved_target = base_segment
                        else:
                            # 2. Try matching any segment that contains the target as prefix
                            for seg_id in segment_lookup:
                                if seg_id.startswith(target_sentence):
                                    resolved_target = seg_id
                                    break

                inter_relations.append({
                    "source_token": source_token,
                    "target_token": target_token,
                    "source_sentence": source_sentence,
                    "target_sentence": resolved_target if resolved_target else target_sentence,
                    "relation": relation_type,
                    # These will be filled in later
                    "source_word": None,
                    "target_word": None,
                    "original_reference": target_ref  # Keep original for debugging
                })
            
            return inter_relations

        def create_json(tokens, main_token_info, inter_relations):
            index_to_word = {str(token["id"]): token["word"] for token in tokens}
            updated_tokens = []

            for token in tokens:
                updated_relations = []
                for relation in token.get("relations", []):
                    target_index = str(relation["target"])
                    if target_index in index_to_word:
                        updated_relations.append({
                            "target": index_to_word[target_index],
                            "target_id": target_index,
                            "label": relation["label"]
                        })

                updated_tokens.append({
                    "id": str(token["id"]),
                    "word": token["word"],
                    "relations": updated_relations,
                    "info": token.get("info", {})
                })

            main_token_combined = None
            if main_token_info:
                main_token_word, main_token_id = main_token_info
                main_token_combined = f"{main_token_word}_{main_token_id}"

            return {
                "tokens": updated_tokens,
                "main": main_token_combined,
                "inter_relations": inter_relations
            }

        # --- Parse USR text (First Pass) ---
        sentences = {}
        current_sentence_id = None
        current_tokens = []
        main_token_info = None
        inter_relations_buffer = []

        for line in usrs_text.strip().splitlines():
            line = line.strip()

            if line.startswith("<sent_id="):
                if current_sentence_id:
                    sentences[current_sentence_id] = create_json(
                        current_tokens, main_token_info, inter_relations_buffer)

                current_sentence_id = re.search(r"<sent_id=\s*(\S+)>", line).group(1)
                current_tokens = []
                main_token_info = None
                inter_relations_buffer = []
                continue

            if not line or line.startswith(("#", "<", "%")) or len(line.split("\t")) == 1:
                continue

            line = re.sub(r'\s+', '\t', line).strip()
            token_data = line.split("\t")

            word = token_data[0]
            token_id = token_data[1]

            info = {
                "semantic_category": token_data[2] if len(token_data) > 2 else "-",
                "morpho_semantic": token_data[3] if len(token_data) > 3 else "-",
                "speakers_view": token_data[6] if len(token_data) > 6 else "-",
                "additional_info": token_data[5] if len(token_data) > 5 else "-"
            }

            relations = []
            dependency_info = token_data[4] if len(token_data) > 4 else "-"
            construction_info = token_data[8] if len(token_data) > 8 else "-"

            if dependency_info:
                if "0:main" in dependency_info:
                    main_token_info = (word, token_id)
                elif not main_token_info and any(
                    dep.split(":")[1].startswith("rc")
                    for dep in dependency_info.split("|")
                    if ":" in dep
                ):
                    main_token_info = (word, token_id)

            if dependency_info and dependency_info != "-":
                for dep in dependency_info.split("|"):
                    if ":" in dep:
                        target, label = dep.split(":")
                        relations.append({"target": target, "label": label})

            if construction_info and construction_info != "-":
                for dep in construction_info.split("|"):
                    if ":" in dep:
                        target, label = dep.split(":")
                        relations.append({"target": target, "label": label})

            current_tokens.append({
                "id": token_id,
                "word": word,
                "relations": relations,
                "info": info
            })

            if info["additional_info"] != "-":
                inter_relations_buffer.extend(
                    parse_inter_relations(
                        info["additional_info"],
                        token_id,
                        current_sentence_id
                    )
                )

        if current_sentence_id:
            sentences[current_sentence_id] = create_json(
                current_tokens, main_token_info, inter_relations_buffer)

        # --- Second Pass: Resolve source and target words ---
        for sent_id, sent_data in sentences.items():
            for inter_rel in sent_data.get("inter_relations", []):
                source_word = next(
                    (tok["word"] for tok in sent_data["tokens"] if str(tok["id"]) == str(inter_rel["source_token"])),
                    inter_rel["source_token"]
                )
                inter_rel["source_word"] = source_word

                resolved_sentence_id = None
                for s_id in sentences.keys():
                    if str(inter_rel["target_sentence"]) == str(s_id) or \
                    str(inter_rel["target_sentence"]) == str(s_id).replace('Sentence', ''):
                        resolved_sentence_id = s_id
                        break

                if resolved_sentence_id:
                    target_tokens = sentences.get(resolved_sentence_id, {}).get("tokens", [])
                    word = next((t["word"] for t in target_tokens if str(t["id"]) == str(inter_rel["target_token"])), None)
                    inter_rel["target_word"] = word
                    inter_rel["target_sentence"] = resolved_sentence_id

        # --- Build Styled GraphViz Tree ---
        dot = Digraph(comment='USR Coreference Tree')
        dot.attr(rankdir='TB', splines='polyline', nodesep='0.6', ranksep='0.7')
        dot.attr(size='20,30')
        dot.attr('node', fontsize='12', width='1.5', height='1.0')
        dot.attr('edge', fontsize='10')

        construction_rel_labels = {
            "op1", "op2", "op3", "op4", "op5", "op7", "op8", "op9", "op10",
            "start", "end", "mod", "head", "count", "unit", "begin", "inside",
            "component1", "component2", "component3", "component4",
            "component5", "component6", "unit_value", "unit_every",
            "whole", "part", "kriyAmUla", "verbalizer"
        }

        sent_order = sorted(sentences.keys())
        for sent_id in sent_order:
            sentence = sentences[sent_id]
            with dot.subgraph(name=f'cluster_{sent_id}') as cluster:
                cluster.attr(style='filled,rounded', color='#d3bff7', fillcolor='#f3e9ff',
                            label=f'Sentence {sent_id}')

                token_nodes = {}

                # Sentence header
                sent_node = f'sent_{sent_id}'
                cluster.node(sent_node, f'Sentence {sent_id}', shape='ellipse',
                            style='filled', fillcolor='lightblue', fontsize='14')

                # Main token
                if sentence['main']:
                    parts = sentence['main'].rsplit('_', 1)
                    if len(parts) == 2:
                        main_word, main_id = parts
                    else:
                        main_word = sentence['main']
                        main_id = "0"
                    main_node = get_node_id(sent_id, main_word, main_id)
                    cluster.node(main_node, f"{main_word}:{main_id}",
                                shape='ellipse', style='filled', fillcolor='white')
                    cluster.edge(sent_node, main_node, label='main', style='dashed', color='gray')
                    token_nodes[main_id] = main_node

                # --- Identify construction concept groups ---
                construction_groups = {}
                for token in sentence['tokens']:
                    word = token['word']
                    token_id = token['id']
                    if '[' in word and ']' in word:
                        group = {token_id}
                        for other_token in sentence['tokens']:
                            for relation in other_token['relations']:
                                if relation['label'] in construction_rel_labels and str(relation['target']) == str(token_id):
                                    group.add(other_token['id'])
                        construction_groups[token_id] = group

                # Draw construction concept groups inside gray boxes
                boxed_tokens = set()
                for con_id, group_ids in construction_groups.items():
                    with cluster.subgraph(name=f"cluster_{sent_id}_con_{con_id}") as con_box:
                        con_box.attr(style='filled,rounded', color='gray', fillcolor='#f0f0f0', label=f'Construction [{con_id}]')
                        for tok_id in sorted(group_ids, key=int):
                            token = next(t for t in sentence['tokens'] if t['id'] == tok_id)
                            token_node = get_node_id(sent_id, token["word"], token["id"])
                            fill = 'lightgrey' if '[' in token["word"] and ']' in token["word"] else 'white'
                            shape = 'box' if '[' in token["word"] and ']' in token["word"] else 'oval'
                            con_box.node(token_node, f"{token['word']}:{token['id']}", shape=shape,
                                        style='filled', fillcolor=fill)
                            token_nodes[token["id"]] = token_node
                            boxed_tokens.add(token["id"])

                # Draw all remaining tokens outside gray boxes
                for token in sorted(sentence['tokens'], key=lambda x: int(x['id'])):
                    if token['id'] in boxed_tokens:
                        continue
                    token_node = get_node_id(sent_id, token["word"], token["id"])
                    fill = 'lightgrey' if '[' in token["word"] and ']' in token["word"] else 'white'
                    shape = 'box' if '[' in token["word"] and ']' in token["word"] else 'oval'
                    cluster.node(token_node, f"{token['word']}:{token['id']}",
                                shape=shape, style='filled', fillcolor=fill)
                    token_nodes[token["id"]] = token_node

                # Draw dependency edges
                for token in sentence['tokens']:
                    child_node = token_nodes[token["id"]]
                    for relation in token["relations"]:
                        parent_id = relation.get("target_id", relation["target"])
                        if parent_id in token_nodes:
                            parent_node = token_nodes[parent_id]
                            cluster.edge(parent_node, child_node,
                                        label=relation['label'], color='blue',
                                        fontcolor='blue', fontsize='10')

        # Draw coreference links (cross-sentence in red)
        for sent_id in sent_order:
            sentence = sentences[sent_id]
            for inter_rel in sentence.get("inter_relations", []):
                if inter_rel["relation"].lower() != "coref":
                    continue
                if not inter_rel["target_word"]:
                    continue
                source_node = get_node_id(inter_rel["source_sentence"],
                                        inter_rel["source_word"],
                                        inter_rel["source_token"])
                target_node = get_node_id(inter_rel["target_sentence"],
                                        inter_rel["target_word"],
                                        inter_rel["target_token"])
                dot.edge(source_node, target_node,
                        label="coref", color="red",
                        style="bold", arrowhead="vee",
                        fontcolor="red", fontsize='10', constraint='false')

        return sentences, dot
