import traceback
from flask import Blueprint, request, jsonify, send_file
import json
from flask_jwt_extended import jwt_required
from application.extensions import db
from application.services.generation_service_process import hindi_genration
from application.services.generation_service import GenerationService
from application.services.generation_service_process import process_file_data
from application.models.generation_model import Generation
from application.services.segment_detail_service import SegmentDetailService
from application.models.segment_model import Segment
from application.models.sentence_model import Sentence
from io import BytesIO
from sqlalchemy.orm import joinedload
from application.services.measure_time import measure_response_time

generation_blueprint = Blueprint('generation', __name__)
@generation_blueprint.route('/process_single', methods=['POST'])
@jwt_required()
@measure_response_time
def process_single_file():
    if 'segment_ids' not in request.json or 'chapter_id' not in request.json:
        return jsonify({"error": "Segment IDs or Chapter ID missing"}), 400
    
    chapter_id = request.json['chapter_id']
    segment_ids = request.json['segment_ids']  
    
    if not isinstance(segment_ids, list):
        return jsonify({"error": "segment_ids should be a list"}), 400

    results = [] 
    combined_generated_texts = []  

    try:
        for segment_id in segment_ids:
            segment_details = SegmentDetailService.get_segment_details_as_text(segment_id)
            print(f"Details for Segment {segment_id}: {segment_details}")

            output_str = hindi_genration(segment_details)
            output = json.loads(output_str) if isinstance(output_str, str) else output_str
            print(f"Output for Segment {segment_id}: ", output)

            segment_index = output.get('sentence_id')
            if isinstance(segment_index, list):
                segment_index = segment_index[0]  
            
            print(f"Segment Index for Segment {segment_id}: ", segment_index)
            generated_text = output.get('text')
            print(f"Generated Text for Segment {segment_id}: ", generated_text)

            if isinstance(generated_text, list):
                generated_text = " ".join(generated_text)  

            combined_generated_texts.append(generated_text)

            segment = (db.session.query(Segment)
                       .join(Sentence)
                       .filter(Segment.segment_index == segment_index, Sentence.chapter_id == chapter_id)
                       .first())
            
            if not segment:
                results.append({
                    "segment_id": segment_id,
                    "error": "Segment not found"
                })
                continue
            
            print(f"Found Segment ID: {segment.segment_id}")

            # Delete existing generation if it exists
            existing_generation = (db.session.query(Generation)
                                   .filter(
                                       Generation.segment_id == segment.segment_id,
                                       Generation.chapter_id == chapter_id,
                                       Generation.segment_index == segment_index
                                   ).first())
            if existing_generation:
                db.session.delete(existing_generation)

            # Create new generation
            new_generation = Generation(
                segment_id=segment.segment_id, 
                segment_index=segment_index,
                chapter_id=chapter_id,  
                generated_text=generated_text
            )
            db.session.add(new_generation)
            db.session.commit()  

            results.append({
                "segment_id": segment_id,
                "message": "Generation saved successfully",
                "data": new_generation.serialize()
            })

        if combined_generated_texts:
            print("Combined Generated Texts: ", combined_generated_texts)
            combined_text = "\n\n".join(combined_generated_texts)
            print(combined_text)

            file_obj = BytesIO(combined_text.encode('utf-8'))
            print(file_obj)
            file_obj.seek(0)
            # Send the file to the user as an attachment
            return send_file(
                file_obj,
                as_attachment=True,
                download_name=f"generated_segments_{chapter_id}.txt",
                mimetype="text/plain"
            )

        return jsonify({"results": results})

    except Exception as e:
        # Log detailed error information
        print(f"Exception occurred: {str(e)}")
        traceback_str = traceback.format_exc()  # Get the full traceback
        print(f"Full traceback:\n{traceback_str}")

        db.session.rollback()  # Ensure the session is rolled back in case of an error
        return jsonify({"error": "Internal server error", "details": str(e), "traceback": traceback_str}), 500

@generation_blueprint.route('/process_bulk', methods=['POST'])
@jwt_required()
@measure_response_time
def process_bulk_file():
    if 'chapter_id' not in request.json:
        return jsonify({"error": "Chapter ID missing"}), 400
    
    chapter_id = request.json['chapter_id']

    try:
        # Fetch all segments related to the chapter's sentences
        segments = (db.session.query(Segment)
                    .join(Sentence)
                    .filter(Sentence.chapter_id == chapter_id)
                    .all())

        if not segments:
            return jsonify({"error": "No segments found for this chapter"}), 404

        # Fetch all segment details for the chapter
        segment_details_ = SegmentDetailService.get_all_segments_for_chapter_as_text(chapter_id)
        print("Input given: ", segment_details_)
        print(type(segment_details_))
        
        # Pass the entire string of segment details to hindi_genration
        output_str = hindi_genration(segment_details_)  # Pass the concatenated string
        output = json.loads(output_str) if isinstance(output_str, str) else output_str
        print(f"Output for all segments: ", output)

        # Initialize a string to store combined generated texts
        combined_generated_text = ""
        results = []

        # Iterate through the output and store each generation in the database
        for generated_segment in output['bulk']:
            segment_id = generated_segment.get('segment_id')
            generated_text = generated_segment.get('text')
            print(f"Processing Segment ID: {segment_id}, Generated Text: {generated_text}")

            # Find the segment by segment_id
            segment = (db.session.query(Segment)
                       .filter(Segment.segment_index == segment_id)
                       .join(Sentence)
                       .filter(Sentence.chapter_id == chapter_id)
                       .first())

            if not segment:
                results.append({
                    "segment_id": segment_id,
                    "error": "Segment not found"
                })
                continue

            print(f"Found Segment ID: {segment.segment_id}")

            # Delete existing generation if it exists
            existing_generation = (db.session.query(Generation)
                                   .filter(
                                       Generation.segment_id == segment.segment_id,
                                       Generation.chapter_id == chapter_id,
                                       Generation.segment_index == segment_id
                                   ).first())
            if existing_generation:
                db.session.delete(existing_generation)

            # Create new generation
            new_generation = Generation(
                segment_id=segment.segment_id,
                segment_index=segment_id,
                chapter_id=chapter_id,
                generated_text=generated_text
            )
            db.session.add(new_generation)
            db.session.commit()

            results.append({
                "segment_id": segment_id,
                "message": "Generation saved successfully",
                "data": new_generation.serialize()
            })

            # Append the segment index and generated text to the combined string with a newline
            combined_generated_text += f"{segment_id}: {generated_text}\n\n"

        # Combine all generated texts into a single text block
        if combined_generated_text:
            print("Combined Generated Texts: ", combined_generated_text)

            file_obj = BytesIO(combined_generated_text.encode('utf-8'))
            print(file_obj)

            # Send the file to the user as an attachment
            return send_file(
                file_obj,
                as_attachment=True,
                download_name=f"generated_segments_{chapter_id}.txt",
                mimetype="text/plain"
            )

        return jsonify({"results": results})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@generation_blueprint.route('/process', methods=['POST'])
