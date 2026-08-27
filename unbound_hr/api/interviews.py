import frappe
from frappe import _
from frappe.utils import getdate


MAJORITY_ROUND_1 = "Majority Roles - Round 1"
MAJORITY_ROUND_2 = "Majority Roles - Round 2"
MAJORITY_ROUND_3 = "Majority Roles - Round 3"
SALES_OPS_ROUND_1 = "Sales Operations - Round 1"


def _ensure_hr_access():
    allowed_roles = {
        "System Manager",
        "HR Manager",
        "HR User",
    }

    user_roles = set(frappe.get_roles())

    if not allowed_roles.intersection(user_roles):
        frappe.throw(
            _("You do not have permission to manage interviews."),
            frappe.PermissionError,
        )


def _is_sales_or_operations(applicant):
    """
    Route Sales / Operations roles directly to Amol.
    Everything else follows the majority-role workflow.
    """

    opening = None

    if applicant.job_title:
        opening = frappe.get_doc(
            "Job Opening",
            applicant.job_title,
        )

    values = [
        getattr(applicant, "designation", None),
        getattr(opening, "designation", None) if opening else None,
        getattr(opening, "department", None) if opening else None,
        getattr(opening, "job_title", None) if opening else None,
    ]

    text = " ".join(
        str(value or "").lower()
        for value in values
    )

    keywords = {
        "sales",
        "operation",
        "operations",
        "business development",
        "bd ",
    }

    return any(keyword in text for keyword in keywords)


def _get_completed_interview_types(applicant_name):
    rows = frappe.get_all(
        "Interview",
        filters={
            "job_applicant": applicant_name,
        },
        fields=[
            "name",
            "interview_type",
            "status",
            "scheduled_on",
            "from_time",
            "to_time",
        ],
        order_by="creation asc",
    )

    return rows


def _resolve_next_interview_type(applicant):
    interviews = _get_completed_interview_types(
        applicant.name
    )

    if _is_sales_or_operations(applicant):
        return SALES_OPS_ROUND_1

    cleared = {
        row.interview_type
        for row in interviews
        if row.status == "Cleared"
    }

    pending_types = {
        row.interview_type
        for row in interviews
        if row.status in {
            "Pending",
            "Under Review",
        }
    }

    if MAJORITY_ROUND_1 in pending_types:
        return MAJORITY_ROUND_1

    if MAJORITY_ROUND_1 not in cleared:
        return MAJORITY_ROUND_1

    if MAJORITY_ROUND_2 in pending_types:
        return MAJORITY_ROUND_2

    if MAJORITY_ROUND_2 not in cleared:
        return MAJORITY_ROUND_2

    # Round 3 is intentionally optional.
    return None


def _get_default_interviewers(interview_type):
    doc = frappe.get_doc(
        "Interview Type",
        interview_type,
    )

    return [
        row.user
        for row in doc.interviewers
        if row.user
    ]


@frappe.whitelist()
def get_interview_plan(applicant_name):
    _ensure_hr_access()

    if not frappe.db.exists(
        "Job Applicant",
        applicant_name,
    ):
        frappe.throw(_("Job Applicant does not exist."))

    applicant = frappe.get_doc(
        "Job Applicant",
        applicant_name,
    )

    interview_type = _resolve_next_interview_type(
        applicant
    )

    if not interview_type:
        return {
            "applicant": applicant.name,
            "applicant_name": applicant.applicant_name,
            "job_opening": applicant.job_title,
            "designation": getattr(
                applicant,
                "designation",
                None,
            ),
            "interview_type": None,
            "interviewers": [],
            "message": _(
                "Required interview rounds are complete. "
                "Proceed to final review or schedule the optional third round."
            ),
        }

    return {
        "applicant": applicant.name,
        "applicant_name": applicant.applicant_name,
        "job_opening": applicant.job_title,
        "designation": getattr(
            applicant,
            "designation",
            None,
        ),
        "interview_type": interview_type,
        "interviewers": _get_default_interviewers(
            interview_type
        ),
        "sales_operations_route": _is_sales_or_operations(
            applicant
        ),
    }


# Temporary testing fallback.
# In production each interviewer will resolve to their own
# User Appointment Availability -> Google Calendar record.
TEST_GOOGLE_CALENDAR = "Himanshu Test Calendar"


def _get_google_calendar_for_interviewer(interviewer):
    """
    Resolve the interviewer's Google Calendar.

    Production:
        User Appointment Availability -> google_calendar

    Test fallback:
        Himanshu Test Calendar
    """

    calendar = frappe.db.get_value(
        "User Appointment Availability",
        {
            "user": interviewer,
        },
        "google_calendar",
    )

    if calendar:
        return calendar

    if frappe.db.exists(
        "Google Calendar",
        TEST_GOOGLE_CALENDAR,
    ):
        return TEST_GOOGLE_CALENDAR

    return None


