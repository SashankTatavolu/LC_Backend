# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required

# from application.services.domain_term_service import DomainTermService

# domain_term_blueprint = Blueprint('domain_term', __name__)

# @domain_term_blueprint.route('/segment/<int:segment_id>/domain_term', methods=['POST', 'PUT'])
# @jwt_required()
# def manage_domain_term_by_segment(segment_id):
#     data = request.get_json()
#     if request.method == 'POST':
#         # Create new domain term entries
#         domain_entries = DomainTermService.create_domain_term_by_segment(segment_id, data)
#         return jsonify([domain.serialize() for domain in domain_entries]), 201
#     elif request.method == 'PUT':
#         # Update existing domain term entries
#         success = DomainTermService.update_domain_term_by_segment(segment_id, data)
#         return ('Update successful', 200) if success else ('No domain term data found', 404)
