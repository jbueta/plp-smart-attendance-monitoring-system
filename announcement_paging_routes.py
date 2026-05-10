from functools import wraps

from flask import Blueprint, request, jsonify, session
from announcement_models import AnnouncementModel

paging_bp = Blueprint('paging', __name__)
announcement_model = AnnouncementModel()


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"success": False, "message": "Authentication required"}), 401
        return view_func(*args, **kwargs)

    return wrapped_view

# [ANNOUNCEMENT FEATURE] - Admin CRUD Endpoints
@paging_bp.route('/admin/alerts', methods=['GET'])
@admin_required
def get_alerts():
    alerts = announcement_model.get_all_alerts()
    return jsonify({"success": True, "alerts": alerts})

@paging_bp.route('/admin/alerts', methods=['POST'])
@admin_required
def add_alert():
    data = request.json
    result = announcement_model.create_alert(
        from_source=data.get('from_source'),
        message=data.get('message'),
        visibility_scope=data.get('visibility_scope'),
        target_id=data.get('target_id'),
        target_department=data.get('target_department'),
        target_event=data.get('target_event'),
        expires_at=data.get('expires_at')
    )
    return jsonify(result)

@paging_bp.route('/admin/alerts/<int:alert_id>/status', methods=['PATCH'])
@admin_required
def toggle_alert(alert_id):
    data = request.json
    success = announcement_model.update_alert_status(alert_id, data.get('is_active'))
    return jsonify({"success": success})

# [ANNOUNCEMENT FEATURE] - Kiosk Public Endpoint
@paging_bp.route('/api/kiosk/alerts', methods=['GET'])
def fetch_kiosk_alerts():
    def sanitize(val):
        if not val or val.lower() in ['null', 'undefined', 'none']:
            return None
        return val

    target_id = sanitize(request.args.get('target_id'))
    target_dept = sanitize(request.args.get('target_dept'))
    target_event = sanitize(request.args.get('target_event'))

    alerts = announcement_model.get_active_alerts(
        target_id=target_id,
        target_dept=target_dept,
        target_event=target_event
    )
    return jsonify({"success": True, "alerts": alerts})
