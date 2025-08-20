from collections import defaultdict
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, jwt_required
from sqlalchemy import exists
from ..models.assignment_model import Assignment
from ..models.segment_model import Segment
from ..models.user_model import User
from ..models.lexical_conceptual_model import LexicalConceptual
from ..models.relational_model import Relational
from ..models.construction_model import Construction
from ..models.discourse_model import Discourse
from ..models.chapter_model import Chapter
from ..extensions import db

assignment_blueprint = Blueprint('assignments', __name__)
    
@assignment_blueprint.route('/chapter/<int:chapter_id>/assigned_users', methods=['GET'])
def get_chapter_assigned_users(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"message": "Chapter not found"}), 404
    
    # Get unique users assigned to this chapter's segments
    users = set()
    for segment in chapter.segments:
        for assignment in segment.assignments:
            users.add((assignment.user.id, assignment.user.username))
    
    return jsonify({
        "users": [{"user_id": u[0], "username": u[1]} for u in users]
    }), 200
    
@assignment_blueprint.route('/assigned_users', methods=['GET'])
@jwt_required()
def get_assignments():
    jwt_data = get_jwt()
    user_id = jwt_data.get('user_id')

    current_user = User.query.get(user_id)
    if not current_user:
        return jsonify({"message": "User not found"}), 404

    assignments = (
        db.session.query(
            Assignment.segment_id,
            Segment.segment_index,
            Assignment.chapter_id,
            Chapter.name.label('chapter_name'),  # ⬅️ Add chapter name
            Assignment.user_id,
            User.username,
            Assignment.tab_name
        )
        .join(User, User.id == Assignment.user_id)
        .join(Segment, Segment.segment_id == Assignment.segment_id)
        .join(Chapter, Chapter.id == Assignment.chapter_id)  # ⬅️ Join Chapter table
        .filter(User.organization == current_user.organization)
        .all()
    )

    grouped_assignments = defaultdict(lambda: {
        "segment_id": None,
        "segment_index": None,
        "chapter_id": None,
        "chapter_name": None,  # ⬅️ Add this
        "user_id": None,
        "username": None,
        "assigned_tabs": []
    })

    for a in assignments:
        segment_data = grouped_assignments[a.segment_id]
        segment_data["segment_id"] = a.segment_id
        segment_data["segment_index"] = a.segment_index
        segment_data["chapter_id"] = a.chapter_id
        segment_data["chapter_name"] = a.chapter_name  # ⬅️ Set chapter name
        segment_data["user_id"] = a.user_id
        segment_data["username"] = a.username

        existing_tabs = [t['tab_name'] for t in segment_data["assigned_tabs"]]
        if a.tab_name not in existing_tabs:
            is_finalized = False

            if a.tab_name == 'lexical_conceptual':
                is_finalized = db.session.query(LexicalConceptual).filter_by(segment_id=a.segment_id, isFinalized=False).count() == 0
            elif a.tab_name == 'construction':
                is_finalized = db.session.query(Construction).filter_by(segment_id=a.segment_id, isFinalized=False).count() == 0
            elif a.tab_name == 'relational':
                is_finalized = db.session.query(Relational).filter_by(segment_id=a.segment_id, isFinalized=False).count() == 0
            elif a.tab_name == 'discourse':
                is_finalized = db.session.query(Discourse).filter_by(segment_id=a.segment_id, isFinalized=False).count() == 0

            segment_data["assigned_tabs"].append({
                "tab_name": a.tab_name,
                "isFinalized": is_finalized
            })

    return jsonify(list(grouped_assignments.values())), 200


