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
    Optimized bulk assignment API with improved error handling and type checking
    """
    data = request.get_json()
    
    # Validate input
    if not data or 'user_id' not in data or 'segments' not in data:
        return jsonify({'error': 'Payload must include user_id and segments list'}), 400

    user_id = data['user_id']
    segments_data = data['segments']

    if not isinstance(segments_data, list):
        return jsonify({'error': 'segments must be a list'}), 400

    # Get user details
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Convert and validate segment IDs
    try:
        segment_ids = [int(seg["segment_id"]) for seg in segments_data if seg.get("segment_id")]
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid segment_id format', 'details': str(e)}), 400

    if not segment_ids:
        return jsonify({'error': 'No valid segment_ids provided'}), 400

    # Bulk fetch all segments with proper type conversion
    segments = {s.segment_id: s for s in Segment.query.filter(Segment.segment_id.in_(segment_ids)).all()}

    # Check for missing segments
    missing_segments = set(segment_ids) - set(segments.keys())
    if missing_segments:
        print(f"Warning: Could not find segments with IDs: {missing_segments}")

    # Bulk fetch all chapters
    chapter_ids = list({s.chapter_id for s in segments.values()})
    chapters = {c.id: c for c in Chapter.query.filter(Chapter.id.in_(chapter_ids)).all()}

    # Process assignments
    all_results = []
    new_assignments = []
    segment_summaries = []

    for seg_item in segments_data:
        try:
            segment_id = int(seg_item["segment_id"])
            tab_names = seg_item.get("tab_names", [])
            
            if not isinstance(tab_names, list):
                raise ValueError("tab_names must be a list")

            segment = segments.get(segment_id)
            if not segment:
                all_results.append({
                    'segment_id': segment_id,
                    'status': 'failed',
                    'error': 'Segment not found'
                })
                continue

            chapter = chapters.get(segment.chapter_id)
            if not chapter:
                all_results.append({
                    'segment_id': segment_id,
                    'status': 'failed',
                    'error': 'Chapter not found for segment'
                })
                continue

            segment_results = []
            for tab_name in tab_names:
                # Check if assignment already exists
                existing = Assignment.query.filter_by(
                    segment_id=segment_id,
                    tab_name=tab_name
                ).first()

                if existing:
                    segment_results.append({
                        'tab_name': tab_name,
                        'status': 'failed',
                        'error': f'Already assigned to user {existing.user_id}',
                        'existing_user_id': existing.user_id
                    })
                    continue

                # Create new assignment
                assignment = Assignment(
                    user_id=user_id,
                    segment_id=segment_id,
                    tab_name=tab_name,
                    chapter_id=segment.chapter_id
                )
                db.session.add(assignment)
                new_assignments.append(assignment)
                segment_results.append({
                    'tab_name': tab_name,
                    'status': 'success'
                })

            all_results.append({
                'segment_id': segment_id,
                'chapter_id': chapter.id,
                'chapter_name': chapter.name,
                'segment_index': segment.segment_index,
                'results': segment_results
            })

            if any(r['status'] == 'success' for r in segment_results):
                segment_summaries.append({
                    'chapter_name': chapter.name,
                    'segment_id': segment_id,
                    'segment_index': segment.segment_index,
                    'assigned_tabs': [t for t in tab_names 
                                    if not any(
                                        r['tab_name'] == t and r['status'] == 'failed' 
                                        for r in segment_results
                                    )],
                    'segment_text': segment.segment_text
                })

        except Exception as e:
            all_results.append({
                'segment_id': seg_item.get("segment_id"),
                'status': 'failed',
                'error': f'Processing error: {str(e)}'
            })

    # Commit changes if there are new assignments
    if new_assignments:
        try:
            db.session.commit()
            
            # Send notification email if there are successful assignments
            if segment_summaries:
                subject = f"New Assignments: {len(new_assignments)} Tasks"
                body = f"Dear {user.username},\n\nYou have been assigned to:\n\n"
                
                for summary in segment_summaries:
                    body += (
                        f"Chapter: {summary['chapter_name']}\n"
                        f"Segment ID: {summary['segment_id']}\n"
                        f"Tabs: {', '.join(summary['assigned_tabs'])}\n"
                        f"Text: {summary['segment_text']}\n\n"
                    )
                
                body += "Please log in to complete these tasks.\n\nRegards,\nThe Team"
                
                try:
                    send_email(subject, body, user.email)
                except Exception as e:
                    print(f"Failed to send email: {str(e)}")
                    all_results.append({
                        'notification_status': 'failed',
                        'error': f'Email notification failed: {str(e)}'
                    })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Database error',
                'details': str(e),
                'partial_results': all_results
            }), 500

    return jsonify({
        'results': all_results,
        'total_new_assignments': len(new_assignments),
        'total_segments_processed': len(segments_data),
        'successful_segments': len([r for r in all_results if any(
            res.get('status') == 'success' for res in r.get('results', [])
        )])
    }), 201
   
        
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
    
@segment_blueprint.route('/chapter/<string:chapter_name>/delete_assignments', methods=['DELETE'])
@jwt_required()
@measure_response_time
def delete_assignments(chapter_name):
    """
    Delete assignments for a user in a chapter. Can handle both single segment and range deletions.
    
    For single segment deletion:
    Request body should contain:
    {
        "user_id": 123,
        "segment": "nio_1ch_001"
    }

    For range deletion:
    Request body should contain:
    {
        "user_id": 123,
        "start_segment": "nio_1ch_001",
        "end_segment": "nio_1ch_020"
    }
    """
    try:
        # Verify chapter exists
        chapter = Chapter.query.filter_by(name=chapter_name).first()
        if not chapter:
            return jsonify({'error': 'Chapter not found'}), 404

        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'Missing required field: user_id'}), 400

        user_id = data['user_id']
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': f"User {user_id} not found"}), 404

        # Handle single segment deletion
        if 'segment' in data:
            segment_index = data['segment']
            
            segment = Segment.query.filter_by(
                chapter_id=chapter.id,
                segment_index=segment_index
            ).first()

            if not segment:
                return jsonify({
                    'message': f"Segment {segment_index} not found in chapter {chapter_name}"
                }), 200

            # Delete single assignment
            deleted_count = Assignment.query.filter_by(
                user_id=user_id,
                segment_id=segment.segment_id
            ).delete()

            db.session.commit()

            return jsonify({
                'message': f"Deleted assignment for user {user_id} in segment {segment_index}",
                'chapter_name': chapter_name,
                'segment': segment_index,
                'deleted_count': deleted_count
            }), 200

        # Handle range deletion
        elif 'start_segment' in data and 'end_segment' in data:
            start_segment = data['start_segment']
            end_segment = data['end_segment']

            # Get all segments in the chapter within the specified range
            segments = db.session.query(Segment.segment_id)\
                .filter(
                    Segment.chapter_id == chapter.id,
                    Segment.segment_index >= start_segment,
                    Segment.segment_index <= end_segment
                )\
                .all()

            if not segments:
                return jsonify({
                    'message': f"No segments found in chapter {chapter_name} between {start_segment} and {end_segment}"
                }), 200

            segment_ids = [s.segment_id for s in segments]

            # Delete assignments for this user in these segments
            deleted_count = Assignment.query\
                .filter(
                    Assignment.user_id == user_id,
                    Assignment.segment_id.in_(segment_ids)
                )\
                .delete()

            db.session.commit()

            return jsonify({
                'message': f"Deleted {deleted_count} assignments for user {user_id}",
                'chapter_name': chapter_name,
                'chapter_id': chapter.id,
                'start_segment': start_segment,
                'end_segment': end_segment,
                'deleted_count': deleted_count
            }), 200

        else:
            return jsonify({
                'error': 'Must provide either "segment" or both "start_segment" and "end_segment"'
            }), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500