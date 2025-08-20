from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.models.tam_dictionary_model import TAM_Dictionary
from application.extensions import db
from application.models.assignment_model import Assignment
from application.models.chapter_model import Chapter
from application.services.concept_service import ConceptService
from application.services.lexical_service import LexicalService
from application.services.user_service import UserService
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from application.models.concept_submissions import ConceptSubmission
from application.models.user_model import User
from application.models.concept_dictionary_model import ConceptDictionary
from flask import jsonify, request
from sqlalchemy.orm import sessionmaker
from application.services.measure_time import measure_response_time
from application.models.segment_model import Segment


concept_blueprint = Blueprint('concepts', __name__)


@concept_blueprint.route('/getconcepts/<string:hindi_label>', methods=['GET'])
def get_concepts_by_hindi(hindi_label):
    # Fetch concepts by hindi_label
    concepts = ConceptService.get_concepts_by_hindi_label(hindi_label)
    if concepts:
        filtered_concepts = {concept.hindi_label: {
                                  "english_label": concept.english_label,
                                  "concept_id": concept.concept_id,
                                  "hindi_label":concept.hindi_label,
                                  "sanskrit_label":concept.sanskrit_label,
                                  "concept_label":concept.concept_label 
                              } 
                             for concept in concepts 
                             if concept.hindi_label == hindi_label or concept.hindi_label.startswith(f"{hindi_label}_")}
        
        if filtered_concepts:
            return jsonify({"concepts": filtered_concepts, "option": "list_found"}), 200

    # Option when no concepts are found
    return jsonify({"message": "No concepts found for the given hindi_label", "option": "other"}), 404

@concept_blueprint.route('/get_sanskrit_concepts/sanskrit/<string:sanskrit_label>', methods=['GET'])
@measure_response_time
def get_concepts_by_Sanskrit_label(sanskrit_label):
    # Fetch concepts by hindi_label
    concepts = ConceptService.get_concepts_by_sanskrit_label(sanskrit_label)
    if concepts:
        filtered_concepts = {concept.sanskrit_label: {
                                  "english_label": concept.english_label,
                                  "concept_id": concept.concept_id,
                                  "hindi_label":concept.hindi_label,"sanskrit_label":concept.sanskrit_label
                              } 
                             for concept in concepts 
                             if concept.sanskrit_label == sanskrit_label or concept.sanskrit_label.startswith(f"{sanskrit_label}_")}
        
        if filtered_concepts:
            return jsonify({"concepts": filtered_concepts, "option": "list_found"}), 200

    # Option when no concepts are found
    return jsonify({"message": "No concepts found for the given sanskrit_label", "option": "other"}), 404

@concept_blueprint.route('/getconcepts/english/<string:english_label>', methods=['GET'])
@measure_response_time
def get_concepts_by_english_string_label(english_label):
    # Fetch concepts by english_label
    concepts = ConceptService.get_concepts_by_english_string_label(english_label)
    if concepts:
        filtered_concepts = {concept.english_label: {
                                  "hindi_label": concept.hindi_label,
                                  "concept_id": concept.concept_id,
                                  "sanskrit_label": concept.sanskrit_label,
                                  "concept_label": concept.concept_label 
                              } 
                             for concept in concepts 
                             if concept.english_label == english_label or concept.english_label.startswith(f"{english_label}_")}
        
        if filtered_concepts:
            return jsonify({"concepts": filtered_concepts, "option": "list_found"}), 200

    # Option when no concepts are found
    return jsonify({"message": "No concepts found for the given english_label", "option": "other"}), 404


@concept_blueprint.route('/check_submission_status/<int:submission_id>', methods=['GET'])
def check_submission_status(submission_id):
    submission = ConceptSubmission.query.get(submission_id)
    if not submission:
        return jsonify({"status": "not_found"}), 404
    
    if submission.status == 'accepted':
        concept = ConceptDictionary.query.filter_by(concept_id=submission.concept_id).first()
        if concept:
            return jsonify({
                "status": "approved",
                "concept": {
                    "concept_id": concept.concept_id,
                    "concept_name": concept.concept_label,
                    "hindi_label": concept.hindi_label,
                    "english_label": concept.english_label,
                    "sanskrit_label": concept.sanskrit_label
                }
            })
    
    return jsonify({
        "status": submission.status,
        "message": "Submission is still pending"
    })
    
@concept_blueprint.route('/duplicates', methods=['GET'])
def get_duplicate_concepts():
    from sqlalchemy import func

    duplicates = (
        db.session.query(ConceptDictionary.concept_label)
        .group_by(ConceptDictionary.concept_label)
        .having(func.count(ConceptDictionary.concept_label) > 1)
        .all()
    )

    concept_labels = [d[0] for d in duplicates]
    if not concept_labels:
        return jsonify({"message": "No duplicates found"}), 404

    all_duplicates = (
        ConceptDictionary.query.filter(ConceptDictionary.concept_label.in_(concept_labels))
        .order_by(ConceptDictionary.concept_label)
        .all()
    )

    result = {}
    for concept in all_duplicates:
        label = concept.concept_label
        if label not in result:
            result[label] = []
        result[label].append({
            "concept_id": concept.concept_id,
            "concept_label": concept.concept_label,
            "hindi_label": concept.hindi_label,
            "sanskrit_label": concept.sanskrit_label,
            "english_label": concept.english_label,
            "mrsc": concept.mrsc
        })

    return jsonify(result), 200

