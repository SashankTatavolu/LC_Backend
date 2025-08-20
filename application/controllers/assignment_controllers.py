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
            Chapter.name.label('chapter_name'),
            Assignment.user_id,
            User.username,
            Assignment.tab_name
        )
        .join(User, User.id == Assignment.user_id)
        .join(Segment, Segment.segment_id == Assignment.segment_id)
        .join(Chapter, Chapter.id == Assignment.chapter_id)
        .filter(User.organization == current_user.organization)
        .all()
    )

    grouped_assignments = defaultdict(lambda: {
        "segment_id": None,
        "segment_index": None,
        "chapter_id": None,
        "chapter_name": None,
        "user_id": None,
        "username": None,
        "assigned_tabs": []
    })

    for a in assignments:
        segment_data = grouped_assignments[a.segment_id]
        segment_data["segment_id"] = a.segment_id
        segment_data["segment_index"] = a.segment_index
        segment_data["chapter_id"] = a.chapter_id
        segment_data["chapter_name"] = a.chapter_name
        segment_data["user_id"] = a.user_id
        segment_data["username"] = a.username

        # Check if tab already exists
        existing_tabs = [t['tab_name'] for t in segment_data["assigned_tabs"]]
        if a.tab_name not in existing_tabs:
            is_finalized = False
            
            # Check if the tab is finalized
            if a.tab_name == 'lexical_conceptual':
                is_finalized = db.session.query(exists().where(
                    LexicalConceptual.segment_id == a.segment_id, 
                    LexicalConceptual.isFinalized == True
                )).scalar()
            elif a.tab_name == 'construction':
                is_finalized = db.session.query(exists().where(
                    Construction.segment_id == a.segment_id, 
                    Construction.isFinalized == True
                )).scalar()
            elif a.tab_name == 'relational':
                is_finalized = db.session.query(exists().where(
                    Relational.segment_id == a.segment_id, 
                    Relational.isFinalized == True
                )).scalar()
            elif a.tab_name == 'discourse':
                is_finalized = db.session.query(exists().where(
                    Discourse.segment_id == a.segment_id, 
                    Discourse.isFinalized == True
                )).scalar()
            
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


@assignment_blueprint.route('/chapter/<int:chapter_id>/assignments', methods=['DELETE'])
@jwt_required()
def delete_chapter_assignments(chapter_id):
    # First verify the chapter exists
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"message": "Chapter not found"}), 404

    try:
        # Delete all assignments for this chapter
        deleted_count = Assignment.query.filter_by(chapter_id=chapter_id).delete()
        db.session.commit()
        
        return jsonify({
            "message": f"Successfully deleted {deleted_count} assignments from chapter {chapter_id}",
            "deleted_count": deleted_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Failed to delete assignments",
            "error": str(e)
        }), 500
        
        
