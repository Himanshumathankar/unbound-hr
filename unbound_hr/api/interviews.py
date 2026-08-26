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
        frappe.throw(
            _(
                "One or more interviewers already have an "
                "interview during this time."
            )
        )

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

    return {
        "success": True,
        "interview": interview.name,
        "interview_type": interview.interview_type,
        "scheduled_on": interview.scheduled_on,
        "from_time": interview.from_time,
        "to_time": interview.to_time,
        "interviewers": interviewers,
        "calendar_sync": "Pending",
    }