from flask import request
from application.models.activity_log_model import ConceptActivityLog
from datetime import datetime, timedelta

def log_activity(action, concept_id=None, concept_label=None, details=None):
    """Helper function to log user activities"""
    try:
        # Get client information
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        log_entry = ConceptActivityLog(
            username=None,  # Can be updated if you have username later
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            concept_id=concept_id,
            concept_label=concept_label,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Failed to log activity: {e}")
        db.session.rollback()

@concept_blueprint.route('/getconceptbyid/<int:concept_id>', methods=['GET'])
def get_concept_by_id(concept_id):
    concept = ConceptService.get_concept_by_id(concept_id)
    if concept:
        # Log the view action
        log_activity(
            action='view',
            concept_id=concept_id,
            concept_label=concept.concept_label,
            details={
                'endpoint': '/getconceptbyid',
                'method': 'GET'
            }
        )
        
        return jsonify({
            "concept": {
                "concept_id": concept.concept_id,
                "concept_label": concept.concept_label,
                "hindi_label": concept.hindi_label,
                "sanskrit_label": concept.sanskrit_label,
                "english_label": concept.english_label,
                "mrsc": concept.mrsc
            }
        }), 200
    return jsonify({"message": "Concept not found"}), 404



@concept_blueprint.route('/delete/<int:concept_id>', methods=['DELETE'])
def delete_concept(concept_id):
    try:
        username = request.json.get('username')  # Get username from request
        concept = ConceptDictionary.query.get_or_404(concept_id)
        
        # Log before deletion
        log_entry = ConceptActivityLog(
            username=username,  # Include the username
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            action='delete',
            concept_id=concept_id,
            concept_label=concept.concept_label,
            details={
                'hindi_label': concept.hindi_label,
                'sanskrit_label': concept.sanskrit_label,
                'english_label': concept.english_label,
                'mrsc': concept.mrsc,
                'endpoint': '/delete',
                'method': 'DELETE'
            },
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        
        concept_details = {
            "concept_id": concept.concept_id,
            "concept_label": concept.concept_label,
            "hindi_label": concept.hindi_label,
            "sanskrit_label": concept.sanskrit_label,
            "english_label": concept.english_label,
            "mrsc": concept.mrsc
        }
        
        db.session.delete(concept)
        db.session.commit()
        
        temp_concept = type('TempConcept', (), concept_details)
        # send_concept_notification("delete", temp_concept)
        
        return jsonify({
            "message": "Concept deleted successfully",
            "deleted_concept": concept_details
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
    
@concept_blueprint.route('/activity_logs', methods=['GET'])
def get_activity_logs():
    try:
        # Get query parameters
        concept_id = request.args.get('concept_id')
        action = request.args.get('action')
        limit = int(request.args.get('limit', 100))
        days = int(request.args.get('days', 7))  # Default to last 7 days
        
        query = ConceptActivityLog.query
        
        if concept_id:
            query = query.filter_by(concept_id=concept_id)
        if action:
            query = query.filter_by(action=action)
            
        # Filter by date range
        from_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ConceptActivityLog.timestamp >= from_date)
            
        logs = query.order_by(ConceptActivityLog.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'logs': [{
                'id': log.id,
                'username': log.username,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'action': log.action,
                'concept_id': log.concept_id,
                'concept_label': log.concept_label,
                'details': log.details,
                'timestamp': log.timestamp.isoformat()
            } for log in logs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# def send_concept_notification(action, concept, updated_fields=None):
#     """Send notification about concept changes to specified recipients."""
#     recipients = [
#         "sashank.tatavolu@research.iiit.ac.in"
#     ]
    
#     if action == "edit":
#         subject = f"Concept Updated: {concept.concept_label}"
#         changes = "\n".join([f"- {field}: {getattr(concept, field)}" 
#                            for field in updated_fields]) if updated_fields else "No specific fields mentioned"
#         body = (
#             f"The following concept has been updated:\n\n"
#             f"Concept ID: {concept.concept_id}\n"
#             f"Concept Label: {concept.concept_label}\n\n"
#             f"Updated Fields:\n{changes}\n\n"
#             f"Current Concept Details:\n"
#             f"- Hindi Label: {concept.hindi_label}\n"
#             f"- Sanskrit Label: {concept.sanskrit_label}\n"
#             f"- English Label: {concept.english_label}\n"
#             f"- MRSC: {concept.mrsc}\n"
#         )
#     elif action == "delete":
#         subject = f"Concept Deleted: {concept.concept_label}"
#         body = (
#             f"The following concept has been deleted:\n\n"
#             f"Concept ID: {concept.concept_id}\n"
#             f"Concept Label: {concept.concept_label}\n"
#             f"Hindi Label: {concept.hindi_label}\n"
#             f"Sanskrit Label: {concept.sanskrit_label}\n"
#             f"English Label: {concept.english_label}\n"
#             f"MRSC: {concept.mrsc}\n"
#         )
    
#     for recipient in recipients:
#         send_email(subject, body, recipient)

  

@concept_blueprint.route('/validate_concept_label/<string:concept_label>', methods=['GET'])
def validate_concept_label(concept_label):
    """
    Validate the concept label and suggest the next available label if it exists.
    """
    try:
        # Extract the base name (e.g., 'lesson' from 'lesson_1')
        base_label = concept_label.split('_')[0]
        
        # Fetch all concept labels starting with the base label
        existing_labels = [concept.concept_label 
                          for concept in ConceptDictionary.query.filter(
                              ConceptDictionary.concept_label.startswith(base_label)
                          ).all()]
        
        # Regex to extract numeric parts from labels like lesson_1, lesson_2, etc.
        numeric_label_pattern = re.compile(rf"^{base_label}_(\d+)$")

        # Find the numbers from the existing labels
        existing_numbers = []
        for label in existing_labels:
            match = numeric_label_pattern.match(label)
            if match:
                existing_numbers.append(int(match.group(1)))

        # Suggest the next label by incrementing the highest existing number by 1
        if existing_numbers:
            max_number = max(existing_numbers)
            next_label = f"{base_label}_{max_number + 1}"
        else:
            # If no labels exist, suggest the first label
            next_label = f"{base_label}_1"

        # Check if the exact label exists
        if concept_label in existing_labels:
            return jsonify({
                'option': 'found',
                'message': f"The concept label '{concept_label}' already exists.",
                'suggested_label': next_label,
                'existing_labels': existing_labels
            }), 200
        else:
            return jsonify({
                'option': 'not_found',
                'message': f"The concept label '{concept_label}' does not exist.",
                'suggested_label': next_label,
                'existing_labels': existing_labels
            }), 200

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500
    
@concept_blueprint.route('/getconceptss/<string:english_label>', methods=['GET'])
def get_concepts_by_english_label(english_label):
    """
    Validate the English label and suggest the next available label if it exists.
    """
    try:
        # Extract the base name (e.g., 'lesson' from 'lesson_1')
        base_label = english_label.split('_')[0]
        
        # Fetch all English labels starting with the base label
        existing_labels = ConceptService.get_concepts_by_english_label(base_label)
        
        # Log existing labels to check if they are fetched correctly
        print(f"Existing labels: {existing_labels}")

        # Regex to extract numeric parts from labels like lesson_1, lesson_2, etc.
        numeric_label_pattern = re.compile(rf"^{base_label}_(\d+)$")

        # Find the numbers from the existing labels
        existing_numbers = []
        for label in existing_labels:
            match = numeric_label_pattern.match(label)
            if match:
                existing_numbers.append(int(match.group(1)))

        # Suggest the next label by incrementing the highest existing number by 1
        if existing_numbers:
            max_number = max(existing_numbers)
            next_label = f"{base_label}_{max_number + 1}"
        else:
            # If no labels exist, suggest the first label
            next_label = f"{base_label}_1"

        # Check if the exact label exists
        if english_label in existing_labels:
            return jsonify({
                'option': 'found',
                'message': f"The English label '{english_label}' already exists.",
                'suggested_label': next_label
            }), 200
        else:
            return jsonify({
                'option': 'not_found',
                'message': f"The English label '{english_label}' does not exist.",
                'suggested_label': next_label
            }), 200

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

    

@concept_blueprint.route('/validate_hindi_label/<string:hindi_label>', methods=['GET'])
def validate_hindi_label(hindi_label):
    """
    Validate the Hindi label and suggest the next available label if it exists.
    """
    try:
        # Extract the base name (e.g., 'पाठ' from 'पाठ_1')
        base_label = hindi_label.split('_')[0]
        
        # Fetch all Hindi labels starting with the base label
        existing_labels = ConceptService.get_concepts_by_hindi_label(base_label)
        existing_labels = [concept.hindi_label for concept in existing_labels]
        
        # Regex to extract numeric parts from labels like पाठ_1, पाठ_2, etc.
        numeric_label_pattern = re.compile(rf"^{base_label}_(\d+)$")

        # Find the numbers from the existing labels
        existing_numbers = []
        for label in existing_labels:
            match = numeric_label_pattern.match(label)
            if match:
                existing_numbers.append(int(match.group(1)))

        # Suggest the next label by incrementing the highest existing number by 1
        if existing_numbers:
            max_number = max(existing_numbers)
            next_label = f"{base_label}_{max_number + 1}"
        else:
            # If no labels exist, suggest the first label
            next_label = f"{base_label}_1"

        # Check if the exact label exists
        if hindi_label in existing_labels:
            return jsonify({
                'option': 'found',
                'message': f"The Hindi label '{hindi_label}' already exists.",
                'suggested_label': next_label
            }), 200
        else:
            return jsonify({
                'option': 'not_found',
                'message': f"The Hindi label '{hindi_label}' does not exist.",
                'suggested_label': next_label
            }), 200

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500


@concept_blueprint.route('/validate_sanskrit_label/<string:sanskrit_label>', methods=['GET'])
def validate_sanskrit_label(sanskrit_label):
    """
    Validate the Sanskrit label and suggest the next available label if it exists.
    """
    try:
        # Extract the base name (e.g., 'पाठ' from 'पाठ_1')
        base_label = sanskrit_label.split('_')[0]
        
        # Fetch all Sanskrit labels starting with the base label
        existing_labels = ConceptService.get_concepts_by_sanskrit_label(base_label)
        existing_labels = [concept.sanskrit_label for concept in existing_labels if concept.sanskrit_label]
        
        # Regex to extract numeric parts from labels like पाठ_1, पाठ_2, etc.
        numeric_label_pattern = re.compile(rf"^{base_label}_(\d+)$")

        # Find the numbers from the existing labels
        existing_numbers = []
        for label in existing_labels:
            match = numeric_label_pattern.match(label)
            if match:
                existing_numbers.append(int(match.group(1)))

        # Suggest the next label by incrementing the highest existing number by 1
        if existing_numbers:
            max_number = max(existing_numbers)
            next_label = f"{base_label}_{max_number + 1}"
        else:
            # If no labels exist, suggest the first label
            next_label = f"{base_label}_1"

        # Check if the exact label exists
        if sanskrit_label in existing_labels:
            return jsonify({
                'option': 'found',
                'message': f"The Sanskrit label '{sanskrit_label}' already exists.",
                'suggested_label': next_label
            }), 200
        else:
            return jsonify({
                'option': 'not_found',
                'message': f"The Sanskrit label '{sanskrit_label}' does not exist.",
                'suggested_label': next_label
            }), 200

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500


@concept_blueprint.route('/search_tam', methods=['GET'])
@measure_response_time
def search_tam_dictionary():
    """
    Search TAM dictionary with language-specific filters
    Parameters:
        - language: One of 'hindi', 'sanskrit', 'english' (required)
        - query: Search term (required)
        - limit: Maximum results to return (optional)
    """
    try:
        # Get query parameters
        language = request.args.get('language', '').lower()
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 10))  # Default to 10 results
        
        if not language or not query:
            return jsonify({
                "error": "Both 'language' and 'query' parameters are required",
                "example": "/search_tam?language=hindi&query=rahA&limit=5"
            }), 400
        
        # Validate language parameter
        if language not in ['hindi', 'sanskrit', 'english']:
            return jsonify({
                "error": "Invalid language parameter. Must be one of: hindi, sanskrit, english"
            }), 400
        
        # Build query based on language
        if language == 'hindi':
            results = TAM_Dictionary.query.filter(
                TAM_Dictionary.hindi_tam.ilike(f'%{query}%')
            ).limit(limit).all()
        elif language == 'sanskrit':
            results = TAM_Dictionary.query.filter(
                TAM_Dictionary.sanskrit_tam.ilike(f'%{query}%')
            ).limit(limit).all()
        else:  # english
            results = TAM_Dictionary.query.filter(
                TAM_Dictionary.english_tam.ilike(f'%{query}%')
            ).limit(limit).all()
        
        # Format results
        formatted_results = [{
            "id": result.id,
            "u_tam": result.u_tam,
            "hindi_tam": result.hindi_tam,
            "sanskrit_tam": result.sanskrit_tam,
            "english_tam": result.english_tam
        } for result in results]
        
        return jsonify({
            "count": len(formatted_results),
            "results": formatted_results,
            "search_params": {
                "language": language,
                "query": query,
                "limit": limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"An error occurred: {str(e)}"
        }), 500
        

# Fetch emails dynamically based on role
def get_recipient_emails(language_filter=None):
    try:
        # Fetch all dictionary validators
        recipients = UserService.get_users_by_role('dictionaryValidator')

        if language_filter:
            recipients = [
                user for user in recipients
                if isinstance(user.language, list)
                and language_filter.lower() in [lang.lower() for lang in user.language]
            ]

        return [user.email for user in recipients]
    except Exception as e:
        print(f"Error fetching recipients: {e}")
        return []


# Counter to track the next recipient (this needs to persist across requests)
current_recipient_index = 0
@concept_blueprint.route('/submit_concept', methods=['POST'])
def submit_concept():
    global current_recipient_index
    data = request.get_json()

    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    from_email = user.email

    concept = data.get('concept', {})
    hindi_concept = concept.get('hindi', '')
    english_concept = concept.get('english', '')
    concept_id = data.get('indexes', [])[0]
    sentence_data = data.get('subSegment', '')

    # NEW: Extract metadata
    project_name = data.get("project_name")
    chapter_id = data.get("chapter_id")
    chapter_name = data.get("chapter_name")
    segment_id = data.get("segment_id")
    concept_index = data.get('concept_index')

    try:
        sentence_id, hindi_sentence = sentence_data.split(' : ', 1)
    except ValueError:
        sentence_id, hindi_sentence = '', sentence_data

    english_sentence = data.get('english_sentence', '')
    if not english_sentence:
        return jsonify({"error": "English sentence is required"}), 400

    recipient_emails = get_recipient_emails()
    if not recipient_emails:
        return jsonify({"error": "No recipients found with the role 'dictionary validator'."}), 500

    recipient_email = recipient_emails[current_recipient_index]
    current_recipient_index = (current_recipient_index + 1) % len(recipient_emails)

    subject = "New Concept Request"
    body = (
        f"Dear Team,\n\n"
        f"A new concept has been submitted for review:\n\n"
        f"Concept Details:\n"
        f"- **Hindi Concept**: {hindi_concept}\n"
        f"- **English Concept**: {english_concept}\n"
        f"- **Concept ID**: {concept_id}\n\n"
        f"Sentence Details:\n"
        f"- **Sentence ID**: {sentence_id}\n"
        f"- **Hindi Sentence**: {hindi_sentence}\n"
        f"- **English Sentence**: {english_sentence}\n\n"
        f"Please review the submission at your earliest convenience.\n\n"
        f"Best regards,\n"
        f"Your Automated Concept Submission System"
    )

    send_email(subject, body, recipient_email, from_email=from_email)

    try:
        new_submission = ConceptSubmission(
            user_id=user_id,
            from_email=from_email,
            to_email=recipient_email,
            hindi_concept=hindi_concept,
            english_concept=english_concept,
            concept_id=concept_id,
            status='pending',
            sentence_id=sentence_id,
            sentence=hindi_sentence,
            english_sentence=english_sentence,
            concept_index=concept_index,  # Add this field
            original_concept=data.get('original_concept'),

            # NEW: Assign metadata
            project_name=project_name,
            chapter_id=chapter_id,
            chapter_name=chapter_name,
            segment_id=segment_id,
        )

        db.session.add(new_submission)
        db.session.commit()

        print(f"Submission data saved to the database.")
    except Exception as e:
        print(f"Error occurred: {e}") 
        return jsonify({"error": f"Failed to save submission to database: {str(e)}"}), 500

    return jsonify({
        "message": f"Concept submitted and email sent to {recipient_email}.",
        "status": "pending"
    }), 200


@concept_blueprint.route('/get_pending_concepts/<segment_id>', methods=['GET'])
def get_pending_concepts(segment_id):
    # Add debug logging
    print(f"Received request for segment_id: {segment_id} (type: {type(segment_id)})")
    
    if not segment_id:
        return jsonify({"error": "segment_id is required"}), 400
    
    pending = ConceptSubmission.query.filter(
        ConceptSubmission.segment_id == segment_id,
        ConceptSubmission.status == 'pending'
    ).all()
    
    print(f"Found {len(pending)} pending concepts for segment {segment_id}")
    
    result = [{
        'temp_id': s.id,
        'concept_index': s.concept_index,
        'proposed_concept': s.sanskrit_concept or s.hindi_concept,
        'original_concept': s.original_concept
    } for s in pending]
    
    print(f"Returning: {result}")
    return jsonify(result)
    
@concept_blueprint.route('/submit_sanskrit_concept', methods=['POST'])
def submit_concept_sanskrit():
    global current_recipient_index
    data = request.get_json()

    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    from_email = user.email

    concept = data.get('concept', {})
    hindi_concept = concept.get('hindi', '')
    english_concept = concept.get('english', '')
    sanskrit_concept = concept.get('sanskrit', '')
    sentence_data = data.get('subSegment', '')

    # Extract metadata
    project_name = data.get("project_name")
    chapter_id = data.get("chapter_id")
    chapter_name = data.get("chapter_name")
    segment_id = data.get("segment_id")

    if english_concept == '' or sanskrit_concept == '':
        return jsonify({"error": "English concept and Sanskrit concept are required"}), 400

    try:
        sentence_id, hindi_sentence = sentence_data.split(' : ', 1)
    except ValueError:
        sentence_id, hindi_sentence = '', sentence_data

    english_sentence = data.get('english_sentence', '')
    if not english_sentence:
        return jsonify({"error": "English sentence is required"}), 400

    subject = "New Sanskrit Concept Request"
    body_lines = [
        "Dear Team,", "", "A new Sanskrit concept has been submitted for review:", "",
        "Concept Details:",
        f"- Sanskrit Concept: {sanskrit_concept}",
        f"- English Concept: {english_concept}",
    ]
    if hindi_concept:
        body_lines.append(f"- Hindi Concept: {hindi_concept}")
    body_lines.extend([
        "", "Sentence Details:",
        f"- Sentence ID: {sentence_id}",
        f"- Hindi Sentence: {hindi_sentence}",
        f"- English Sentence: {english_sentence}", "", 
        "Project Details:",
        f"- Project: {project_name}",
        f"- Chapter: {chapter_name} (ID: {chapter_id})",
        f"- Segment ID: {segment_id}", "",
        "Please review at your earliest convenience.",
        "", "Best regards,", "Concept Submission System"
    ])
    body = "\n".join(body_lines)

    recipient_emails = get_recipient_emails(language_filter='Sanskrit')
    if not recipient_emails:
        return jsonify({"error": "No Sanskrit validators available"}), 500

    recipient_email = recipient_emails[current_recipient_index]
    current_recipient_index = (current_recipient_index + 1) % len(recipient_emails)

    try:
        new_submission = ConceptSubmission(
            user_id=user_id,
            from_email=from_email,
            to_email=recipient_email,
            hindi_concept=hindi_concept if hindi_concept else None,
            english_concept=english_concept,
            sanskrit_concept=sanskrit_concept,
            concept_id=None,  # No concept ID assigned yet
            sentence_id=sentence_id,
            status='pending',
            sentence=hindi_sentence,
            english_sentence=english_sentence,
            project_name=project_name,
            chapter_id=chapter_id,
            chapter_name=chapter_name,
            segment_id=segment_id,
        )

        db.session.add(new_submission)
        db.session.commit()

        send_email(subject, body, recipient_email, from_email=from_email)

        return jsonify({
            "success": True,
            "submission_id": new_submission.id,
            "message": f"Sanskrit concept submitted to {recipient_email}",
            "data": {
                "sanskrit": sanskrit_concept,
                "english": english_concept,
                "hindi": hindi_concept if hindi_concept else None,
                "status": "pending"
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
@concept_blueprint.route('/update_sanskrit_label/<int:concept_id>', methods=['PUT'])
@jwt_required()
@measure_response_time
def propose_sanskrit_label(concept_id):
    try:
        data = request.get_json()
        proposed_sanskrit = data.get('sanskrit_label')
        user_id = data.get('user_id')

        if not proposed_sanskrit or not user_id:
            return jsonify({"error": "Sanskrit label and user ID are required"}), 400

        # Fetch concept
        concept = ConceptDictionary.query.filter_by(concept_id=concept_id).first()
        if not concept:
            return jsonify({"error": "Concept not found"}), 404

        # Fetch user info
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        from_email = user.email

        # Get Sanskrit validators
        recipients = get_recipient_emails(language_filter='Sanskrit')
        if not recipients:
            return jsonify({"error": "No Sanskrit validators found"}), 500

        # Email content
        subject = "New Sanskrit Label Proposal"
        body = (
            f"Dear Validator,\n\n"
            f"A user has proposed a new Sanskrit label for a concept.\n\n"
            f"Concept ID: {concept.concept_id}\n"
            f"Current Hindi Label: {concept.hindi_label}\n"
            f"Current Sanskrit Label: {concept.sanskrit_label or 'N/A'}\n"
            f"Proposed Sanskrit Label: {proposed_sanskrit}\n"
            f"Submitted By: {from_email}\n\n"
            f"Please review and approve/reject this proposal via the validation interface.\n\n"
            f"Best,\nDictionary System"
        )

        # Send to all validators (or pick one in round-robin if needed)
        for email in recipients:
            send_email(subject, body, email, from_email=from_email)

        # Optionally: save as a new ConceptSubmission for tracking
        new_submission = ConceptSubmission(
            user_id=user_id,
            from_email=from_email,
            to_email=recipients[0],
            hindi_concept=concept.hindi_label,
            english_concept=concept.english_label,
            sanskrit_concept=proposed_sanskrit,
            concept_id=concept.concept_id,
            sentence_id='N/A',
            sentence='N/A',
            english_sentence='N/A'
        )
        db.session.add(new_submission)
        db.session.commit()

        return jsonify({"message": f"Sanskrit label proposal sent to {recipients[0]}"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error proposing Sanskrit label: {e}")
        return jsonify({"error": str(e)}), 500
    


@concept_blueprint.route('/approve_sanskrit_label/<temp_id>', methods=['POST'])
@jwt_required()
@measure_response_time
def approve_sanskrit_label(temp_id):
    try:
        # Step 1: Find the submission entry
        submission = ConceptSubmission.query.filter_by(id=temp_id).first()
        if not submission:
            return jsonify({"error": "Submission not found"}), 404

        # Step 2: Get the target concept from ConceptDictionary
        concept = ConceptDictionary.query.filter_by(concept_id=submission.concept_id).first()
        if not concept:
            return jsonify({"error": "Target concept not found"}), 404

        # Step 3: Update Sanskrit label
        concept.sanskrit_label = submission.sanskrit_concept
        db.session.commit()

        # Step 4: Send acceptance email to submitter
        subject = "Sanskrit Label Approved"
        body = (
            f"Dear User,\n\n"
            f"Your proposed Sanskrit label '{submission.sanskrit_concept}' for the concept "
            f"with Hindi label '{submission.hindi_concept}' and English label '{submission.english_concept}' "
            f"has been approved and added to the dictionary.\n\n"
            f"Thank you for your contribution!\n\n"
            f"Best,\nDictionary Validation Team"
        )
        send_email(subject, body, submission.from_email)

        # Step 5: Remove the submission from the pending list
        db.session.delete(submission)
        db.session.commit()

        return jsonify({"message": "Sanskrit label approved and updated."}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error in approving Sanskrit label: {e}")
        return jsonify({"error": str(e)}), 500


SMTP_SERVER = 'smtp.gmail.com'  # e.g., Gmail SMTP server
SMTP_PORT = 587  # SMTP port for STARTTLS
SENDER_EMAIL = 'tat.iiith2025@gmail.com'
SENDER_PASSWORD = 'noal fndb ucip aiui'  # Make sure this is securely handled



def send_email(subject, body, to_email, from_email=None):
    try:
        # Set up the email server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Start TLS encryption
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Determine the "From" address
        sender_email = from_email if from_email else SENDER_EMAIL

        # Create the email with UTF-8 headers and body
        msg = MIMEMultipart()
        msg['From'] = sender_email  # Use provided "from_email" if available
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach the body with UTF-8 encoding
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Ensure UTF-8 for all headers
        msg_str = msg.as_string()
        msg_bytes = msg_str.encode('utf-8')  # Encode the whole message as UTF-8

        # Send the email
        server.sendmail(sender_email, to_email, msg_bytes)
        server.quit()

        print(f"Email sent successfully from {sender_email} to {to_email}.")
    except Exception as e:
        print(f"Failed to send email: {e}")


@concept_blueprint.route('/get_req', methods=['GET'])
@jwt_required()
@measure_response_time
def get_concepts():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        current_user_email = user.email
        user_language = user.language[0] if isinstance(user.language, list) else user.language
        user_language = user_language.lower()
        
        # Join with User table to get submitter info and filter by status='pending'
        submissions = db.session.query(
            ConceptSubmission,
            User.username,
            User.email
        ).join(
            User, ConceptSubmission.user_id == User.id
        ).filter(
            ConceptSubmission.to_email == current_user_email,
            ConceptSubmission.status == 'pending'  # Only get pending submissions
        ).all()

        if not submissions:
            return jsonify({"error": "No pending submissions found"}), 404

        response_data = []
        for submission, submitter_username, submitter_email in submissions:
            concept_data = {
                'Temp_Id': submission.id,
                'sentence_id': submission.sentence_id,
                'hindi_sentence': submission.sentence,
                'english_sentence': submission.english_sentence,
                'concept_id': submission.concept_id,
                'hindi_label': submission.hindi_concept,
                'english_label': submission.english_concept,
                'status': submission.status,
                'submitted_at': submission.created_at.isoformat() if submission.created_at else None,
                'submitter_username': submitter_username,
                'submitter_email': submitter_email,
                'project_name': submission.project_name,
                'chapter_name': submission.chapter_name,
                'segment_id': submission.segment_id
            }
            
            if user_language == 'sanskrit':
                concept_data['sanskrit_label'] = getattr(submission, 'sanskrit_concept', submission.hindi_concept)
            
            response_data.append(concept_data)

        return jsonify(response_data), 200
    
    except Exception as e:
        print(f"Error fetching concepts: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
    
@concept_blueprint.route('/edit/<int:concept_id>', methods=['PUT'])
def edit_concept(concept_id):
    try:
        data = request.json
        username = data.pop('username', None)  # Extract username from request
        concept = ConceptDictionary.query.get_or_404(concept_id)
        
        # Track changes
        original_values = {
            'concept_label': concept.concept_label,
            'hindi_label': concept.hindi_label,
            'sanskrit_label': concept.sanskrit_label,
            'english_label': concept.english_label,
            'mrsc': concept.mrsc
        }
        
        updated_fields = []
        changes = {}
        
        # Check each field for changes
        for field in ['concept_label', 'hindi_label', 'sanskrit_label', 'english_label', 'mrsc']:
            if field in data and data[field] != getattr(concept, field):
                updated_fields.append(field)
                changes[field] = {
                    'old': getattr(concept, field),
                    'new': data[field]
                }
                setattr(concept, field, data[field])

        if not updated_fields:
            return jsonify({"message": "No changes detected"}), 200

        db.session.commit()
        
        # Log the edit action with changes
        log_entry = ConceptActivityLog(
            username=username,  # Include the username
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            action='edit',
            concept_id=concept_id,
            concept_label=concept.concept_label,
            details={
                'changes': changes,
                'original_values': original_values,
                'endpoint': '/edit',
                'method': 'PUT'
            },
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # Send notification to the respective dictionary validator based on the updated field
        for field in updated_fields:
            if field == 'concept_label':
                # Get all dictionary validators for concept label changes
                recipients = get_recipient_emails()
                if recipients:
                    subject = f"Concept Label Updated: {original_values['concept_label']} → {concept.concept_label}"
                    body = (
                        f"The concept label has been updated:\n\n"
                        f"Concept ID: {concept.concept_id}\n"
                        f"Previous Concept Label: {original_values['concept_label']}\n"
                        f"New Concept Label: {concept.concept_label}\n\n"
                        f"Other Details:\n"
                        f"- Hindi Label: {concept.hindi_label}\n"
                        f"- Sanskrit Label: {concept.sanskrit_label}\n"
                        f"- English Label: {concept.english_label}\n\n"
                        f"Updated by: {username}\n"
                        f"Timestamp: {datetime.utcnow().isoformat()}\n\n"
                        f"Please review the changes."
                    )
                    # for recipient in recipients:
                    #     send_email(subject, body, recipient)
            
            elif field == 'sanskrit_label':
                # Get Sanskrit validators
                recipients = get_recipient_emails(language_filter='Sanskrit')
                if recipients:
                    subject = f"Sanskrit Label Updated: {concept.concept_label}"
                    body = (
                        f"The Sanskrit label for the following concept has been updated:\n\n"
                        f"Concept ID: {concept.concept_id}\n"
                        f"Concept Label: {concept.concept_label}\n"
                        f"Previous Sanskrit Label: {changes[field]['old']}\n"
                        f"New Sanskrit Label: {changes[field]['new']}\n\n"
                        f"Other Details:\n"
                        f"- Hindi Label: {concept.hindi_label}\n"
                        f"- English Label: {concept.english_label}\n\n"
                        f"Updated by: {username}\n"
                        f"Timestamp: {datetime.utcnow().isoformat()}\n\n"
                        f"Please review the changes."
                    )
                    # for recipient in recipients:
                    #     send_email(subject, body, recipient)
            
            elif field in ['hindi_label', 'english_label']:
                # Get Hindi/English validators
                recipients = get_recipient_emails(language_filter='Hindi' if field == 'hindi_label' else 'English')
                if recipients:
                    subject = f"{field.capitalize()} Label Updated: {concept.concept_label}"
                    body = (
                        f"The {field} label for the following concept has been updated:\n\n"
                        f"Concept ID: {concept.concept_id}\n"
                        f"Concept Label: {concept.concept_label}\n"
                        f"Previous {field.capitalize()} Label: {changes[field]['old']}\n"
                        f"New {field.capitalize()} Label: {changes[field]['new']}\n\n"
                        f"Other Details:\n"
                        f"- Sanskrit Label: {concept.sanskrit_label}\n"
                        f"- {('English' if field == 'hindi_label' else 'Hindi')} Label: "
                        f"{concept.english_label if field == 'hindi_label' else concept.hindi_label}\n\n"
                        f"Updated by: {username}\n"
                        f"Timestamp: {datetime.utcnow().isoformat()}\n\n"
                        f"Please review the changes."
                    )
                    # for recipient in recipients:
                    #     send_email(subject, body, recipient)
        
        return jsonify({
            "message": "Concept updated successfully",
            "updated_fields": updated_fields
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@concept_blueprint.route('/update_sanskrit_label/<int:concept_id>', methods=['PUT'])
@jwt_required()
@measure_response_time
def update_sanskrit_label(concept_id):
    try:
        data = request.get_json()
        username = data.get('username')  # Get username from request
        sanskrit_label = data.get('sanskrit_label')
        
        if not sanskrit_label:
            return jsonify({"error": "Sanskrit label is required"}), 400

        concept = ConceptDictionary.query.filter_by(concept_id=concept_id).first()
        if not concept:
            return jsonify({"error": "Concept not found"}), 404

        # Store original value for notification
        original_sanskrit = concept.sanskrit_label
        
        # Update the Sanskrit label
        concept.sanskrit_label = sanskrit_label
        
        db.session.commit()
        
        # Send notification to Sanskrit validators
        recipients = get_recipient_emails(language_filter='Sanskrit')
        if recipients:
            subject = f"Sanskrit Label Updated: {concept.concept_label}"
            body = (
                f"The Sanskrit label for the following concept has been updated:\n\n"
                f"Concept ID: {concept.concept_id}\n"
                f"Concept Label: {concept.concept_label}\n"
                f"Previous Sanskrit Label: {original_sanskrit}\n"
                f"New Sanskrit Label: {sanskrit_label}\n\n"
                f"Other Details:\n"
                f"- Hindi Label: {concept.hindi_label}\n"
                f"- English Label: {concept.english_label}\n\n"
                f"Updated by: {username}\n"
                f"Timestamp: {datetime.utcnow().isoformat()}\n\n"
                f"Please review the changes."
            )
            # for recipient in recipients:
            #     send_email(subject, body, recipient)
        
        return jsonify({"message": "Sanskrit label updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error updating Sanskrit label: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@concept_blueprint.route('/accept_and_store/<temp_id>', methods=['POST'])
@jwt_required()
@measure_response_time
def accept_and_store(temp_id):
    try:
        # Step 1: Find the submission entry
        submission = ConceptSubmission.query.filter_by(id=temp_id).first()
        if not submission:
            return jsonify({"error": "Submission not found"}), 404

        # Step 2: Get the next available concept ID
        max_id = db.session.query(db.func.max(ConceptDictionary.concept_id)).scalar() or 0
        new_concept_id = max_id + 1

        # Step 3: Create new concept in dictionary
        new_concept = ConceptDictionary(
            concept_id=new_concept_id,
            concept_label=submission.sanskrit_concept or submission.hindi_concept,
            hindi_label=submission.hindi_concept,
            sanskrit_label=submission.sanskrit_concept,
            english_label=submission.english_concept,
            mrsc=None
        )
        db.session.add(new_concept)

        # Step 4: Update submission with concept ID and mark as accepted
        submission.concept_id = new_concept_id
        submission.status = 'accepted'
        
        # Step 5: Commit changes
        db.session.commit()

        # Step 6: Send acceptance email to submitter
        subject = "Sanskrit Concept Approved"
        body = (
            f"Dear User,\n\n"
            f"Your proposed Sanskrit concept has been approved and added to the dictionary.\n\n"
            f"Concept Details:\n"
            f"- Sanskrit: {submission.sanskrit_concept}\n"
            f"- English: {submission.english_concept}\n"
            f"- Hindi: {submission.hindi_concept}\n"
            f"- New Concept ID: {new_concept_id}\n\n"
            f"Project Details:\n"
            f"- Project: {submission.project_name}\n"
            f"- Chapter: {submission.chapter_name} (ID: {submission.chapter_id})\n"
            f"- Segment ID: {submission.segment_id}\n\n"
            f"Thank you for your contribution!\n\n"
            f"Best,\nDictionary Validation Team"
        )
        send_email(subject, body, submission.from_email)

        return jsonify({
            "message": "Concept approved and added to dictionary",
            "concept_id": new_concept_id,
            "concept_details": {
                "sanskrit": submission.sanskrit_concept,
                "english": submission.english_concept,
                "hindi": submission.hindi_concept
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error in approving concept: {e}")
        return jsonify({"error": str(e)}), 500
    

@concept_blueprint.route('/reject/<temp_id>', methods=['POST'])
@jwt_required()
@measure_response_time
def reject_concept(temp_id):
    try:
        submission = ConceptSubmission.query.filter_by(id=temp_id).first()
        if not submission:
            return jsonify({"error": "Submission not found"}), 404

        data = request.get_json()
        rejection_reason = data.get("reason", "").strip()
        if not rejection_reason:
            return jsonify({"error": "Rejection reason is required."}), 400

        # Update status to rejected (no concept ID assigned)
        submission.status = 'rejected'
        db.session.commit()

        # Send rejection email
        subject = "Your concept submission was rejected"
        body = (
            f"Dear User,\n\n"
            f"We regret to inform you that your concept submission has been rejected.\n\n"
            f"Submission Details:\n"
            f"- Sanskrit: {submission.sanskrit_concept}\n"
            f"- English: {submission.english_concept}\n"
            f"- Hindi: {submission.hindi_concept}\n\n"
            f"Project Details:\n"
            f"- Project: {submission.project_name}\n"
            f"- Chapter: {submission.chapter_name} (ID: {submission.chapter_id})\n"
            f"- Segment ID: {submission.segment_id}\n\n"
            f"Reason for Rejection:\n"
            f"{rejection_reason}\n\n"
            f"If you have questions about this decision, please contact us.\n\n"
            f"Best regards,\n"
            f"Dictionary Validation Team"
        )

        send_email(subject, body, submission.from_email)

        return jsonify({
            "message": "Concept rejected",
            "submission_id": submission.id,
            "reason": rejection_reason
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
