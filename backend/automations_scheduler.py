"""Executes due Automation steps (see main.py's AUTOMATIONS section for the CRUD layer).

Deliberately off by default: this sends real WhatsApp messages to real customers, so it
only runs if AUTOMATIONS_SCHEDULER_ENABLED is explicitly set to a truthy value. Until then,
enrolling someone in an automation just records intent - nothing gets sent. When enabled, a
background asyncio task (started from main.py's lifespan) wakes up every
AUTOMATIONS_SCHEDULER_INTERVAL_SECONDS (default 300 = 5 minutes), sends whichever step is
due, and advances or completes each enrollment.
"""
import os
import asyncio
from datetime import datetime, timedelta

if os.getenv("DATABASE_URL"):
    from database_mysql import get_db
else:
    from database_sqlite import get_db

SCHEDULER_ENABLED = os.getenv("AUTOMATIONS_SCHEDULER_ENABLED", "").lower() in ("1", "true", "yes")
INTERVAL_SECONDS = int(os.getenv("AUTOMATIONS_SCHEDULER_INTERVAL_SECONDS", "300"))


def _entity_phone(cursor, entity_type, entity_id):
    table = "leads" if entity_type == "lead" else "contacts"
    cursor.execute(f"SELECT phone FROM {table} WHERE id = ?", (entity_id,))
    row = cursor.fetchone()
    return row["phone"] if row and row["phone"] else None


def _process_due_enrollments():
    """One tick: send whatever step is due for every active enrollment past its next_run_at,
    then advance it to the next step or mark it completed. Each enrollment is committed
    independently so one bad phone number/API failure doesn't block the rest of the batch."""
    from main import (
        normalize_phone, _find_or_link_conversation, _send_whatsapp_api_message,
        _log_whatsapp_message,
    )

    # Same graceful-degradation convention as every other WhatsApp-sending route in this
    # app (see reply_whatsapp_conversation) - do nothing rather than firing a request at
    # Meta's API with an empty token/phone_id.
    if not (os.getenv("WHATSAPP_TOKEN") and os.getenv("WHATSAPP_PHONE_ID")):
        return

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM automation_enrollments WHERE status = 'active' AND next_run_at <= ?",
            (datetime.utcnow().isoformat(),)
        )
        due = [dict(row) for row in cursor.fetchall()]

    for enrollment in due:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM automation_steps WHERE automation_id = ? ORDER BY step_order",
                (enrollment["automation_id"],)
            )
            steps = [dict(row) for row in cursor.fetchall()]
            current_step = steps[enrollment["current_step"]] if enrollment["current_step"] < len(steps) else None

            if not current_step:
                cursor.execute("UPDATE automation_enrollments SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (enrollment["id"],))
                conn.commit()
                continue

            phone = _entity_phone(cursor, enrollment["entity_type"], enrollment["entity_id"])
            if not phone:
                print(f"[automations] enrollment {enrollment['id']}: no phone on {enrollment['entity_type']} {enrollment['entity_id']}, stopping")
                cursor.execute("UPDATE automation_enrollments SET status = 'stopped', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (enrollment["id"],))
                conn.commit()
                continue

            wa_number = normalize_phone(phone)
            convo = _find_or_link_conversation(cursor, wa_number)
            if convo.get("opted_out_at"):
                cursor.execute("UPDATE automation_enrollments SET status = 'stopped', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (enrollment["id"],))
                conn.commit()
                continue

            ok, wa_message_id, error = _send_whatsapp_api_message(
                wa_number,
                message=current_step["body"] if current_step["message_type"] == "text" else None,
                template_name=current_step["template_name"] if current_step["message_type"] == "template" else None,
            )
            _log_whatsapp_message(
                cursor, convo["id"], direction="out", status="sent" if ok else "failed",
                message_type=current_step["message_type"], template_name=current_step["template_name"],
                body=current_step["body"], wa_message_id=wa_message_id, error_message=error,
            )

            next_index = enrollment["current_step"] + 1
            if next_index < len(steps):
                next_run_at = (datetime.utcnow() + timedelta(minutes=steps[next_index]["wait_minutes"])).isoformat()
                cursor.execute(
                    "UPDATE automation_enrollments SET current_step = ?, next_run_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (next_index, next_run_at, enrollment["id"])
                )
            else:
                cursor.execute(
                    "UPDATE automation_enrollments SET current_step = ?, status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (next_index, enrollment["id"])
                )
            conn.commit()


async def run_scheduler_loop():
    """Started once from main.py's lifespan, only when SCHEDULER_ENABLED. Runs forever,
    ticking every INTERVAL_SECONDS; a single tick's exception is logged and swallowed so one
    bad row never kills the loop for everyone else."""
    print(f"[automations] scheduler started, ticking every {INTERVAL_SECONDS}s")
    while True:
        try:
            _process_due_enrollments()
        except Exception as e:
            print(f"[automations] scheduler tick failed: {e}")
        await asyncio.sleep(INTERVAL_SECONDS)