@assignment_blueprint.route('/user_assignments/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_assignments(user_id):
    assignments = (
        db.session.query(
            Assignment.segment_id,
            Segment.segment_index,
            Assignment.chapter_id,
            Chapter.name,  # ✅ Fetch chapter_name
            Assignment.tab_name  # ✅ Fetch assigned tab_name
        )
        .join(Segment, Segment.segment_id == Assignment.segment_id)
        .join(Chapter, Chapter.id == Assignment.chapter_id)  # ✅ Join with Chapter table
        .filter(Assignment.user_id == user_id)
        .all()
    )

    if not assignments:
        return jsonify({"message": "No assignments found for this user"}), 404

    result = {}

    for a in assignments:
        segment_id = a.segment_id
        segment_index = a.segment_index
        chapter_id = f"chapter_{a.chapter_id}"
        chapter_name = a.name  # ✅ Store chapter_name
        tab_name = a.tab_name  # ✅ Store tab_name

        # Check if at least one record exists where isFinalized is True
        is_finalized = {
            "L": db.session.query(exists().where(LexicalConceptual.segment_id == segment_id, LexicalConceptual.isFinalized == True)).scalar(),
            "R": db.session.query(exists().where(Relational.segment_id == segment_id, Relational.isFinalized == True)).scalar(),
            "C": db.session.query(exists().where(Construction.segment_id == segment_id, Construction.isFinalized == True)).scalar(),
            "D": db.session.query(exists().where(Discourse.segment_id == segment_id, Discourse.isFinalized == True)).scalar(),
        }

        # Convert SQLAlchemy Boolean to Python bool
        is_finalized = {key: bool(value) for key, value in is_finalized.items()}

        # Organizing data under chapters
        if chapter_id not in result:
            result[chapter_id] = {
                "chapter_name": chapter_name,  # ✅ Include chapter_name
                "segments": [],
                "segment_ids_set": set()  # ✅ Track unique segment IDs
            }

        # ✅ Add segment only if it hasn't been added before
        existing_segment = next((s for s in result[chapter_id]["segments"] if s["segment_id"] == segment_id), None)

        if existing_segment:
            # ✅ Append new tab_name if segment already exists
            if tab_name not in existing_segment["assigned_tabs"]:
                existing_segment["assigned_tabs"].append(tab_name)
        else:
            # ✅ Create a new segment entry
            result[chapter_id]["segments"].append({
                "segment_id": segment_id,
                "segment_index": segment_index,
                "isFinalized": is_finalized,
                "assigned_tabs": [tab_name]  # ✅ Store tab names in a list
            })
            result[chapter_id]["segment_ids_set"].add(segment_id)  # ✅ Add to set

    # ✅ Remove tracking set before returning response
    for chapter in result.values():
        chapter.pop("segment_ids_set")

    return jsonify(result), 200


@assignment_blueprint.route('/segment_assignments/<int:segment_id>', methods=['GET'])
@jwt_required()
def get_segment_assignments(segment_id):
    """
    Get all user assignments for a specific segment ID
    Returns: List of users assigned to this segment with their assigned tabs
    """
    # First verify the segment exists
    segment = Segment.query.get(segment_id)
    if not segment:
        return jsonify({"message": "Segment not found"}), 404

    # Get all assignments for this segment
    assignments = (
        db.session.query(
            Assignment.user_id,
            User.username,
            Assignment.tab_name,
            Chapter.name.label('chapter_name')
        )
        .join(User, User.id == Assignment.user_id)
        .join(Chapter, Chapter.id == Assignment.chapter_id)
        .filter(Assignment.segment_id == segment_id)
        .all()
    )

    if not assignments:
        return jsonify({"message": "No assignments found for this segment"}), 404

    # Group assignments by user
    result = {
        "segment_id": segment_id,
        "segment_index": segment.segment_index,
        "chapter_id": assignments[0].chapter_id if assignments else None,
        "chapter_name": assignments[0].chapter_name if assignments else None,
        "assigned_users": []
    }

    # Group tabs by user
    user_assignments = defaultdict(list)
    for a in assignments:
        user_assignments[(a.user_id, a.username)].append(a.tab_name)

    # Format the response
    for (user_id, username), tabs in user_assignments.items():
        result["assigned_users"].append({
            "user_id": user_id,
            "username": username,
            "assigned_tabs": tabs,
            # Add any additional user info you want to include
            # "user_email": email, etc.
        })

    return jsonify(result), 200




from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from flask_mail import Message
from application.services.chapter_service import ChapterService
from application.services.measure_time import measure_response_time
# from application.extensions import mail 

chapter_blueprint = Blueprint('chapters', __name__)


@chapter_blueprint.route('/add', methods=['POST'])
@jwt_required()
@measure_response_time
def add_chapter():
    jwt_claims = get_jwt()
    data = request.get_json()

    # Create the chapter
    chapter = ChapterService.create_chapter(
        project_id=data['project_id'],
        name=data['name'],
        uploaded_by_id=jwt_claims['user_id'],
        text=data['text']
    )

    # Notify assigned users via email
    user_ids = data.get('user_ids', [])
    ChapterService.notify_users(user_ids, data['project_id'], chapter.name)

    return jsonify({'message': 'Chapter added successfully', 'chapter_id': chapter.id}), 201



@chapter_blueprint.route('/by_project/<int:project_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_chapters(project_id):
    chapters = ChapterService.get_chapters_by_project(project_id)
    chapters_data = [
        {
            'id': chapter.id,
            'name': chapter.name,
            'text': chapter.text,
            'created_at': chapter.created_at,
            'uploaded_by': chapter.uploaded_by.username,
            'assigned_to': [user.username for user in chapter.assigned_users],
            'status': "completed"
        } for chapter in chapters
    ]
    return jsonify(chapters_data), 200

@chapter_blueprint.route('/by_chapter/<int:chapter_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_chapter(chapter_id):
    chapter = ChapterService.get_chapters_by_chapter_id(chapter_id)
    print("chapter: ",chapter.id)
    if not chapter:
        return jsonify({'message': 'Chapter not found'}), 404

    chapter_data = {
        'id': chapter.id,
        'name': chapter.name,
        'text': chapter.text,
        'created_at': chapter.created_at,
        'uploaded_by': chapter.uploaded_by.username,
        'assigned_to': [user.username for user in chapter.assigned_users],
        'status': "completed"
    }
    return jsonify(chapter_data), 200

@chapter_blueprint.route('/by_chapter/<int:chapter_id>/text', methods=['GET'])
@jwt_required()
@measure_response_time
def get_chapter_text(chapter_id):
    chapter = ChapterService.get_chapters_by_chapter_id(chapter_id)
    if not chapter:
        return jsonify({'message': 'Chapter not found'}), 404

    return jsonify({'text': chapter.text}), 200


@chapter_blueprint.route('/by_chapter/<int:chapter_id>/assigned_users', methods=['GET'])
@jwt_required()
@measure_response_time
def get_assigned_users_to_chapter(chapter_id):
    assigned_users = ChapterService.get_users_assigned_to_chapter(chapter_id)
    if assigned_users is None:
        return jsonify({'message': 'Chapter not found'}), 404
    
    return jsonify(assigned_users), 200



@chapter_blueprint.route('/by_chapter/<int:chapter_id>/sentences_segments', methods=['GET'])
@jwt_required()
@measure_response_time
def get_sentences_and_segments(chapter_id):
    sentences = ChapterService.get_sentences_by_chapter_id(chapter_id)
    if not sentences:
        return jsonify({'message': 'No sentences found for the given chapter'}), 404

    sentence_ids = [sentence.id for sentence in sentences]
    segments = ChapterService.get_segments_by_sentence_ids(sentence_ids)
    # print(segments)

    sentences_data = []
    for sentence in sentences:
        sentence_segments = [segment.serialize(exclude_keys=['sentence_id']) for segment in segments if segment.sentence_id == sentence.id]
        sentences_data.append({
            'chapter_id': chapter_id,
            'id': sentence.id,
            'sentence_id': sentence.sentence_id,  
            'text': sentence.text,
            'segments': sentence_segments
            # 'segment_id': segments.segment_id
        })

    return jsonify(sentences_data), 200

@chapter_blueprint.route('/chapters/<int:chapter_id>/segments', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segment_indices(chapter_id):
    try:
        segment_indices = ChapterService.get_segment_indices_by_chapter(chapter_id)
        if segment_indices:
            return jsonify(segment_indices), 200
        else:
            return jsonify({"message": "No segments found for this chapter"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@chapter_blueprint.route('/delete/<int:chapter_id>', methods=['DELETE'])
@jwt_required()
@measure_response_time
def delete_chapter(chapter_id):
    try:
        # First get the chapter to ensure it exists
        chapter = ChapterService.get_chapters_by_chapter_id(chapter_id)
        if not chapter:
            return jsonify({'message': 'Chapter not found'}), 404

        # Delete all related data in the correct order to maintain referential integrity
        ChapterService.delete_chapter_and_related_data(chapter_id)
        
        return jsonify({'message': 'Chapter and all related content deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
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

# List of recipient emails (adjust as needed)


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
    

@concept_blueprint.route('/check_submission_status/<int:submission_id>', methods=['GET'])
def check_submission_status(submission_id):
    submission = ConceptSubmission.query.get(submission_id)
    if not submission:
        return jsonify({"status": "not_found"}), 404
    
    if submission.status == 'approved':
        concept = ConceptDictionary.query.filter_by(concept_id=submission.concept_id).first()
        if concept:
            return jsonify({
                "status": "approved",
                "concept": {
                    "concept_id": concept.concept_id,
                    "concept_name": concept.concept_label,  # Changed to match frontend expectation
                    "hindi_label": concept.hindi_label,
                    "english_label": concept.english_label,
                    "sanskrit_label": concept.sanskrit_label
                }
            })
    
    return jsonify({
        "status": submission.status,
        "message": "Submission is still pending"
    })
    


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.services.measure_time import measure_response_time
from application.services.construction_service import ConstructionService

construction_blueprint = Blueprint('construction', __name__)


@construction_blueprint.route('/segment/<int:segment_id>/construction', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def manage_construction_by_segment(segment_id):
    data = request.get_json()
    is_finalized = data.get('is_finalized', False)  # Extract is_finalized from request

    if request.method == 'POST':
        construction_entries = ConstructionService.create_construction_by_segment(segment_id, data)
        return jsonify([construction.serialize() for construction in construction_entries]), 201
    elif request.method == 'PUT':
        success = ConstructionService.update_construction_by_segment(segment_id, data.get('constructions', []), is_finalized)
        return ('Update successful', 200) if success else ('No construction data found', 404)


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.services.measure_time import measure_response_time
from application.services.discourse_service import DiscourseService

discourse_blueprint = Blueprint('discourse', __name__)

@discourse_blueprint.route('/segment/<int:segment_id>/discourse', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def manage_discourse_by_segment(segment_id):
    data = request.get_json()
    is_finalized = data.get('is_finalized', False)  # Extract is_finalized from request

    if request.method == 'POST':
        discourse_entries = DiscourseService.create_discourse_by_segment(segment_id, data)
        return jsonify([discourse.serialize() for discourse in discourse_entries]), 201
    elif request.method == 'PUT':
        success = DiscourseService.update_discourse_by_segment(segment_id, data.get('discourse', []), is_finalized)
        return ('Update successful', 200) if success else ('No discourse data found', 404)



from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.services.measure_time import measure_response_time
from application.services.lexical_service import LexicalService

lexical_blueprint = Blueprint('lexicals', __name__)

@lexical_blueprint.route('/segment/<int:segment_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_lexicals_by_segment(segment_id):
    lexicals = LexicalService.get_lexicals_by_segment(segment_id)
    if lexicals:
        return jsonify([lexical.serialize() for lexical in lexicals]), 200
    return jsonify({"message": "No lexical conceptual data found for the given segment_id"}), 404


@lexical_blueprint.route('/segment/<int:segment_id>', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def manage_lexicals_by_segment(segment_id):
    data = request.get_json()
    is_finalized = data.get('is_finalized', False)

    print(f"Received PUT /segment/{segment_id} payload: {data}")

    if request.method == 'POST':
        lexicals = LexicalService.create_lexicals(segment_id, data)
        return jsonify([lexical.serialize() for lexical in lexicals]), 201

    elif request.method == 'PUT':
        success, message = LexicalService.update_lexicals_by_segment(
            segment_id,
            data.get('lexicals', []),
            is_finalized
        )
        if success:
            return jsonify({"message": "Update successful"}), 200
        else:
            return jsonify({"message": "Update failed", "error": message}), 400


@lexical_blueprint.route('/segment/<int:segment_id>/is_concept_generated', methods=['GET'])
@jwt_required()
@measure_response_time
def check_is_concept_generated(segment_id):
    is_generated, column_count = LexicalService.is_concept_generated(segment_id)
    return jsonify({"is_concept_generated": is_generated, "column_count": column_count}), 200



from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
from application.models.notification_model import Notification
from ..extensions import db
from application.models.feedback_model import Feedback
from application.models.user_model import User
from application.controllers.concept_controller import send_email
from application.models.project_model import Project
from application.models.segment_model import Segment
from application.models.chapter_model import Chapter

from sqlalchemy.orm import contains_eager
from sqlalchemy import func


notification_blueprint = Blueprint('notifications', __name__)

@notification_blueprint.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        # Fetch user_id from claims
        claims = get_jwt()
        user_id = claims.get("user_id")

        # Ensure user_id is an integer
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user_id format'}), 400

        # Fetch detailed notifications with related segment, chapter, project info, and error details
        
        notifications = (
            db.session.query(
                Notification.id,
                Notification.user_id,
                Notification.segment_id,
                Notification.message,
                Notification.is_read,
                Notification.created_at,
                Segment.segment_index,
                Segment.chapter_id,
                Chapter.name.label('chapter_name'),
                Chapter.project_id,
                Project.name.label('project_name'),
                func.bool_or(Feedback.has_error).label('has_error'),
                func.string_agg(Feedback.error_details, '; ').label('error_details')
            )
            .join(Segment, Segment.segment_id == Notification.segment_id)
            .join(Chapter, Chapter.id == Segment.chapter_id)
            .join(Project, Project.id == Chapter.project_id)
            .outerjoin(Feedback, Feedback.segment_id == Segment.segment_id)
            .filter(Notification.user_id == user_id)
            .group_by(
                Notification.id,
                Segment.segment_index,
                Segment.chapter_id,
                Chapter.name,
                Chapter.project_id,
                Project.name
            )
            .all()
        )

        # Serialize the response
        notification_list = []
        for notif in notifications:
            notification_list.append({
                "notification_id": notif.id,  # ✅ explicitly include it
                "user_id": notif.user_id,
                "segment_id": notif.segment_id,
                "segment_index": notif.segment_index,
                "chapter_id": notif.chapter_id,
                "chapter_name": notif.chapter_name,
                "project_id": notif.project_id,
                "project_name": notif.project_name,
                "message": notif.message,
                "is_read": notif.is_read,
                "created_at": notif.created_at,
                "has_error": notif.has_error if notif.has_error is not None else False,
                "error_details": notif.error_details if notif.error_details else ""
            })


        return jsonify(notification_list), 200

    except Exception as e:
        print(f"Error in get_notifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500



@notification_blueprint.route('/notifications/read/<int:notification_id>', methods=['PUT'])
@jwt_required()
def mark_notification_as_read(notification_id):
    data = request.get_json()
    comment = data.get('comment', None)

    user_id = get_jwt()["user_id"]

    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    # Mark as read
    notification.is_read = True

    segment_id = notification.segment_id

    # Fetch additional context information
    segment = Segment.query.get(segment_id)
    chapter_name = ""
    project_name = ""
    chapter_id = None

    if segment:
        chapter_id = segment.chapter_id
        chapter = Chapter.query.get(chapter_id)
        if chapter:
            chapter_name = chapter.name
            project = Project.query.get(chapter.project_id)
            if project:
                project_name = project.name

    # Find the reviewer who gave the original feedback
    feedback = Feedback.query.filter_by(segment_id=segment_id).order_by(Feedback.id.desc()).first()

    if feedback:
        reviewer = User.query.get(feedback.user_id)

        if reviewer:
            # Construct the notification message
            reviewer_message = (
                f"The assigned user has reviewed your feedback for Segment {segment.segment_index} "
                f"in Chapter '{chapter_name}' (ID: {chapter_id}) of Project '{project_name}' and left a comment."
            )

            # Check if a similar notification already exists for the reviewer
            existing_notification = (
                Notification.query.filter_by(
                    user_id=reviewer.id,
                    segment_id=segment_id,
                    sender_id=user_id,
                    message=reviewer_message
                ).first()
            )

            # Only send a new notification if a similar one does not already exist
            if not existing_notification:
                # Save notification for the reviewer
                reviewer_notification = Notification(
                    user_id=reviewer.id,
                    sender_id=user_id,
                    segment_id=segment_id,
                    message=reviewer_message
                )
                db.session.add(reviewer_notification)

                # Optional: Send email to the reviewer
                subject = f"Feedback Review for Segment {segment.segment_index}"
                body = (
                    f"Hello {reviewer.username},\n\n"
                    f"The assigned user has reviewed your feedback for Segment {segment.segment_index} in "
                    f"Chapter '{chapter_name}' (ID: {chapter_id}) of Project '{project_name}'.\n\n"
                    f"Comment: {comment}\n\n"
                    "Please check the application for further details.\n\n"
                    "Regards,\nReview Team"
                )
                send_email(subject, body, reviewer.email)

    # Commit the changes
    db.session.commit()

    return jsonify({
        'message': 'Notification marked as read and reviewer notified if applicable',
        'notification': {
            'id': notification.id,
            'segment_id': segment_id,
            'segment_index': segment.segment_index if segment else None,
            'chapter_id': chapter_id,
            'chapter_name': chapter_name,
            'project_name': project_name,
            'comment': comment,
            'is_read': notification.is_read
        }
    }), 200




@notification_blueprint.route('/notifications/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    try:
        user_id = get_jwt()['user_id']
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404

        db.session.delete(notification)
        db.session.commit()
        return jsonify({'message': 'Notification deleted successfully'}), 200
    except Exception as e:
        print(f"Error in delete_notification: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@notification_blueprint.route('/notifications', methods=['DELETE'])
@jwt_required()
def delete_all_notifications():
    try:
        user_id = get_jwt()['user_id']
        notifications = Notification.query.filter_by(user_id=user_id).all()

        if not notifications:
            return jsonify({'message': 'No notifications to delete'}), 200

        for notification in notifications:
            db.session.delete(notification)

        db.session.commit()
        return jsonify({'message': 'All notifications deleted successfully'}), 200
    except Exception as e:
        print(f"Error in delete_all_notifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@notification_blueprint.route('/notifications/unread', methods=['GET'])
@jwt_required()
def get_unread_notifications():
    try:
        # Get user_id from JWT
        user_id = get_jwt()["user_id"]

        # Fetch unread notifications
        unread_notifications = (
            db.session.query(Notification.segment_id)
            .filter_by(user_id=user_id, is_read=False)
            .distinct()  # Only unique segment_ids
            .all()
        )

        # Convert result to flat list of segment_ids
        unread_segment_ids = [row.segment_id for row in unread_notifications]

        return jsonify(unread_segment_ids), 200

    except Exception as e:
        print(f"Error in get_unread_notifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500


from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
from application.services.project_service import ProjectService
from application.services.user_service import UserService
from application.models.user_model import User
from application.models.chapter_model import Chapter
from .decorators import admin_required
from application.extensions import db
from application.models.sentence_model import Sentence
from application.models.segment_model import Segment
from application.services.measure_time import measure_response_time
from application.services.chapter_service import ChapterService
from application.services.segment_service import SegmentService
from application.models.project_model import Project

project_blueprint = Blueprint('projects', __name__)


@project_blueprint.route('/add', methods=['POST'])
@jwt_required()
@measure_response_time
@admin_required
def add_project():
    jwt_claims = get_jwt()

    data = request.get_json()
    project = ProjectService.create_project(
        name=data['name'],
        description=data.get('description', ''),
        language=data['language'],
        owner_id=jwt_claims['user_id']
    )
    return jsonify({'message': 'Project added successfully', 'project_id': project.id}), 201



@project_blueprint.route('/all', methods=['GET'])
@jwt_required()
@measure_response_time
def view_all_projects():
    jwt_data = get_jwt()
    user_id = jwt_data.get('user_id')

    current_user = User.query.get(user_id)
    if not current_user:
        return jsonify({"message": "User not found"}), 404

    # Now filter projects by the user's organization
    projects = Project.query.join(User, Project.owner_id == User.id)\
        .filter(User.organization == current_user.organization).all()

    projects_data = []
    for project in projects:
        total_chapters = Chapter.query.filter_by(project_id=project.id).count()
        total_segments = db.session.query(Segment).join(Sentence).join(Chapter).filter(Chapter.project_id == project.id).count()
        pending_segments = db.session.query(Segment).join(Sentence).join(Chapter).filter(
            Chapter.project_id == project.id,
            Segment.status == 'pending'
        ).count()

        projects_data.append({
            'id': project.id,
            'name': project.name,
            'language': project.language,
            'created_at': project.created_at,
            'total_chapters': total_chapters,
            'total_segments': total_segments,
            'pending_segments': pending_segments
        })

    return jsonify(projects_data), 200

@project_blueprint.route('/by_language/<language>', methods=['GET'])
@jwt_required()
@measure_response_time
def view_projects_by_language(language):
    projects = ProjectService.get_projects_by_language(language)
    projects_data = [{'id': project.id, 'name': project.name} for project in projects]
    return jsonify(projects_data), 200



@project_blueprint.route('/by_user/<int:user_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def view_projects_by_user(user_id):
    projects = ProjectService.get_projects_by_user(user_id)
    projects_data = [{'id': project.id, 'name': project.name, 'description': project.description, 'language': project.language, 'owner_id': project.owner_id} for project in projects]
    return jsonify(projects_data), 200


@project_blueprint.route('/by_organization/<organization>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_projects_by_user_organization(organization):
    projects = ProjectService.get_projects_by_user_organization(organization)
    projects_data = []

    for project in projects:
        total_chapters = Chapter.query.filter_by(project_id=project.id).count()
        projects_data.append({
            'id': project.id,
            'name': project.name,
            'language': project.language,
            'created_at': project.created_at,
            'total_chapters': total_chapters,
            'total_segments': 50,
            'pending_segments': 5
        })

    return jsonify(projects_data), 200


@project_blueprint.route('/<int:project_id>/overview', methods=['GET'])
@jwt_required()
def get_project_overview(project_id):
    """
    Get project overview with chapter count, total segments, completed segments, pending segments,
    and a list of chapter IDs.
    """
    try:
        # Get all chapters for the project
        chapters = ChapterService.get_chapters_by_project(project_id)
        total_chapters = len(chapters)
        
        total_segments = 0
        completed_segments = 0
        chapter_ids = []

        for chapter in chapters:
            chapter_ids.append(chapter.id)
            chapter_segments = SegmentService.get_segments_count_by_chapter(chapter.id)
            completed_chapter_segments = SegmentService.get_completed_segments_count_by_chapter(chapter.id)

            total_segments += chapter_segments
            completed_segments += completed_chapter_segments

        pending_segments = total_segments - completed_segments

        return jsonify({
            'project_id': project_id,
            'total_chapters': total_chapters,
            'chapter_ids': chapter_ids,
            'total_segments': total_segments,
            'completed_segments': completed_segments,
            'pending_segments': pending_segments
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.services.measure_time import measure_response_time
from application.services.relational_service import RelationalService

relational_blueprint = Blueprint('relational', __name__)

@relational_blueprint.route('/segment/<int:segment_id>/relational', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def manage_relational_by_segment(segment_id):
    data = request.get_json()
    is_finalized = data.get('is_finalized', False)  # Extract is_finalized from request

    if request.method == 'POST':
        relational_entries = RelationalService.create_relational_by_segment(segment_id, data)
        return jsonify([relational.serialize() for relational in relational_entries]), 201
    elif request.method == 'PUT':
        success = RelationalService.update_relational_by_segment(segment_id, data.get('relational', []), is_finalized)
        return ('Update successful', 200) if success else ('Failed to update relational data', 400)


from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
from application.extensions import db
from application.models.feedback_model import Feedback
from application.models.notification_model import Notification
from application.models.segment_model import Segment
from application.models.chapter_model import Chapter
from application.models.project_model import Project
from application.models.assignment_model import Assignment
from application.models.user_model import User

reviewer_blueprint = Blueprint('reviewer', __name__)

@reviewer_blueprint.route('/feedback', methods=['GET'])
@jwt_required()
def get_feedback_for_reviewer():
    try:
        # Get the reviewer user ID
        claims = get_jwt()
        reviewer_id = claims.get("user_id")

        # Fetch feedback given by the reviewer
        feedback_query = (
            db.session.query(
                Feedback.id,
                Feedback.segment_id,
                Feedback.has_error,
                Feedback.error_details,
                Feedback.tab_name,
                Feedback.timestamp,
                Segment.segment_index,
                Segment.chapter_id,
                Chapter.name.label('chapter_name'),
                Chapter.project_id,
                Project.name.label('project_name'),
                # Notifications related to this feedback (both assigned user and feedback giver notifications)
                Notification.message.label('notification_message'),
                Notification.is_read,
                Notification.created_at.label('notification_timestamp'),
                Notification.user_id.label('notification_recipient_id'),
                # Get assignment info to see who was assigned
                Assignment.user_id.label('assigned_user_id'),
                User.username.label('assigned_user_name')
            )
            .join(Segment, Segment.segment_id == Feedback.segment_id)
            .join(Chapter, Chapter.id == Segment.chapter_id)
            .join(Project, Project.id == Chapter.project_id)
            .outerjoin(Notification, Notification.segment_id == Feedback.segment_id)
            .outerjoin(Assignment, Assignment.segment_id == Feedback.segment_id)
            .outerjoin(User, User.id == Assignment.user_id)
            .filter(Feedback.user_id == reviewer_id)
            .order_by(Feedback.timestamp.desc())
            .all()
        )

        feedback_list = []
        processed_segments = set()
        
        for feedback in feedback_query:
            if feedback.segment_id in processed_segments:
                continue  # Skip duplicates
                
            processed_segments.add(feedback.segment_id)
            
            # Get all notifications related to this feedback
            notifications = Notification.query.filter_by(segment_id=feedback.segment_id).all()
            
            notification_details = []
            for notif in notifications:
                notification_details.append({
                    "message": notif.message,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at,
                    "recipient_id": notif.user_id,
                    "sender_id": notif.sender_id
                })
            
            feedback_list.append({
                "feedback_id": feedback.id,
                "segment_id": feedback.segment_id,
                "segment_index": feedback.segment_index,
                "chapter_id": feedback.chapter_id,
                "chapter_name": feedback.chapter_name,
                "project_id": feedback.project_id,
                "project_name": feedback.project_name,
                "tab_name": feedback.tab_name,
                "has_error": feedback.has_error,
                "error_details": feedback.error_details,
                "timestamp": feedback.timestamp,
                "assigned_to": {
                    "user_id": feedback.assigned_user_id,
                    "username": feedback.assigned_user_name
                },
                "notifications": notification_details,
                "status": "completed" if any(n.is_read for n in notifications) else "pending"
            })

        return jsonify(feedback_list), 200

    except Exception as e:
        print(f"Error in get_feedback_for_reviewer: {e}")
        return jsonify({"error": "Internal server error"}), 500

@reviewer_blueprint.route('/feedback/<int:feedback_id>', methods=['DELETE'])
@jwt_required()
def delete_feedback(feedback_id):
    try:
        claims = get_jwt()
        current_user_id = claims.get("user_id")  # Correct way if using additional_claims

        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            return jsonify({"error": "Feedback not found"}), 404

        if feedback.user_id != current_user_id:
            return jsonify({"error": "You are not authorized to delete this feedback"}), 403

        db.session.delete(feedback)
        db.session.commit()

        return jsonify({"message": "Feedback deleted successfully"}), 200

    except Exception as e:
        print(f"Error deleting feedback: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
    
import csv
import io
import os
import tempfile
from application.models.construction_model import Construction
from application.models.lexical_conceptual_model import LexicalConceptual
from application.models.discourse_model import Discourse
from application.models.relational_model import Relational
from application.extensions import db
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, jwt_required
from application.models.sentence_model import Sentence
from application.models.assignment_model import Assignment
from application.services.measure_time import measure_response_time
from application.services.segment_service import SegmentService
from application.models.segment_model import Segment
from application.models.chapter_model import Chapter
from application.models.feedback_model import Feedback
from application.models.user_model import User
from application.controllers.concept_controller import send_email
from application.models.notification_model import Notification
from application.models.project_model import Project

segment_blueprint = Blueprint('segments', __name__)

@segment_blueprint.route('/convert_to_wx/format', methods=['POST'])
@jwt_required()
@measure_response_time
def get_wx_format():
    data = request.json
    
    if 'text' not in data or not isinstance(data['text'], list):
        return jsonify({'error': "'text' must be a list of sentences"}), 400
    
    input_texts = data['text']
    results = [SegmentService.text_to_wx(text) for text in input_texts]

    return jsonify({'wx_formats': results})


@segment_blueprint.route('/<int:segment_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
@measure_response_time
def segment(segment_id):
    if request.method == 'GET':
        segment = SegmentService.get_segment_by_id(segment_id)
        return jsonify(segment.serialize()) if segment else ('', 404)

    elif request.method == 'PUT':
        data = request.get_json()
        segment = SegmentService.update_segment(segment_id, data)
        return jsonify(segment.serialize()) if segment else ('', 404)

    elif request.method == 'DELETE':
        try:
            result = SegmentService.delete_segment(segment_id)
            return ('segment deleted', 204) if result else ('Segment not found', 404)
        except Exception as e:
            print(f"Error during DELETE: {e}")  # Log the actual error
            
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
        
@segment_blueprint.route('/by_chapter/<int:chapter_id>', methods=['GET'])
def get_segments_by_chapter_details(chapter_id):
    segments = Segment.query.filter_by(chapter_id=chapter_id).all()
    result = [
        {
            'segment_index': segment.segment_index,
            'segment_text': segment.segment_text,
            'english_text': segment.english_text,
            'wx_text': segment.wx_text
        }
        for segment in segments
    ]
    return jsonify(result)

@segment_blueprint.route('/segments/by_chapter/<int:chapter_id>', methods=['GET'])
def get_segments_sentences_by_chapter(chapter_id):
    segments = Segment.query.filter_by(chapter_id=chapter_id).all()

    # Find the project_id from the chapter
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"error": "Chapter not found"}), 404

    project_id = chapter.project_id

    sentences = []
    for segment in segments:
        sentences.append({
            "project_id": str(project_id),
            "sentence_id": str(segment.segment_index),
            "sentence": segment.segment_text
        })

    return jsonify({"sentences": sentences})

@segment_blueprint.route('/', methods=['POST'])
@jwt_required()
@measure_response_time
def create_segment():
    """
    Create a new segment with required fields.
    """
    data = request.get_json()
    
    # Ensure required fields are present
    required_fields = ['sentence_id', 'segment_index', 'segment_text', 'chapter_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
    
    # Set default values for optional fields
    data.setdefault('segment_type', 'default_type')
    data.setdefault('index_type', 'default_index_type')
    data.setdefault('english_text', '')
    data.setdefault('wx_text', '')
    
    try:
        segment = SegmentService.create_segment(data)
        return jsonify(segment.serialize()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@segment_blueprint.route('/sentence/<int:sentence_id>', methods=['POST', 'PUT'])
@jwt_required()
@measure_response_time
def segments_by_sentence(sentence_id):
    """
    Create or update multiple segments for a sentence.
    """
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({'error': 'Data should be a list of segment objects'}), 400

    # Extract chapter_id from the first segment (assuming all segments have the same chapter_id)
    chapter_id = data[0].get('chapter_id')

    if request.method == 'POST':
        segments = SegmentService.create_segments(sentence_id, chapter_id, data)
        return jsonify([s.serialize() for s in segments]), 201

    elif request.method == 'PUT':
        updated_segments = []
        for segment_data in data:
            segment_id = segment_data.get('segment_id')
            if segment_id:
                updated_segment = SegmentService.update_segment(segment_id, segment_data)
                if updated_segment:
                    updated_segments.append(updated_segment.serialize())

        return jsonify(updated_segments) if updated_segments else ('No segments found', 404)


@segment_blueprint.route('/segments', methods=['PUT'])
@jwt_required()
@measure_response_time
def update_segments():
    """
    Update multiple segments using segment_id.
    """
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({'error': 'Data should be a list of segment objects'}), 400

    updated_segments = []
    for segment_data in data:
        segment_id = segment_data.get('segment_id')
        if segment_id:
            updated_segment = SegmentService.update_segment(segment_id, segment_data)
            if updated_segment:
                updated_segments.append(updated_segment.serialize())

    return jsonify(updated_segments) if updated_segments else ('No segments found', 404)



@segment_blueprint.route('/<int:chapter_id>/segment_count', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segments_count(chapter_id):
    """
    Get the total number of segments in a chapter and the number of fully completed ones.
    """
    try:
        total_segments = SegmentService.get_segments_count_by_chapter(chapter_id)
        completed_segments = SegmentService.get_completed_segments_count_by_chapter(chapter_id)

        return jsonify({
            'chapter_id': chapter_id,
            'total_segments': total_segments,
            'completed_segments': completed_segments
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@segment_blueprint.route('/upload_segments', methods=['POST'])
@jwt_required()
@measure_response_time
def upload_segments():
    """
    Upload multiple segments from a text file.
    Expects multipart form data with:
    - file: the text file to upload
    - chapter_id: the chapter id as a form field
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Missing file'}), 400

    file = request.files['file']
    chapter_id = request.form.get('chapter_id')  # Read from form field

    if not chapter_id:
        return jsonify({'error': 'Missing chapter_id in form data'}), 400

    try:
        chapter_id = int(chapter_id)
    except ValueError:
        return jsonify({'error': 'Invalid chapter_id, must be an integer'}), 400

    file_format = file.filename.split('.')[-1].lower()

    if file_format != 'txt':
        return jsonify({'error': 'Unsupported file format. Only TXT is allowed.'}), 400

    segments_data = []

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        lines = stream.readlines()

        for line in lines:
            parts = line.strip().split("\t")  # Split by tab

            if len(parts) < 2:
                print(f"Skipping invalid line: {line}")
                continue

            segment_index = parts[0]
            segment_text = parts[1]
            wx_text = parts[2] if len(parts) > 2 else None
            english_text = parts[3] if len(parts) > 3 else None

            # Extract sentence_id from segment_index by stripping trailing letters
            extracted_sentence_id = re.sub(r'[a-zA-Z]+$', '', segment_index)

            # Query sentence filtering by sentence_id and chapter_id from form data
            sentence = db.session.query(Sentence).filter(
                Sentence.sentence_id == extracted_sentence_id,
                Sentence.chapter_id == chapter_id
            ).first()

            if not sentence:
                print(f"Sentence with id {extracted_sentence_id} not found in chapter {chapter_id}.")
                continue

            segments_data.append({
                'sentence_id': sentence.id,
                'segment_index': segment_index,
                'segment_text': segment_text,
                'wx_text': wx_text,
                'english_text': english_text,
                'chapter_id': sentence.chapter_id,
                'segment_type': " ",
                'index_type': "type",
            })

        if not segments_data:
            return jsonify({'error': 'No valid segments found to insert'}), 400

        # Bulk insert segments
        created_segments = SegmentService.create_segments_bulk(segments_data)

        return jsonify({'message': f'{len(created_segments)} segments uploaded successfully'}), 201

    except Exception as e:
        print(f"Exception during segment upload: {e}")
        return jsonify({'error': str(e)}), 500



@segment_blueprint.route('/upload_usr', methods=['POST'])
@jwt_required()
@measure_response_time
def upload_usr():
    if 'file' not in request.files:
        return jsonify({'error': 'Missing file'}), 400

    file = request.files['file']
    if file.filename.split('.')[-1].lower() != 'txt':
        return jsonify({'error': 'Unsupported file format. Only TXT is allowed.'}), 400

    chapter_id = request.form.get('chapter_id')
    if not chapter_id:
        return jsonify({'error': 'Chapter ID is required'}), 400

    try:
        chapter_id = int(chapter_id)
    except ValueError:
        return jsonify({'error': 'Chapter ID must be an integer'}), 400

    try:
        # Create a temporary file in binary mode
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            # Save the file directly (it's already in bytes)
            file.save(temp_file)
            temp_file_path = temp_file.name

        try:
            # Parse the data with explicit encoding
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                data = parse_usr_file(f)

            # Verify chapter exists
            chapter = db.session.query(Chapter).filter(Chapter.id == chapter_id).first()
            if not chapter:
                return jsonify({'error': f'Chapter with ID {chapter_id} not found'}), 404

            # Start transaction
            try:
                lexical_count = insert_lexical_concepts(db.session, data, chapter_id)
                relational_count = insert_relational_data(db.session, data, chapter_id)
                construction_count = insert_construction_data(db.session, data, chapter_id)
                discourse_count = insert_discourse_data(db.session, data, chapter_id)
                
                db.session.commit()

                return jsonify({
                    'message': 'USR data uploaded successfully',
                    'counts': {
                        'lexical_concepts': lexical_count,
                        'relational_data': relational_count,
                        'constructions': construction_count,
                        'discourse': discourse_count
                    }
                }), 201

            except Exception as e:
                db.session.rollback()
                return jsonify({'error': f'Database error: {str(e)}'}), 500

        finally:
            os.unlink(temp_file_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def parse_usr_file(file_obj):
    """Parse USR file and return structured data
    Args:
        file_obj: A file-like object or file path (maintains backward compatibility)
    """
    lexical_concepts = []
    relational_data = []
    constructions = []
    discourses = []
    current_segment_id = None

    # Handle both file paths and file objects
    if isinstance(file_obj, str):
        # Backward compatibility - treat as file path
        with open(file_obj, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        # Assume it's a file-like object
        lines = file_obj.readlines() if hasattr(file_obj, 'readlines') else [line for line in file_obj]

    for line in lines:
        line = line.strip()
        
        # Handle segment ID markers
        if line.startswith("<sent_id=") or line.startswith("<segment_id="):
            match = re.search(r'<(?:sent_id|segment_id)\s*=\s*([\w_\-]+)>', line)
            if match:
                current_segment_id = match.group(1)
            else:
                current_segment_id = None
        elif line.startswith("</sent_id>") or line.startswith("</segment_id>"):
            current_segment_id = None
        elif line.startswith("#") or line.startswith("%") or line.startswith("*"):
            continue  # Skip comments and markers
        elif line and current_segment_id is not None:
            parts = re.split(r'\s+', line)
            
            # Parse lexical concepts (minimum 7 parts)
            if len(parts) >= 7:
                concept = parts[0] if len(parts) > 0 else None
                index = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                semantic_category = parts[2] if len(parts) > 2 else None
                morpho_semantics = parts[3] if len(parts) > 3 else None
                speakers_view = parts[6] if len(parts) > 6 else None

                if concept and index is not None:
                    lexical_concepts.append({
                        'segment_id': current_segment_id,
                        'index': index,
                        'concept': concept,
                        'semantic_category': semantic_category,
                        'morpho_semantics': morpho_semantics,
                        'speakers_view': speakers_view
                    })

            # Parse relational data (minimum 5 parts)
            if len(parts) >= 5:
                try:
                    index = int(parts[1])
                    head_relation = parts[4]
                    
                    if ':' in parts[4]:
                        head_index, dep_relation = parts[4].split(':', 1)
                        head_index = head_index.strip() if head_index.strip().isdigit() else "-"
                        dep_relation = dep_relation.strip()
                    else:
                        head_index = "-"
                        dep_relation = "-"

                    is_main = head_relation.strip() == "0:main"
                    
                    relational_data.append({
                        'segment_id': current_segment_id,
                        'index': index,
                        'head_relation': head_relation,
                        'head_index': head_index,
                        'dep_relation': dep_relation,
                        'is_main': is_main
                    })
                except (ValueError, IndexError):
                    pass

            # Parse constructions (minimum 9 parts)
            if len(parts) >= 9:
                try:
                    index = int(parts[1])
                    construction = parts[8]

                    if ':' in construction:
                        cxn_index, component_type = construction.split(':', 1)
                    else:
                        cxn_index = "-"
                        component_type = "-"

                    constructions.append({
                        'segment_id': current_segment_id,
                        'index': index,
                        'cxn_index': cxn_index.strip(),
                        'component_type': component_type.strip(),
                        'construction': construction
                    })
                except (ValueError, IndexError):
                    pass

            # Parse discourse (minimum 6 parts)
            if len(parts) >= 6:
                try:
                    index = int(parts[1])
                    discourse = parts[5]

                    if ':' in discourse:
                        head_index, relation = discourse.split(':', 1)
                    else:
                        head_index = "-"
                        relation = "-"

                    discourses.append({
                        'segment_id': current_segment_id,
                        'index': index,
                        'head_index': head_index.strip(),
                        'relation': relation.strip(),
                        'discourse': discourse
                    })
                except (ValueError, IndexError):
                    pass

    return {
        'lexical_concepts': lexical_concepts,
        'relational_data': relational_data,
        'constructions': constructions,
        'discourses': discourses
    }


def insert_lexical_concepts(session, data, chapter_id):
    count = 0
    for segment_data in data['lexical_concepts']:
        segment = session.query(Segment).join(Sentence).filter(
            Segment.segment_index == segment_data['segment_id'],
            Sentence.chapter_id == chapter_id
        ).first()

        if segment:
            existing_lexical_concept = session.query(LexicalConceptual).filter_by(
                segment_id=segment.segment_id,
                segment_index=segment_data['segment_id'],
                index=segment_data['index']
            ).first()

            if not existing_lexical_concept:
                lexical_concept = LexicalConceptual(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id'],
                    index=segment_data['index'],
                    concept=segment_data['concept'],
                    semantic_category=segment_data['semantic_category'],
                    morpho_semantics=segment_data['morpho_semantics'],
                    speakers_view=segment_data['speakers_view']
                )
                session.add(lexical_concept)
                count += 1
    return count


def insert_relational_data(session, data, chapter_id):
    count = 0
    for segment_data in data['relational_data']:
        segment = session.query(Segment).join(Sentence).filter(
            Segment.segment_index == segment_data['segment_id'],
            Sentence.chapter_id == chapter_id
        ).first()
        
        if segment:
            lexical_concept = session.query(LexicalConceptual).filter_by(
                segment_id=segment.segment_id,
                index=segment_data['index']
            ).first()

            concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

            existing_relational_entry = session.query(Relational).filter_by(
                segment_id=segment.segment_id,
                segment_index=segment_data['segment_id'],
                index=segment_data['index']
            ).first()

            if not existing_relational_entry:
                relational_entry = Relational(
                    segment_id=segment.segment_id,
                    segment_index=segment_data['segment_id'],
                    index=segment_data['index'],
                    head_index=segment_data['head_index'],
                    dep_relation=segment_data['dep_relation'],
                    head_relation=segment_data['head_relation'],
                    is_main=segment_data['is_main'],
                    concept_id=concept_id
                )
                session.add(relational_entry)
                count += 1
    return count


def insert_construction_data(session, data, chapter_id):
    count = 0
    for construction_data_item in data['constructions']:
        segment = session.query(Segment).join(Sentence).filter(
            Segment.segment_index == construction_data_item['segment_id'],
            Sentence.chapter_id == chapter_id
        ).first()
        
        if segment:
            lexical_concept = session.query(LexicalConceptual).filter_by(
                segment_id=segment.segment_id,
                index=construction_data_item['index']
            ).first()

            concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

            existing_construction_entry = session.query(Construction).filter_by(
                segment_id=segment.segment_id,
                segment_index=construction_data_item['segment_id'],
                index=construction_data_item['index']
            ).first()

            if not existing_construction_entry:
                construction = Construction(
                    segment_id=segment.segment_id,
                    segment_index=construction_data_item['segment_id'],
                    index=construction_data_item['index'],
                    cxn_index=construction_data_item['cxn_index'],
                    component_type=construction_data_item['component_type'],
                    concept_id=concept_id,
                    construction=construction_data_item['construction']
                )
                session.add(construction)
                count += 1
    return count


def insert_discourse_data(session, data, chapter_id):
    count = 0
    for discourse_data_item in data['discourses']:
        segment = session.query(Segment).join(Sentence).filter(
            Segment.segment_index == discourse_data_item['segment_id'],
            Sentence.chapter_id == chapter_id
        ).first()

        if segment:
            lexical_concept = session.query(LexicalConceptual).filter_by(
                segment_id=segment.segment_id,
                index=discourse_data_item['index']
            ).first()

            concept_id = lexical_concept.lexical_conceptual_id if lexical_concept else None

            existing_discourse_entry = session.query(Discourse).filter_by(
                segment_id=segment.segment_id,
                segment_index=discourse_data_item['segment_id'],
                index=discourse_data_item['index']
            ).first()

            if not existing_discourse_entry:
                discourse = Discourse(
                    segment_id=segment.segment_id,
                    segment_index=discourse_data_item['segment_id'],
                    index=discourse_data_item['index'],
                    head_index=discourse_data_item['head_index'],
                    relation=discourse_data_item['relation'],
                    concept_id=concept_id,
                    discourse=discourse_data_item['discourse']
                )
                session.add(discourse)
                count += 1
    return count




@segment_blueprint.route('/assign_user', methods=['POST'])
@jwt_required()
def assign_user_to_segment():
    """
    API to assign a user to a specific tab of a segment.
    Sends email notification to the assigned user with segment details.
    """
    data = request.get_json()
    
    user_id = data.get('user_id')
    segment_id = data.get('segment_id')
    tab_name = data.get('tab_name')  # e.g., 'lexical_conceptual'

    if not all([user_id, segment_id, tab_name]):
        return jsonify({'error': 'user_id, segment_id, and tab_name are required'}), 400

    # Get user details
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get segment details
    segment = Segment.query.get(segment_id)
    if not segment:
        return jsonify({'error': 'Segment not found'}), 404

    # Get chapter details
    chapter = Chapter.query.get(segment.chapter_id)
    if not chapter:
        return jsonify({'error': 'Chapter not found'}), 404

    # Assign user to segment
    result = SegmentService.assign_user_to_tab(user_id, segment_id, tab_name)
    
    if isinstance(result, Assignment):
        # Prepare email content
        subject = f"New Assignment: {tab_name.replace('_', ' ').title()} Task"
        body = (
            f"Dear {user.username},\n\n"
            f"You have been assigned to work on the following segment:\n\n"
            f"Chapter: {chapter.name} (ID: {chapter.id})\n"
            f"Segment ID: {segment.segment_id}\n"
            f"Segment Index: {segment.segment_index}\n"
            f"Tab: {tab_name.replace('_', ' ').title()}\n"
            f"Segment Text: {segment.segment_text}\n\n"
            f"Please log in to the system to begin your work.\n\n"
            f"Best regards,\n"
            f"The Assignment Team"
        )

        # Send email notification
        try:
            send_email(subject, body, user.email)
            
            # # Create in-app notification
            # notification = Notification(
            #     user_id=user_id,
            #     segment_id=segment_id,
            #     message=f"You've been assigned to segment {segment.segment_index} for {tab_name.replace('_', ' ')}"
            # )
            # db.session.add(notification)
            # db.session.commit()
            
        except Exception as e:
            print(f"Failed to send notification: {e}")
            # Don't fail the whole operation if notification fails
            pass

        return jsonify({
            'assignment': result.serialize(),
            'message': 'User assigned successfully and notification sent'
        }), 201
    else:
        return jsonify({
            'status': 'failure',
            'error': result.get('error'),
            'details': result.get('details')
        }), 400

@segment_blueprint.route('/assign_user_bulk', methods=['POST'])
@jwt_required()
def assign_user_to_multiple_tabs():
    """
    API to assign a user to multiple segments and multiple tabs in one request.
    Sends a single email covering all assignments.
    """
    data = request.get_json()
    
    user_id = data.get('user_id')
    segments_data = data.get('segments')

    if not user_id or not segments_data or not isinstance(segments_data, list):
        return jsonify({
            'error': 'Payload must include user_id and segments (list).'
        }), 400

    # Get user details once
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    all_results = []
    all_assignments = []
    segment_summaries = []

    try:
        for segment_item in segments_data:
            segment_id = segment_item.get('segment_id')
            tab_names = segment_item.get('tab_names')

            if not segment_id or not tab_names or not isinstance(tab_names, list):
                all_results.append({
                    'segment_id': segment_id,
                    'status': 'failed',
                    'error': 'segment_id and tab_names (list) are required.'
                })
                continue

            segment = Segment.query.get(segment_id)
            if not segment:
                all_results.append({
                    'segment_id': segment_id,
                    'status': 'failed',
                    'error': 'Segment not found.'
                })
                continue

            chapter = Chapter.query.get(segment.chapter_id)
            if not chapter:
                all_results.append({
                    'segment_id': segment_id,
                    'status': 'failed',
                    'error': 'Chapter not found.'
                })
                continue

            segment_results = []
            for tab_name in tab_names:
                result = SegmentService.assign_user_to_tab(user_id, segment_id, tab_name)
                
                if isinstance(result, Assignment):
                    all_assignments.append(result)
                    segment_results.append({
                        'tab_name': tab_name,
                        'status': 'success'
                    })
                else:
                    segment_results.append({
                        'tab_name': tab_name,
                        'status': 'failed',
                        'error': result.get('error')
                    })

            all_results.append({
                'segment_id': segment_id,
                'chapter_name': chapter.name,
                'segment_index': segment.segment_index,
                'results': segment_results
            })

            segment_summaries.append({
                'chapter_name': chapter.name,
                'chapter_id': chapter.id,
                'segment_id': segment.segment_id,
                'segment_index': segment.segment_index,
                'tab_names': tab_names,
                'segment_text': segment.segment_text
            })

        # Send single email summarizing all assignments
        if all_assignments:
            email_body = f"Dear {user.username},\n\n"
            email_body += f"You have been assigned to the following segments and tabs:\n\n"

            for s in segment_summaries:
                tab_list = ", ".join([t.replace('_', ' ').title() for t in s['tab_names']])
                email_body += (
                    f"Chapter: {s['chapter_name']} (ID: {s['chapter_id']})\n"
                    f"Segment ID: {s['segment_id']}\n"
                    f"Segment Index: {s['segment_index']}\n"
                    f"Tabs: {tab_list}\n"
                    f"Segment Text: {s['segment_text']}\n\n"
                )

            email_body += (
                f"Please log in to the system to begin your work.\n\n"
                f"Best regards,\n"
                f"The Assignment Team"
            )

            subject = f"New Assignments Across {len(segment_summaries)} Segments"
            try:
                send_email(subject, email_body, user.email)
            except Exception as e:
                print(f"Failed to send email notification: {e}")

        return jsonify({
            'results': all_results,
            'message': f"User assigned to {len(all_assignments)} tabs across {len(segment_summaries)} segments successfully."
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
   
        
@segment_blueprint.route('/assigned_users/<int:segment_id>/<string:tab_name>', methods=['GET'])
@jwt_required()
def get_assigned_users(segment_id, tab_name):
    """
    API to fetch users assigned to a specific tab of a segment.
    """
    users = SegmentService.get_assigned_users(segment_id, tab_name)
    return jsonify(users), 200


@segment_blueprint.route('/assigned_users_username/<int:segment_id>/<string:tab_name>', methods=['GET'])
def get_assigned_users_username(segment_id, tab_name):
    """
    API to fetch users assigned to a specific tab of a segment.
    """
    users = SegmentService.get_assigned_users(segment_id, tab_name)
    return jsonify(users), 200



@segment_blueprint.route('/segments/<int:chapter_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segments_by_chapter(chapter_id):
    """
    Fetch segment IDs along with segment indexes for a given chapter ID.
    """
    try:
        segments = Segment.query.filter_by(chapter_id=chapter_id).all()
        result = [{'segment_id': segment.segment_id, 'segment_index': segment.segment_index} for segment in segments]
        return jsonify({'chapter_id': chapter_id, 'segments': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@segment_blueprint.route('/segment/finalized-status/<int:segment_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def fetch_is_finalized(segment_id):
    """
    Fetch `isFinalized` status for all related tables based on segment_id.
    """
    try:
        status = SegmentService.get_is_finalized_status(segment_id)
        return jsonify({"success": True, "data": status}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@segment_blueprint.route('/<int:chapter_id>/finalized_counts', methods=['GET'])
@jwt_required()
@measure_response_time
def get_finalized_counts(chapter_id):
    """
    Get the count of finalized lexical, relational, construction, and discourse segments for a chapter,
    including the chapter name, the count of fully finalized segments, and pending segments.
    """
    try:
        counts = SegmentService.get_finalized_counts_by_chapter(chapter_id)
        return jsonify({
            'chapter_id': chapter_id,
            'chapter_name': counts["chapter_name"],
            'total_segments': counts["total_segments"],
            'lexical_finalized': counts["lexical_finalized"],
            'relational_finalized': counts["relational_finalized"],
            'construction_finalized': counts["construction_finalized"],
            'discourse_finalized': counts["discourse_finalized"],
            'fully_finalized': counts["fully_finalized"],
            'pending_segments': counts["pending_segments"]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@segment_blueprint.route('/by_sentences/<int:sentence_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segments_by_sentence_id(sentence_id):
    """
    Get all segments for a given sentence ID.
    """
    try:
        segments = Segment.query.filter_by(sentence_id=sentence_id).all()
        if not segments:
            return jsonify({'message': 'No segments found for this sentence_id'}), 404

        return jsonify([segment.serialize() for segment in segments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@segment_blueprint.route('/segments/<int:segment_id>/feedback', methods=['POST', 'GET'])
@jwt_required()
@measure_response_time
def segment_feedback(segment_id):
    if request.method == 'POST':
        data = request.get_json()
        user_id = data.get('user_id')
        concept_index = data.get('concept_index') 
        has_error = data.get('has_error', False)
        error_details = data.get('error_details', '')
        tab_name = data.get('tab_name')

        # Log basic feedback input
        print(f"[FEEDBACK] user_id={user_id}, segment_id={segment_id}, concept_index={concept_index}, has_error={has_error}, tab_name={tab_name}")

        # Check if segment exists
        segment = Segment.query.get(segment_id)
        if not segment:
            print(f"[ERROR] Segment {segment_id} not found.")
            return jsonify({'error': 'Segment not found'}), 404

        # Extract chapter_id and segment_index
        chapter_id = segment.chapter_id
        segment_index = segment.segment_index

        # Save feedback
        feedback = Feedback(
            segment_id=segment_id,
            user_id=user_id,
            concept_index=concept_index,
            has_error=has_error,
            error_details=error_details,
            tab_name=tab_name
        )
        db.session.add(feedback)
        db.session.commit()
        print(f"[SUCCESS] Feedback saved for segment {segment_id}")

        # Fetch related entities
        assignment = Assignment.query.filter_by(segment_id=segment_id).first()
        feedback_giver = User.query.get(user_id)
        chapter = Chapter.query.get(chapter_id)
        project = Project.query.get(chapter.project_id) if chapter else None

        # Notify assigned user
        if assignment:
            assigned_user = User.query.get(assignment.user_id)

            if assigned_user:
                try:
                    assigned_user_message = (
                        f"New feedback received for Segment {segment_index} ({segment_id}) "
                        f"(Concept {concept_index}) in {tab_name} from {feedback_giver.username}."
                    )

                    # Check if a similar notification already exists (not marked as read)
                    
                    existing_notification = Notification.query.filter_by(
                        user_id=assigned_user.id,
                        segment_id=segment_id,
                        sender_id=user_id,
                        message=assigned_user_message,
                        is_read=False
                    ).first()

                    if not existing_notification:
                        # Create a new notification if none exists
                        notification = Notification(
                            user_id=assigned_user.id,
                            segment_id=segment_id,
                            message=assigned_user_message,
                            sender_id=user_id
                        )
                        db.session.add(notification)
                    else:
                        # Optionally, you could update created_at to "refresh" the notification timestamp
                        existing_notification.created_at = db.func.now()


                    # Notify the feedback giver too
                    feedback_giver_message = (
                        f"You gave feedback for Segment {segment_index} ({segment_id}) "
                        f"in {tab_name} of chapter '{chapter.name if chapter else 'N/A'}' "
                        f"in project '{project.name if project else 'N/A'}'."
                    )
                    feedback_giver_notification = Notification(
                        user_id=user_id,
                        segment_id=segment_id,
                        message=feedback_giver_message
                    )
                    db.session.add(feedback_giver_notification)

                    db.session.commit()
                    print(f"[NOTIFICATION] Sent to assigned_user_id={assigned_user.id} and feedback_giver_id={user_id}")
                except Exception as notif_err:
                    print(f"[ERROR] Failed to create notifications: {notif_err}")

                # Send email to the assigned user
                try:
                    if assigned_user.email:
                        subject = f"New Feedback for Segment {segment_index}"
                        body = (
                            f"Hello {assigned_user.username},\n\n"
                            f"You have received new feedback from {feedback_giver.username} for:\n"
                            f"- Project: {project.name if project else 'N/A'}\n"
                            f"- Chapter: {chapter.name if chapter else 'N/A'}\n"
                            f"- Segment Index: {segment_index}\n"
                            f"- Tab: {tab_name}\n"
                            f"- Has Error: {'Yes' if has_error else 'No'}\n"
                            f"- Details: {error_details}\n\n"
                            "Please review the feedback at your earliest convenience.\n\n"
                            "Regards,\nThe Review Team"
                        )
                        send_email(subject, body, assigned_user.email)
                        print(f"[EMAIL] Sent to {assigned_user.email}")
                except Exception as email_err:
                    print(f"[ERROR] Email sending failed: {email_err}")
            else:
                print(f"[WARNING] No assigned user found for assignment.user_id={assignment.user_id}")
        else:
            print(f"[INFO] No assignment found for segment_id={segment_id}")

        return jsonify(feedback.serialize()), 201

    elif request.method == 'GET':
        feedbacks = Feedback.query.filter_by(segment_id=segment_id).all()
        return jsonify([feedback.serialize() for feedback in feedbacks]), 200





@segment_blueprint.route('/<int:segment_id>/feedback/concept_indexes', methods=['GET'])
@jwt_required()
def get_segment_feedback_concept_indexes(segment_id):
    """
    Get all concept indexes that have received feedback for a specific segment.
    
    Returns:
        JSON response with:
        - segment_id: The ID of the segment
        - concept_indexes: List of unique concept indexes with feedback
        - count: Number of unique concept indexes with feedback
    """
    # Check if segment exists first
    segment = Segment.query.get(segment_id)
    if not segment:
        return jsonify({'error': 'Segment not found'}), 404
    
    # Query for distinct concept indexes with feedback for this segment
    feedback_indexes = db.session.query(Feedback.concept_index)\
        .filter(Feedback.segment_id == segment_id,
                Feedback.concept_index.isnot(None))\
        .distinct()\
        .all()
    
    # Extract the indexes from the query result
    concept_indexes = [index[0] for index in feedback_indexes]
    
    return jsonify({
        'segment_id': segment_id,
        'concept_indexes': concept_indexes,
        'count': len(concept_indexes)
    }), 200
    

    
@segment_blueprint.route('/chapter/<int:chapter_id>/reassign', methods=['POST'])
@jwt_required()
@measure_response_time
def reassign_chapter_segments(chapter_id):
    """
    Delete current assignments for segments in a chapter and create new assignments.
    Request body should contain:
    {
        "assignments": [
            {
                "segment_id": 1,
                "user_id": 1,
                "tab_name": "lexical_conceptual"
            },
            ...
        ]
    }
    """
    try:
        # Verify chapter exists
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return jsonify({'error': 'Chapter not found'}), 404

        data = request.get_json()
        if not data or 'assignments' not in data:
            return jsonify({'error': 'Missing assignments data'}), 400

        new_assignments = data['assignments']
        if not isinstance(new_assignments, list):
            return jsonify({'error': 'Assignments must be a list'}), 400

        # Get all segments in the chapter
        segments = Segment.query.filter_by(chapter_id=chapter_id).all()
        segment_ids = [segment.segment_id for segment in segments]

        # Start transaction
        db.session.begin()

        # 1. Delete existing assignments for these segments
        Assignment.query.filter(Assignment.segment_id.in_(segment_ids)).delete()

        # 2. Create new assignments
        created_assignments = []
        for assignment_data in new_assignments:
            # Validate required fields
            if not all(k in assignment_data for k in ['segment_id', 'user_id', 'tab_name']):
                db.session.rollback()
                return jsonify({'error': 'Each assignment must have segment_id, user_id and tab_name'}), 400

            # Verify segment belongs to chapter
            if assignment_data['segment_id'] not in segment_ids:
                db.session.rollback()
                return jsonify({'error': f"Segment {assignment_data['segment_id']} not found in chapter"}), 400

            # Verify user exists
            user = User.query.get(assignment_data['user_id'])
            if not user:
                db.session.rollback()
                return jsonify({'error': f"User {assignment_data['user_id']} not found"}), 400

            # Create assignment
            assignment = Assignment(
                segment_id=assignment_data['segment_id'],
                user_id=assignment_data['user_id'],
                tab_name=assignment_data['tab_name']
            )
            db.session.add(assignment)
            created_assignments.append(assignment)

        # Commit transaction
        db.session.commit()

        # Prepare response
        result = [{
            'assignment_id': a.id,
            'segment_id': a.segment_id,
            'user_id': a.user_id,
            'tab_name': a.tab_name
        } for a in created_assignments]

        return jsonify({
            'message': 'Successfully reassigned segments',
            'chapter_id': chapter_id,
            'new_assignments': result,
            'count': len(result)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@segment_blueprint.route('/chapter/<int:chapter_id>/assigned_segments', methods=['GET'])
@jwt_required()
@measure_response_time
def get_assigned_segments_by_chapter(chapter_id):
    """
    Get all segments with assignments for a given chapter.
    Returns segments grouped by segment_id with their assignments.
    """
    try:
        # Verify chapter exists
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return jsonify({'error': 'Chapter not found'}), 404

        # Get all segments for the chapter
        segments = Segment.query.filter_by(chapter_id=chapter_id).all()
        
        if not segments:
            return jsonify({
                'chapter_id': chapter_id,
                'assigned_segments': [],
                'count': 0,
                'message': 'No segments found in this chapter'
            }), 200

        # Get assignments for these segments
        segment_ids = [s.segment_id for s in segments]
        assignments = db.session.query(Assignment, User)\
            .join(User, User.id == Assignment.user_id)\
            .filter(Assignment.segment_id.in_(segment_ids))\
            .all()

        # Group assignments by segment
        segments_data = []
        for segment in segments:
            segment_assignments = [
                {
                    'tab_name': a.tab_name,
                    'username': u.username
                }
                for a, u in assignments 
                if a.segment_id == segment.segment_id
            ]
            
            segments_data.append({
                'segment_id': segment.segment_id,
                'assignments': segment_assignments
            })

        return jsonify({
            'chapter_id': chapter_id,
            'assigned_segments': segments_data,
            'count': len(segments_data)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@segment_blueprint.route('/assignments/user/<int:user_id>', methods=['DELETE'])
@jwt_required()
@measure_response_time
def delete_user_assignments(user_id):
    """
    Delete all assignments for a specific user.
    Only allowed for admins.
    """
    try:
        # Get JWT claims
        jwt_claims = get_jwt()
        
        # Check admin permissions - using same pattern as other endpoints
        if 'role' not in jwt_claims or 'Admin' not in jwt_claims['role']:
            return jsonify({"error": "Permission denied. Only admins can delete assignments."}), 403

        # Check user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": f"User {user_id} not found."}), 404

        # Find all assignments for user
        assignments = Assignment.query.filter_by(user_id=user_id).all()
        if not assignments:
            return jsonify({"message": f"No assignments found for user {user_id}."}), 200

        # Delete all assignments
        deleted_count = 0
        for assignment in assignments:
            db.session.delete(assignment)
            deleted_count += 1

        db.session.commit()

        return jsonify({
            "message": f"All assignments for user {user_id} deleted.",
            "deleted_count": deleted_count
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[Delete User Assignments Error] {e}")
        return jsonify({"error": "Failed to delete user assignments"}), 500
    
    
from flask import Blueprint, Response, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from io import BytesIO
from application.extensions import db
from application.services.measure_time import measure_response_time

from application.services.segment_detail_service import SegmentDetailService

segment_detail_blueprint = Blueprint('segment_detail', __name__)

@segment_detail_blueprint.route('/process_text', methods=['POST'])
@jwt_required
@measure_response_time
def handle_process_text():
    data = request.get_json()
    if 'chapter_id' not in data or 'chapter_data' not in data:
        return jsonify({"error": "Both 'chapter_id' and 'chapter_data' fields are required in the JSON body"}), 400

    chapter_id = data['chapter_id']
    sentences = data['chapter_data']
    
    try:
        processed_results = SegmentDetailService.process_sentences(sentences, chapter_id)
        return jsonify({"chapter_id": chapter_id, "processed_results": processed_results}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@segment_detail_blueprint.route('/segment_details/<int:segment_id>', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segment_details(segment_id):
    segment_details = SegmentDetailService.get_segment_details(segment_id)
    if segment_details:
        return jsonify(segment_details)
    else:
        return ('', 404)

@segment_detail_blueprint.route('/segment_details', methods=['POST'])
@jwt_required()
@measure_response_time
def create_segment_details():
    data = request.get_json()
    segment_id = SegmentDetailService.create_segment_details(data)
    if segment_id:
        return jsonify({'message': 'Segment details created/updated successfully', 'segment_id': segment_id}), 201
    else:
        return jsonify({'message': 'Failed to create/update segment details'}), 400
    

@segment_detail_blueprint.route('/segment_details/<int:segment_id>/download', methods=['GET'])
@jwt_required()
@measure_response_time
def download_segment_details(segment_id):
    segment_details = SegmentDetailService.get_segment_details_as_text(segment_id)
    if not segment_details:
        return ('', 404)

    # Convert the text data to bytes and create a BytesIO object
    file_obj = BytesIO(segment_details.encode('utf-8'))

    # Send the file to the user
    return send_file(
        file_obj,
        as_attachment=True,
        download_name=f"segment_{segment_id}.txt",
        mimetype="text/plain"
    )

@segment_detail_blueprint.route('/segment_details/<int:segment_id>/csv', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segment_details_csv(segment_id):
    segment_details = SegmentDetailService.get_segment_details_as_csv_single(segment_id)
    if segment_details:
        # Return as plain text with content type 'text/plain'
        return segment_details, 200, {'Content-Type': 'text/plain'}
    else:
        return 'Data not found', 404


@segment_detail_blueprint.route('/segment_details/<int:segment_id>/previous_csv', methods=['GET'])
@jwt_required()
@measure_response_time
def get_segment_details_csv_multiple(segment_id):
    segment_details = SegmentDetailService.get_segment_details_as_csv(segment_id)
    if segment_details:
        # Return as plain text with content type 'text/plain'
        return segment_details, 200, {'Content-Type': 'text/plain'}
    else:
        return 'Data not found', 404


@segment_detail_blueprint.route('/segment_details/<int:segment_id>/download_xml', methods=['GET'])
@jwt_required()
@measure_response_time
def download_segment_details_xml(segment_id):
    # Fetch the segment details using the service function
    segment_details = SegmentDetailService.get_segment_details_as_dict(segment_id)
    
    # If no segment details are found, return 404
    if not segment_details:
        return ('', 404)

    # Generate the XML content
    xml_content = SegmentDetailService.generate_segment_details_xml(segment_details)

    # Return the XML as a downloadable file
    response = Response(xml_content, mimetype='application/xml')
    response.headers['Content-Disposition'] = f'attachment; filename=segment_{segment_id}.xml'

    return response

@segment_detail_blueprint.route('/chapter_segments/<int:chapter_id>/download', methods=['GET'])
@jwt_required()
@measure_response_time
def download_all_segments_for_chapter(chapter_id):
    chapter_segments = SegmentDetailService.get_all_segments_for_chapter_as_text(chapter_id)
    if not chapter_segments:
        return ('', 404)

    # Convert the text data to bytes and create a BytesIO object
    file_obj = BytesIO(chapter_segments.encode('utf-8'))

    # Send the file to the user
    return send_file(
        file_obj,
        as_attachment=True,
        download_name=f"chapter_{chapter_id}_segments.txt",
        mimetype="text/plain"
    )


@segment_detail_blueprint.route('/chapters/<int:chapter_id>/segments/download_usr', methods=['GET'])
def download_usr_format(chapter_id):
    content = SegmentDetailService.get_all_segments_for_chapter_as_text(chapter_id)
    if not content:
        return Response("No content found", status=404)
    
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename=chapter_{chapter_id}_segments.usr"}
    )

@segment_detail_blueprint.route('/segment_details/<int:segment_id>/previous', methods=['GET'])
@jwt_required()
@measure_response_time
def get_previous_segment_details(segment_id):
    # Call the service method to fetch the previous segment's details
    previous_segment_details = SegmentDetailService.get_previous_segment_details(segment_id)
    
    if previous_segment_details:
        return jsonify(previous_segment_details)
    else:
        return ('', 404)



from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from application.extensions import db
from application.models.segment_model import Segment
from application.services.sentence_service import SentenceService
from application.models.sentence_model import Sentence
from application.services.measure_time import measure_response_time

sentence_blueprint = Blueprint('sentences', __name__)

@sentence_blueprint.route('/add', methods=['POST'])
@jwt_required()
@measure_response_time
def add_multiple_sentences():
    if 'file' not in request.files or 'chapter_id' not in request.form:
        return jsonify({'error': 'Missing file or chapter_id'}), 400

    file = request.files['file']
    chapter_id = request.form['chapter_id']

    if not file or not chapter_id:
        return jsonify({'error': 'Invalid data. Ensure chapter_id and file are provided.'}), 400

    # Read file content
    file_content = [line.strip() for line in file.read().decode('utf-8').splitlines() if line.strip()]
    print(f"Read {len(file_content)} lines from file")  # Debugging output

    new_sentences = SentenceService.create_sentences(chapter_id, file_content)
    return jsonify({'message': f'{len(new_sentences)} sentences added successfully'}), 201

    
@sentence_blueprint.route('/chapter/<int:chapter_id>/sentences', methods=['GET'])
@jwt_required()
@measure_response_time
def get_sentences_by_chapter(chapter_id):
    # Subquery to get the first segment per sentence
    subquery = (
        db.session.query(Segment)
        .filter(Segment.chapter_id == chapter_id)
        .distinct(Segment.sentence_id)
        .subquery()
    )

    # Join Sentence with the subquery
    results = (
        db.session.query(
            Sentence.id,
            Sentence.sentence_id,
            Sentence.sentence_index,
            Sentence.text,
            subquery.c.english_text,
            subquery.c.wx_text
        )
        .outerjoin(subquery, subquery.c.sentence_id == Sentence.id)
        .filter(Sentence.chapter_id == chapter_id)
        .order_by(Sentence.sentence_index)
        .all()
    )

    # Serialize results
    response = []
    for row in results:
        response.append({
            "id": row.id,
            "sentence_id": row.sentence_id,
            "sentence_index": row.sentence_index,
            "text": row.text,
            "english_text": row.english_text,
            "wx_text": row.wx_text,
        })

    return jsonify(response), 200


import re
from flask import Blueprint, Response, app, request, jsonify
from flask_jwt_extended import jwt_required
import requests

from application.services.segment_detail_service import SegmentDetailService
from application.services.visualizer_service import VisualizerService

visualizer_blueprint = Blueprint('visualizer', __name__)



@visualizer_blueprint.route('/generate-svg-from-api/<int:segment_id>', methods=['POST'])
@jwt_required()
def generate_svg_from_api(segment_id):
    try:
        # Fetch segment details directly using the service
        segment_details = SegmentDetailService.get_segment_details_as_csv_single(segment_id)
        
        if not segment_details:
            return jsonify({"error": "Segment details not found"}), 404
        
        usrs_text = segment_details  # Use the data fetched directly

        # Process the USR text (parsing and generating DOT graph)
        sentences, dot_graph = VisualizerService.process_usr_data(usrs_text)

        # Generate SVG in memory
        svg_output = dot_graph.pipe(format='svg')

        # Return the SVG file as response
        return Response(svg_output, mimetype='image/svg+xml')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@visualizer_blueprint.route('/generate-svg-from-api_multiple/<segment_id>', methods=['POST'])
@jwt_required()
def generate_svg_from_api_multiple(segment_id):
    try:
        # Step 1: Convert segment_id to integer (ensures correct database query)
        segment_id = int(segment_id)

        # Step 2: Fetch segment details using segment_id
        usrs_text = SegmentDetailService.get_segment_details_as_csv_single(segment_id)
        
        if not usrs_text:
            return jsonify({"error": f"Segment details not found for ID {segment_id}"}), 404

        # Step 3: Extract discourse-related segment_index from USR text
        connected_segment_indexes = set()
        for line in usrs_text.splitlines():
            if line and not line.startswith(("<", "#", "%")):  # Ignore metadata and comments
                columns = re.split(r'\t+', line.strip())
                if len(columns) > 5 and ":" in columns[5]:  # Checking discourse info
                    connected_segment_index = columns[5].split(":")[0]  # Extract segment reference
                    if "." in connected_segment_index:
                        connected_segment_index = connected_segment_index.split(".")[0]  # Remove sub-references
                    connected_segment_indexes.add(connected_segment_index)

        # Step 4: Fetch segment_ids for these segment_indexes
        connected_segment_ids = set()
        for segment_index in connected_segment_indexes:
            found_segment_id = SegmentDetailService.get_segment_id_by_index(segment_index)  # New DB function
            if found_segment_id:
                connected_segment_ids.add(found_segment_id)

        # Step 5: Fetch details of connected segments using their segment_ids
        for connected_id in connected_segment_ids:
            additional_usr = SegmentDetailService.get_segment_details_as_csv_single(connected_id)
            if additional_usr:
                usrs_text += "\n\n" + additional_usr  # Combine USR texts

        # Step 6: Process USR text (parsing and generating DOT graph)
        sentences, dot_graph = VisualizerService.process_usr_data_multiple(usrs_text)

        # Step 7: Generate SVG in memory
        svg_output = dot_graph.pipe(format='svg')

        # Step 8: Return the SVG file as response
        return Response(svg_output, mimetype='image/svg+xml')

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@visualizer_blueprint.route('/generate-svg-from-api_coref/<segment_id>', methods=['POST'])
@jwt_required()
def generate_svg_from_api_coref(segment_id):
    try:
        # 1️⃣ Fetch main segment USR text
        usr_text = SegmentDetailService.get_segment_details_as_csv_single(segment_id)
        if not usr_text:
            return jsonify({"error": "No USR data found for the given segment"}), 404

        print(f"INFO:application:Fetched main segment {segment_id} (USR size: {len(usr_text)} chars)")

        # 2️⃣ Detect coref-linked segment names (pattern matching like 'Geo_nios_2ch_0012')
        connection_pattern = r'(Geo_\w+_\d{4})'
        found_connections = set(re.findall(connection_pattern, usr_text))

        print(f"INFO:application:Found connections: {found_connections}")

        # 3️⃣ Fetch and merge connected segments' USR text
        for conn_name in found_connections:
            try:
                linked_id = SegmentDetailService.get_segment_id_by_name(conn_name)
                if linked_id:
                    linked_text = SegmentDetailService.get_segment_details_as_csv_single(linked_id)
                    if linked_text:
                        usr_text += "\n" + linked_text
                        print(f"INFO:application:Merged linked segment {conn_name} (ID: {linked_id})")
                    else:
                        print(f"WARN:application:No USR text found for {conn_name} (ID: {linked_id})")
                else:
                    print(f"WARN:application:Segment not found in DB: {conn_name}")
            except Exception as e:
                print(f"ERROR:application:Skipping {conn_name}: {e}")

        print(f"DEBUG:application:Final USR size after merging: {len(usr_text)} chars")

        # 4️⃣ Generate visualization using process_usr_data_coref
        sentences, dot = VisualizerService.process_usr_data_coref(usr_text)

        if not dot:
            return jsonify({"error": "Failed to generate visualization"}), 500

        svg = dot.pipe(format='svg')

        return Response(svg, mimetype='image/svg+xml')

    except Exception as e:
        print(f"ERROR:application:Visualization failed: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500