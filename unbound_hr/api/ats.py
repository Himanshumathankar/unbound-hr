import frappe
from frappe import _
from frappe.utils import now_datetime


ALLOWED_SORTS = {
    "score_desc": "custom_ats_score desc",
    "score_asc": "custom_ats_score asc",
    "newest": "creation desc",
    "oldest": "creation asc",
    "modified": "modified desc",
}


def _ensure_hr_access():
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required."), frappe.PermissionError)

    if not (
        frappe.has_permission("Job Applicant", "read")
        or "System Manager" in frappe.get_roles()
        or "HR Manager" in frappe.get_roles()
        or "HR User" in frappe.get_roles()
    ):
        frappe.throw(_("You do not have access to the ATS."), frappe.PermissionError)


@frappe.whitelist()
def get_job_openings():
    _ensure_hr_access()

    meta = frappe.get_meta("Job Opening")

    available_fields = {
        df.fieldname for df in meta.fields
    }

    requested = [
        "name",
        "job_title",
        "designation",
        "department",
        "company",
        "status",
    ]

    fields = [
        field
        for field in requested
        if field == "name" or field in available_fields
    ]

    filters = {}

    if "status" in available_fields:
        filters["status"] = "Open"

    return frappe.get_all(
        "Job Opening",
        fields=fields,
        filters=filters,
        order_by="modified desc",
        limit_page_length=500,
    )


@frappe.whitelist()
def get_applicants(
    job_opening=None,
    search=None,
    ats_stage=None,
    source=None,
    processing_status=None,
    sort="score_desc",
    limit_start=0,
    limit_page_length=100,
):
    _ensure_hr_access()

    limit_start = int(limit_start or 0)
    limit_page_length = min(int(limit_page_length or 100), 500)

    filters = {}

    if job_opening:
        filters["job_title"] = job_opening

        # Some HRMS versions use job_title while others expose job_opening.
        meta = frappe.get_meta("Job Applicant")
        available = {df.fieldname for df in meta.fields}

        if "job_opening" in available:
            filters.pop("job_title", None)
            filters["job_opening"] = job_opening

    if ats_stage:
        filters["custom_ats_stage"] = ats_stage

    if source:
        filters["source"] = source

    if processing_status:
        filters["custom_processing_status"] = processing_status

    meta = frappe.get_meta("Job Applicant")
    available = {df.fieldname for df in meta.fields}

    requested_fields = [
        "name",
        "applicant_name",
        "email_id",
        "phone_number",
        "job_title",
        "job_opening",
        "designation",
        "source",
        "status",
        "creation",
        "modified",
        "custom_ats_stage",
        "custom_processing_status",
        "custom_screening_status",
        "custom_ats_score",
        "custom_skills_match",
        "custom_experience_match",
        "custom_education_match",
        "custom_source_type",
    ]

    fields = [
        field
        for field in requested_fields
        if field == "name" or field in available
    ]

    or_filters = []

    if search:
        search = search.strip()

        if "applicant_name" in available:
            or_filters.append(["Job Applicant", "applicant_name", "like", f"%{search}%"])

        if "email_id" in available:
            or_filters.append(["Job Applicant", "email_id", "like", f"%{search}%"])

        or_filters.append(["Job Applicant", "name", "like", f"%{search}%"])

    order_by = ALLOWED_SORTS.get(sort, ALLOWED_SORTS["score_desc"])

    applicants = frappe.get_list(
        "Job Applicant",
        fields=fields,
        filters=filters,
        or_filters=or_filters or None,
        order_by=order_by,
        limit_start=limit_start,
        limit_page_length=limit_page_length,
    )

    for row in applicants:
        opening_id = row.get("job_title")

        if opening_id:
            row["job_opening_name"] = frappe.db.get_value(
                "Job Opening",
                opening_id,
                "job_title",
            ) or opening_id
        else:
            row["job_opening_name"] = ""

    count = frappe.db.count(
        "Job Applicant",
        filters=filters,
    )

    return {
        "applicants": applicants,
        "count": count,
    }


@frappe.whitelist()
def bulk_update_stage(applicants, stage):
    _ensure_hr_access()

    if isinstance(applicants, str):
        applicants = frappe.parse_json(applicants)

    if not isinstance(applicants, list) or not applicants:
        frappe.throw(_("Select at least one applicant."))

    allowed_stages = {
        "New Applicant",
        "Processing",
        "Screening",
        "HR Review",
        "Shortlisted",
        "Selection Mail Sent",
        "Interview Scheduled",
        "Interview Round 1",
        "Interview Round 2",
        "Final Review",
        "Selected",
        "Offer Sent",
        "Joined",
        "Rejected",
        "On Hold",
        "Withdrawn",
        "Not Interested",
        "Offer Declined",
    }

    if stage not in allowed_stages:
        frappe.throw(_("Invalid ATS stage."))

    updated = []

    for applicant_name in applicants:
        if not frappe.has_permission(
            "Job Applicant",
            "write",
            doc=applicant_name,
        ):
            frappe.throw(
                _("You cannot update Job Applicant {0}.").format(applicant_name),
                frappe.PermissionError,
            )

        values = {
            "custom_ats_stage": stage,
        }

        if stage == "Shortlisted":
            values["custom_shortlisted_on"] = now_datetime()

        if stage == "Rejected":
            values["custom_rejected_on"] = now_datetime()

        frappe.db.set_value(
            "Job Applicant",
            applicant_name,
            values,
            update_modified=True,
        )

        updated.append(applicant_name)

    frappe.db.commit()

    return {
        "updated": updated,
        "stage": stage,
    }


@frappe.whitelist()
def get_candidate_details(applicant_name):
    _ensure_hr_access()

    if not applicant_name:
        frappe.throw(_("Job Applicant is required."))

    if not frappe.has_permission(
        "Job Applicant",
        "read",
        doc=applicant_name,
    ):
        frappe.throw(
            _("You do not have permission to view this applicant."),
            frappe.PermissionError,
        )

    applicant = frappe.get_doc("Job Applicant", applicant_name)

    meta = frappe.get_meta("Job Applicant")
    available = {df.fieldname for df in meta.fields}

    def get(fieldname, default=None):
        if fieldname in available:
            return getattr(applicant, fieldname, default)
        return default

    resume = None

    if "resume_attachment" in available:
        resume = get("resume_attachment")
    elif "resume_link" in available:
        resume = get("resume_link")

    return {
        "name": applicant.name,
        "applicant_name": get("applicant_name") or applicant.name,
        "email_id": get("email_id"),
        "phone_number": get("phone_number"),
        "job_opening": get("job_opening") or get("job_title"),
        "designation": get("designation"),
        "source": get("source"),
        "source_type": get("custom_source_type"),
        "status": get("status"),
        "ats_stage": get("custom_ats_stage") or "New Applicant",
        "processing_status": get("custom_processing_status"),
        "screening_status": get("custom_screening_status"),
        "ats_score": get("custom_ats_score"),
        "skills_match": get("custom_skills_match"),
        "experience_match": get("custom_experience_match"),
        "education_match": get("custom_education_match"),
        "ai_summary": get("custom_ai_summary"),
        "strengths": get("custom_strengths"),
        "concerns": get("custom_concerns"),
        "recruiter_notes": get("custom_recruiter_notes"),
        "resume": resume,
        "creation": applicant.creation,
        "modified": applicant.modified,
    }