@jwt_required()
@measure_response_time
def process_file():
    if 'segment_ids' not in request.json or 'chapter_id' not in request.json:
        return jsonify({"error": "Segment IDs or Chapter ID missing"}), 400
    
    chapter_id = request.json['chapter_id']
    segment_ids = request.json['segment_ids']  # Expecting this to be a list of segment IDs
    
    if not isinstance(segment_ids, list):
        return jsonify({"error": "segment_ids should be a list"}), 400

    results = []  # This will store the results for each segment

    try:
        for segment_id in segment_ids:
            segment_details = SegmentDetailService.get_segment_details_as_text(segment_id)
            print(f"Details for Segment {segment_id}: {segment_details}")

            output_str = hindi_genration(segment_details)
            output = json.loads(output_str) if isinstance(output_str, str) else output_str
            print(f"Output for Segment {segment_id}: ", output)

            segment_index = output.get('sentence_id')
            if isinstance(segment_index, list):
                segment_index = segment_index[0]  # If it's a list, take the first element
            
            print(f"Segment Index for Segment {segment_id}: ", segment_index)
            generated_text = output.get('text')
            print(f"Generated Text for Segment {segment_id}: ", generated_text)

            # Find corresponding segment
            segment = (db.session.query(Segment)
                       .join(Sentence)
                       .filter(Segment.segment_index == segment_index, Sentence.chapter_id == chapter_id)
                       .first())
            
            if not segment:
                results.append({
                    "segment_id": segment_id,
                    "error": "Segment not found"
                })
                continue
            
            print(f"Found Segment ID: {segment.segment_id}")

            # Delete existing generation if it exists
            existing_generation = (db.session.query(Generation)
                                   .filter(
                                       Generation.segment_id == segment.segment_id,
                                       Generation.chapter_id == chapter_id,
                                       Generation.segment_index == segment_index
                                   ).first())
            if existing_generation:
                db.session.delete(existing_generation)

            # Create new generation
            new_generation = Generation(
                segment_id=segment.segment_id, 
                segment_index=segment_index,
                chapter_id=chapter_id,  
                generated_text=generated_text
            )
            db.session.add(new_generation)
            db.session.commit()

            # Append successful result to the list
            results.append({
                "segment_id": segment_id,
                "message": "Generation saved successfully",
                "data": new_generation.serialize()
            })

        return jsonify({"results": results})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@generation_blueprint.route('/generate/text', methods=['GET'])
@jwt_required()
@measure_response_time
def fetch_generated_text():
    segment_id = request.args.get('segment_id')
    chapter_id = request.args.get('chapter_id')

    if not segment_id or not chapter_id:
        return jsonify({"error": "segment_id and chapter_id are required"}), 400

    generated_text = GenerationService.get_generated_text_by_segment_id(segment_id, chapter_id)

    if generated_text:
        return jsonify({"generated_text": generated_text}), 200
    else:
        return jsonify({"error": "No generated text found for the given segment ID"}), 404
    
@generation_blueprint.route('/<int:segment_id>/download', methods=['GET'])
@jwt_required()
@measure_response_time
def download_generated_text(segment_id):
    generated_text = GenerationService.get_generated_text_as_string(segment_id)
    if not generated_text:
        return ('', 404)

    # Convert the generated text to bytes
    file_obj = BytesIO(generated_text.encode('utf-8'))

    # Send the file to the user as an attachment
    return send_file(
        file_obj,
        as_attachment=True,
        download_name=f"generated_segment_{segment_id}.txt",
        mimetype="text/plain"
    )

@generation_blueprint.route('/chapter/<int:chapter_id>/download', methods=['GET'])
@jwt_required()
@measure_response_time
def download_generated_texts_for_chapter(chapter_id):
    generated_texts = GenerationService.get_all_generated_texts_by_chapter(chapter_id)
    
    if not generated_texts:
        return ('no data found', 404)

    # Combine all generated texts into a single string
    combined_text = "\n\n".join(generated_texts)

    # Convert the combined string to bytes
    file_obj = BytesIO(combined_text.encode('utf-8'))

    # Send the file to the user as an attachment
    return send_file(
        file_obj,
        as_attachment=True,
        download_name=f"generated_chapter_{chapter_id}.txt",
        mimetype="text/plain"
    )