def _get_google_calendar_conflicts(
    interviewer,
    scheduled_on,
    from_time,
    to_time,
):
    """
    Check synced Google Calendar Events overlapping the
    requested interview slot.
    """

    calendar = _get_google_calendar_for_interviewer(
        interviewer
    )

    if not calendar:
        return []

    from datetime import datetime

    date_string = str(scheduled_on)

    requested_start = datetime.fromisoformat(
        f"{date_string} {from_time}"
    )

    requested_end = datetime.fromisoformat(
        f"{date_string} {to_time}"
    )

    rows = frappe.get_all(
        "Event",
        filters={
            "google_calendar": calendar,
            "starts_on": ["<", requested_end],
            "ends_on": [">", requested_start],
        },
        fields=[
            "name",
            "subject",
            "starts_on",
            "ends_on",
            "google_calendar",
            "google_calendar_event_id",
            "google_meet_link",
        ],
        order_by="starts_on asc",
        limit_page_length=100,
    )

    conflicts = []

    for row in rows:
        conflicts.append(
            {
                "source": "Google Calendar",
                "interviewer": interviewer,
                "calendar": calendar,
                "event": row.name,
                "subject": row.subject,
                "starts_on": row.starts_on,
                "ends_on": row.ends_on,
                "google_calendar_event_id":
                    row.google_calendar_event_id,
            }
        )

    return conflicts


@frappe.whitelist()
def check_interviewer_availability(
    scheduled_on,
    from_time,
    to_time,
    interviewers,
    exclude_interview=None,
):
    _ensure_hr_access()

    if isinstance(interviewers, str):
        interviewers = frappe.parse_json(
            interviewers
        )

    if not interviewers:
        frappe.throw(
            _("At least one interviewer is required.")
        )

    scheduled_on = getdate(scheduled_on)

    conflicts = []

    for interviewer in interviewers:
        google_conflicts = (
            _get_google_calendar_conflicts(
                interviewer=interviewer,
                scheduled_on=scheduled_on,
                from_time=from_time,
                to_time=to_time,
            )
        )

        conflicts.extend(
            google_conflicts
        )

        child_rows = frappe.get_all(
            "Interview Detail",
            filters={
                "interviewer": interviewer,
            },
            pluck="parent",
        )

        if not child_rows:
            continue

        interview_names = list(set(child_rows))

        if exclude_interview:
            interview_names = [
                name
                for name in interview_names
                if name != exclude_interview
            ]

        if not interview_names:
            continue

        filters = {
            "name": ["in", interview_names],
            "scheduled_on": scheduled_on,
            "status": [
                "in",
                [
                    "Pending",
                    "Under Review",
                ],
            ],
            "from_time": ["<", to_time],
            "to_time": [">", from_time],
        }

        rows = frappe.get_all(
            "Interview",
            filters=filters,
            fields=[
                "name",
                "interview_type",
                "job_applicant",
                "scheduled_on",
                "from_time",
                "to_time",
            ],
        )

        for row in rows:
            conflicts.append(
                {
                    "interviewer": interviewer,
                    **row,
                }
            )

    return {
        "available": not conflicts,
        "conflicts": conflicts,
    }


def sync_interview_event_to_google(
    event_name,
):
    """
    Push an already committed Frappe Event to Google.

    This deliberately runs outside the interview scheduling
    database transaction so a DB deadlock can never leave
    behind an orphan Google Calendar event.
    """

    if not frappe.db.exists(
        "Event",
        event_name,
    ):
        return {
            "success": False,
            "reason": "event_missing",
        }

    event = frappe.get_doc(
        "Event",
        event_name,
    )

    # Idempotency protection.
    # Never create the same Google Event twice.
    if event.google_calendar_event_id:
        return {
            "success": True,
            "already_synced": True,
            "event": event.name,
            "google_calendar_event_id":
                event.google_calendar_event_id,
            "google_meet_link":
                event.google_meet_link,
        }

    try:
        from frappe_appointment.helpers.google_calendar import (
            insert_event_in_google_calendar_override,
        )

        # Enable sync only after the DB transaction
        # that created the Interview/Event has committed.
        frappe.db.set_value(
            "Event",
            event.name,
            "sync_with_google_calendar",
            1,
            update_modified=False,
        )

        event.sync_with_google_calendar = 1

        google_event_id = (
            insert_event_in_google_calendar_override(
                event,
                mute_message=True,
                update_doc=True,
            )
        )

        frappe.db.commit()

        google_data = frappe.db.get_value(
            "Event",
            event.name,
            [
                "google_calendar_event_id",
                "google_meet_link",
                "custom_google_calendar_event_url",
            ],
            as_dict=True,
        ) or {}

        return {
            "success": True,
            "event": event.name,
            "google_calendar_event_id":
                google_data.get(
                    "google_calendar_event_id"
                ),
            "google_meet_link":
                google_data.get(
                    "google_meet_link"
                ),
            "google_calendar_event_url":
                google_data.get(
                    "custom_google_calendar_event_url"
                ),
        }

    except Exception:
        frappe.db.rollback()

        frappe.log_error(
            title=(
                f"Interview Google Calendar sync failed: "
                f"{event_name}"
            ),
            message=frappe.get_traceback(),
        )

        raise


