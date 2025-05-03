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
