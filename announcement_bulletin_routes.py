from functools import wraps

from flask import Blueprint, request, jsonify, session
from announcement_models import AnnouncementModel
from datetime import date

bulletin_bp = Blueprint('bulletin', __name__)
announcement_model = AnnouncementModel()


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"success": False, "message": "Authentication required"}), 401
        return view_func(*args, **kwargs)

    return wrapped_view

# [ANNOUNCEMENT FEATURE] - Admin CRUD Endpoints
@bulletin_bp.route('/admin/bulletins', methods=['GET'])
@admin_required
def get_bulletins():
    bulletins = announcement_model.get_all_bulletins()
    return jsonify({"success": True, "bulletins": bulletins})

@bulletin_bp.route('/admin/bulletins', methods=['POST'])
@admin_required
def add_bulletin():
    data = request.json
    result = announcement_model.create_bulletin(
        from_source=data.get('from_source'),
        category=data.get('category'),
        content=data.get('content'),
        visibility_scope=data.get('visibility_scope'),
        target_id=data.get('target_id'),
        target_department=data.get('target_department'),
        target_event=data.get('target_event'),
        scheduled_date=data.get('scheduled_date')
    )
    return jsonify(result)

@bulletin_bp.route('/admin/bulletins/<int:bulletin_id>/status', methods=['PATCH'])
@admin_required
def toggle_bulletin(bulletin_id):
    data = request.json
    success = announcement_model.update_bulletin_status(bulletin_id, data.get('is_active'))
    return jsonify({"success": success})

@bulletin_bp.route('/admin/bulletins/<int:bulletin_id>', methods=['DELETE'])
@admin_required
def delete_bulletin(bulletin_id):
    success = announcement_model.delete_bulletin(bulletin_id)
    return jsonify({"success": success})

# [ANNOUNCEMENT FEATURE] - Kiosk Public Endpoint
@bulletin_bp.route('/api/kiosk/bulletins', methods=['GET'])
def fetch_kiosk_bulletins():
    def sanitize(val):
        if not val or val.lower() in ['null', 'undefined', 'none']:
            return None
        return val

    target_id = sanitize(request.args.get('target_id'))
    target_dept = sanitize(request.args.get('target_dept'))
    target_event = sanitize(request.args.get('target_event'))
    scheduled_date = sanitize(request.args.get('scheduled_date')) or date.today().isoformat()

    bulletins = announcement_model.get_active_bulletins(
        target_id=target_id,
        target_dept=target_dept,
        target_event=target_event,
        scheduled_date=scheduled_date
    )
    return jsonify({"success": True, "bulletins": bulletins})