def _create_google_event_for_interview(
    interview,
    applicant,
    interviewers,
):
    """
    Create one Frappe Event.

    Frappe's Event after_insert hook pushes the Event to
    Google Calendar, creates Google Meet and sends attendee
    invitations.
    """

    if not interviewers:
        return None

    # For production this resolves the interviewer's own calendar.
    # During testing it falls back to Himanshu Test Calendar.
    google_calendar = _get_google_calendar_for_interviewer(
        interviewers[0]
    )

    if not google_calendar:
        frappe.throw(
            _("No Google Calendar is configured for the interviewer.")
        )

    calendar_doc = frappe.get_doc(
        "Google Calendar",
        google_calendar,
    )

    if not calendar_doc.enable:
        frappe.throw(
            _("Google Calendar {0} is disabled.").format(
                google_calendar
            )
        )

    if not calendar_doc.push_to_google_calendar:
        frappe.throw(
            _(
                "Push to Google Calendar is disabled for {0}."
            ).format(
                google_calendar
            )
        )

    if not calendar_doc.google_calendar_id:
        frappe.throw(
            _(
                "Google Calendar {0} is not fully authorized."
            ).format(
                google_calendar
            )
        )

    from frappe.utils import get_datetime

    starts_on = get_datetime(
        f"{interview.scheduled_on} {interview.from_time}"
    )

    ends_on = get_datetime(
        f"{interview.scheduled_on} {interview.to_time}"
    )

    candidate_name = (
        applicant.applicant_name
        or applicant.name
    )

    opening_title = interview.job_opening

    if interview.job_opening:
        opening_title = (
            frappe.db.get_value(
                "Job Opening",
                interview.job_opening,
                "job_title",
            )
            or interview.job_opening
        )

    event = frappe.new_doc("Event")

    event.subject = _(
        "Interview - {0} - {1}"
    ).format(
        candidate_name,
        opening_title,
    )

    event.event_type = "Private"
    event.starts_on = starts_on
    event.ends_on = ends_on

    event.description = _(
        """
        Interview: {0}<br>
        Candidate: {1}<br>
        Position: {2}<br>
        Interview Type: {3}
        """
    ).format(
        interview.name,
        candidate_name,
        opening_title,
        interview.interview_type,
    )

    # IMPORTANT:
    # Do not call Google while the Interview transaction
    # is still open. Google sync happens only after the
    # database transaction commits successfully.
    event.sync_with_google_calendar = 0
    event.google_calendar = google_calendar
    event.google_calendar_id = (
        calendar_doc.google_calendar_id
    )

    # Native Frappe Google Calendar integration uses this field
    # to request a Google Meet conference during Event insert.
    event.add_video_conferencing = 1

    # Keep Appointment integration metadata consistent too.
    if event.meta.has_field(
        "custom_meeting_provider"
    ):
        event.custom_meeting_provider = "Google Meet"

    candidate_email = getattr(
        applicant,
        "email_id",
        None,
    )

    if candidate_email:
        event.append(
            "event_participants",
            {
                "reference_doctype": "Job Applicant",
                "reference_docname": applicant.name,
                "email": candidate_email,
            },
        )

    calendar_owner = calendar_doc.user

    for interviewer in interviewers:
        # If this is the interviewer's own Google Calendar,
        # Google already treats them as the event organizer.
        # Do not add the owner again as an attendee.
        if interviewer == calendar_owner:
            continue

        event.append(
            "event_participants",
            {
                "reference_doctype": "User",
                "reference_docname": interviewer,
                "email": interviewer,
            },
        )

    event.insert(ignore_permissions=True)

    # Google sync is intentionally deferred until after
    # the Interview transaction commits successfully.
    return {
        "event": event.name,
        "google_calendar": google_calendar,
        "google_calendar_event_id": None,
        "google_meet_link": None,
        "google_calendar_event_url": None,
    }


