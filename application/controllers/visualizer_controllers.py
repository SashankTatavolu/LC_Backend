import re
from flask import Blueprint, Response, app, current_app, request, jsonify
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
        current_app.logger.info(f"Starting visualization for segment {segment_id}")

        # 1. Fetch main segment USR text
        usr_text = SegmentDetailService.get_segment_details_as_csv_single(segment_id)
        if not usr_text:
            current_app.logger.error(f"No USR data found for segment {segment_id}")
            return jsonify({"error": "No USR data found for the given segment"}), 404

        current_app.logger.debug(f"Initial USR text length: {len(usr_text)}")

        # 2. Extract all segment references from discourse fields
        found_connections = set()
        
        for line in usr_text.split('\n'):
            try:
                if not line.strip() or line.startswith(('#', '<', '%')):
                    continue
                    
                parts = re.split(r'\t+', line.strip())
                if len(parts) > 5 and parts[5] not in ('-', ''):
                    for item in parts[5].split('|'):
                        if ':' in item:
                            ref = item.split(':')[0].strip()
                            if not ref.isdigit():  # Skip simple token references
                                found_connections.add(ref)
            except Exception as e:
                current_app.logger.warning(f"Error processing line: {line[:50]}... Error: {str(e)}")
                continue

        current_app.logger.info(f"Found {len(found_connections)} unique segment references")

        # 3. Resolve and merge connected segments
        merged_texts = [usr_text]
        resolution_failures = []
        
        for ref in found_connections:
            try:
                # Extract base segment reference (before any dot)
                segment_ref = ref.split('.')[0]
                
                current_app.logger.debug(f"Attempting to resolve: {segment_ref}")
                segment_id = SegmentDetailService.get_segment_id_by_name(segment_ref)
                
                if segment_id:
                    linked_text = SegmentDetailService.get_segment_details_as_csv_single(segment_id)
                    if linked_text:
                        merged_texts.append(linked_text)
                        current_app.logger.debug(f"Successfully merged {segment_ref}")
                    else:
                        resolution_failures.append(f"Empty USR for {segment_ref}")
                else:
                    resolution_failures.append(f"Not found: {segment_ref}")
            except Exception as e:
                resolution_failures.append(f"Error resolving {ref}: {str(e)}")
                current_app.logger.error(f"Failed to resolve {ref}: {str(e)}", exc_info=True)

        if resolution_failures:
            current_app.logger.warning(f"Resolution failures: {', '.join(resolution_failures)}")

        # 4. Combine all USR texts
        full_usr_text = '\n'.join(merged_texts)
        current_app.logger.debug(f"Final USR text length: {len(full_usr_text)}")

        # 5. Generate visualization
        try:
            current_app.logger.info("Generating visualization...")
            sentences, dot = VisualizerService.process_usr_data_coref(full_usr_text)
            
            if not dot:
                current_app.logger.error("Visualization generation returned empty DOT graph")
                return jsonify({"error": "Failed to generate visualization"}), 500
                
            svg = dot.pipe(format='svg')
            current_app.logger.info("Successfully generated SVG")
            return Response(svg, mimetype='image/svg+xml')
            
        except Exception as e:
            current_app.logger.error(f"Visualization generation failed: {str(e)}", exc_info=True)
            return jsonify({"error": "Visualization failed", "details": str(e)}), 500

    except Exception as e:
        current_app.logger.critical(f"Endpoint crashed: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500