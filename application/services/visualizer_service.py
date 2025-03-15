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
                                    "op1", "op2", "op3", "op4", "op5", "op7", "op8",
                                    "start", "end", "mod", "head", "count", "unit",
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
                                    "op1", "op2", "op3", "op4", "op5", "op7", "op8",
                                    "start", "end", "mod", "head", "count", "unit",
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