@frappe.whitelist()
def schedule_interview(
    applicant_name,
    scheduled_on,
    from_time,
    to_time,
    interview_type=None,
    interviewers=None,
):
    _ensure_hr_access()

    if not frappe.db.exists(
        "Job Applicant",
        applicant_name,
    ):
        frappe.throw(_("Job Applicant does not exist."))

    applicant = frappe.get_doc(
        "Job Applicant",
        applicant_name,
    )

    if not interview_type:
        interview_type = _resolve_next_interview_type(
            applicant
        )

    if not interview_type:
        frappe.throw(
            _(
                "Required interview rounds are already complete."
            )
        )

    if not frappe.db.exists(
        "Interview Type",
        interview_type,
    ):
        frappe.throw(
            _("Interview Type {0} does not exist.").format(
                interview_type
            )
        )

    if isinstance(interviewers, str):
        interviewers = frappe.parse_json(
            interviewers
        )

    if not interviewers:
        interviewers = _get_default_interviewers(
            interview_type
        )

    if not interviewers:
        frappe.throw(
            _("No interviewer is configured for this Interview Type.")
        )

    from frappe.utils import get_time

    start_time = get_time(from_time)
    end_time = get_time(to_time)

    if start_time >= end_time:
        frappe.throw(
            _("Interview end time must be after the start time.")
        )

    existing = frappe.get_all(
        "Interview",
        filters={
            "job_applicant": applicant.name,
            "interview_type": interview_type,
            "status": [
                "in",
                [
                    "Pending",
                    "Under Review",
                ],
            ],
        },
        fields=[
            "name",
            "scheduled_on",
            "from_time",
            "to_time",
        ],
        limit_page_length=1,
    )

    if existing:
        current = existing[0]

        frappe.throw(
            _(
                "An active {0} interview already exists for this candidate: {1}."
            ).format(
                interview_type,
                current.name,
            )
        )

    availability = check_interviewer_availability(
        scheduled_on=scheduled_on,
        from_time=from_time,
        to_time=to_time,
        interviewers=interviewers,
    )

    if not availability["available"]:
        return {
            "success": False,
            "reason": "calendar_conflict",
            "message": _(
                "The selected interview time is unavailable."
            ),
            "conflicts": availability["conflicts"],
        }

    interview = frappe.new_doc("Interview")

    interview.interview_type = interview_type
    interview.job_applicant = applicant.name
    interview.job_opening = applicant.job_title
    interview.designation = getattr(
        applicant,
        "designation",
        None,
    )
    interview.resume_link = getattr(
        applicant,
        "resume_attachment",
        None,
    )

    interview.status = "Pending"
    interview.scheduled_on = scheduled_on
    interview.from_time = from_time
    interview.to_time = to_time

    for interviewer in interviewers:
        interview.append(
            "interview_details",
            {
                "interviewer": interviewer,
            },
        )

    interview.insert()

    calendar_result = _create_google_event_for_interview(
        interview=interview,
        applicant=applicant,
        interviewers=interviewers,
    )

    frappe.db.set_value(
        "Job Applicant",
        applicant.name,
        {
            "custom_ats_stage": "Interview Scheduled",
            "status": "Shortlisted",
        },
        update_modified=True,
    )

    frappe.db.commit()

    if calendar_result and calendar_result.get("event"):
        frappe.enqueue(
            "unbound_hr.api.interviews.sync_interview_event_to_google",
            queue="short",
            event_name=calendar_result["event"],
            enqueue_after_commit=True,
            job_name=(
                "unbound_hr_google_interview_sync::"
                + calendar_result["event"]
            ),
        )

    return {
        "success": True,
        "interview": interview.name,
        "interview_type": interview.interview_type,
        "scheduled_on": interview.scheduled_on,
        "from_time": interview.from_time,
        "to_time": interview.to_time,
        "interviewers": interviewers,
        "calendar_sync": (
            "Queued"
            if calendar_result
            else "Not Configured"
        ),
        "event": (
            calendar_result.get("event")
            if calendar_result
            else None
        ),
        "google_calendar": (
            calendar_result.get("google_calendar")
            if calendar_result
            else None
        ),
        "google_calendar_event_id": (
            calendar_result.get(
                "google_calendar_event_id"
            )
            if calendar_result
            else None
        ),
        "google_meet_link": (
            calendar_result.get(
                "google_meet_link"
            )
            if calendar_result
            else None
        ),
        "google_calendar_event_url": (
            calendar_result.get(
                "google_calendar_event_url"
            )
            if calendar_result
            else None
        ),
    }
