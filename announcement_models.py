import logging
from datetime import datetime
from database import connect_db

logger = logging.getLogger(__name__)

class AnnouncementModel:
    def __init__(self):
        pass

    def get_db(self):
        return connect_db()

    # [ANNOUNCEMENT FEATURE] - Bulletin Methods
    def create_bulletin(self, from_source, category, content, visibility_scope, target_id, target_department, target_event, scheduled_date):
        conn = self.get_db()
        if not conn: return {"success": False, "message": "Database offline"}
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO bulletins (from_source, category, content, visibility_scope, target_id, target_department, target_event, scheduled_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (from_source, category, content, visibility_scope, target_id, target_department, target_event, scheduled_date))
            conn.commit()
            return {"success": True, "bulletin_id": cursor.lastrowid}
        except Exception as e:
            logger.error(f"Error creating bulletin: {e}")
            return {"success": False, "message": str(e)}

    def get_all_bulletins(self):
        conn = self.get_db()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bulletins ORDER BY created_at DESC")
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching all bulletins: {e}")
            return []

    def update_bulletin_status(self, bulletin_id, is_active):
        conn = self.get_db()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE bulletins SET is_active = %s WHERE bulletin_id = %s", (is_active, bulletin_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating bulletin status: {e}")
            return False

    def delete_bulletin(self, bulletin_id):
        conn = self.get_db()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bulletins WHERE bulletin_id = %s", (bulletin_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting bulletin: {e}")
            return False

    def get_active_bulletins(self, scope=None, target_id=None, target_dept=None, target_event=None, scheduled_date=None):
        conn = self.get_db()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            # Order by specificity (Targeted > Departmental > Event > Global) then by recency
            query = """
                SELECT * FROM bulletins
                WHERE is_active = 1
                ORDER BY
                    CASE visibility_scope
                        WHEN 'targeted' THEN 1
                        WHEN 'departmental' THEN 2
                        WHEN 'event_specific' THEN 3
                        ELSE 4
                    END ASC,
                    created_at DESC
            """
            cursor.execute(query)
            all_active = cursor.fetchall()

            filtered = []
            for b in all_active:
                v_scope = str(b['visibility_scope']).lower()

                # Check scheduled_date filter if present
                if scheduled_date and str(b.get('scheduled_date')) != str(scheduled_date):
                    continue

                if v_scope == 'global':
                    filtered.append(b)
                elif v_scope == 'targeted' and target_id and str(target_id).strip() == str(b['target_id']).strip():
                    filtered.append(b)
                elif v_scope == 'departmental' and target_dept and str(target_dept).lower().strip() == str(b['target_department']).lower().strip():
                    filtered.append(b)
                elif v_scope == 'event_specific' and target_event and str(target_event).lower().strip() == str(b['target_event']).lower().strip():
                    filtered.append(b)

            return filtered
        except Exception as e:
            logger.error(f"Error fetching active bulletins: {e}")
            return []

    # [ANNOUNCEMENT FEATURE] - Paging/Alert Methods
    def create_alert(self, from_source, message, visibility_scope, target_id, target_department, target_event, expires_at):
        conn = self.get_db()
        if not conn: return {"success": False, "message": "Database offline"}
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO paging_alerts (from_source, message, visibility_scope, target_id, target_department, target_event, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (from_source, message, visibility_scope, target_id, target_department, target_event, expires_at))
            conn.commit()
            return {"success": True, "alert_id": cursor.lastrowid}
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return {"success": False, "message": str(e)}

    def get_all_alerts(self):
        conn = self.get_db()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM paging_alerts ORDER BY created_at DESC")
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching all alerts: {e}")
            return []

    def update_alert_status(self, alert_id, is_active):
        conn = self.get_db()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE paging_alerts SET is_active = %s WHERE alert_id = %s", (is_active, alert_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")
            return False

    def get_active_alerts(self, target_id=None, target_dept=None, target_event=None):
        conn = self.get_db()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            now = datetime.now()
            query = "SELECT * FROM paging_alerts WHERE is_active = 1 AND (expires_at IS NULL OR expires_at > %s)"
            cursor.execute(query, (now,))
            all_active = cursor.fetchall()

            filtered = []
            for a in all_active:
                v_scope = str(a['visibility_scope']).lower()

                if v_scope == 'global':
                    filtered.append(a)
                elif v_scope == 'targeted' and target_id and str(target_id).strip() == str(a['target_id']).strip():
                    filtered.append(a)
                elif v_scope == 'departmental' and target_dept and str(target_dept).lower().strip() == str(a['target_department']).lower().strip():
                    filtered.append(a)
                elif v_scope == 'event_specific' and target_event and str(target_event).lower().strip() == str(a['target_event']).lower().strip():
                    filtered.append(a)

            return filtered
        except Exception as e:
            logger.error(f"Error fetching active alerts: {e}")
            return []
