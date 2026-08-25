import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_job_opening(job_opening):
    """
    Return public information for an active Job Opening.
    """

    if not job_opening:
        frappe.throw(_("Job Opening is required."))

    if not frappe.db.exists("Job Opening", job_opening):
        frappe.throw(_("Job Opening not found."))

    opening = frappe.get_doc(
        "Job Opening",
        job_opening,
    )

    # Only expose openings that are available publicly.
    if getattr(opening, "status", None) != "Open":
        frappe.throw(_("This Job Opening is not accepting applications."))

    return {
        "name": opening.name,
        "job_title": opening.job_title,
        "designation": getattr(opening, "designation", None),
        "department": getattr(opening, "department", None),
        "location": getattr(opening, "location", None),
        "description": getattr(opening, "description", None),
    }


@frappe.whitelist(allow_guest=True)
def submit_application(
    job_opening,
    applicant_name,
    email,
    phone=None,
    cover_letter=None,
    source="Inbound",
):
    """
    Create a Job Applicant from the public application form.

    Resume upload will be handled separately so that we can validate
    the file before attaching it to the Job Applicant.
    """

    if not job_opening:
        frappe.throw(_("Job Opening is required."))

    if not applicant_name:
        frappe.throw(_("Full Name is required."))

    if not email:
        frappe.throw(_("Email is required."))

    email = email.strip().lower()

    if not frappe.db.exists("Job Opening", job_opening):
        frappe.throw(_("Job Opening not found."))

    opening = frappe.get_doc(
        "Job Opening",
        job_opening,
    )

    if getattr(opening, "status", None) != "Open":
        frappe.throw(
            _("This Job Opening is not accepting applications.")
        )

    # Prevent duplicate applications to the same opening.
    existing = frappe.db.exists(
        "Job Applicant",
        {
            "email_id": email,
            "job_title": job_opening,
        },
    )

    if existing:
        return {
            "success": False,
            "duplicate": True,
            "applicant": existing,
            "message": _(
                "You have already applied for this position."
            ),
        }

    applicant = frappe.new_doc("Job Applicant")

    applicant.applicant_name = applicant_name.strip()
    applicant.email_id = email
    applicant.job_title = job_opening

    meta = frappe.get_meta("Job Applicant")
    fields = {df.fieldname for df in meta.fields}

    if phone and "phone_number" in fields:
        applicant.phone_number = phone.strip()

    if source and "source" in fields:
        # Only set Source if the linked/source value exists.
        source_doctype = frappe.get_meta(
            "Job Applicant"
        ).get_field("source")

        if (
            source_doctype
            and source_doctype.fieldtype == "Link"
            and source_doctype.options
        ):
            if frappe.db.exists(
                source_doctype.options,
                source,
            ):
                applicant.source = source
        else:
            applicant.source = source

    if "custom_source_type" in fields:
        applicant.custom_source_type = "Inbound"

    if (
        cover_letter
        and "cover_letter" in fields
    ):
        applicant.cover_letter = cover_letter

    if "custom_processing_status" in fields:
        applicant.custom_processing_status = "Not Processed"

    if "custom_ats_stage" in fields:
        applicant.custom_ats_stage = "New Applicant"

    applicant.flags.ignore_permissions = True
    applicant.insert()

    frappe.db.commit()

    return {
        "success": True,
        "duplicate": False,
        "applicant": applicant.name,
        "message": _("Application submitted successfully."),
    }


@frappe.whitelist(allow_guest=True)
def attach_resume(applicant):
    """
    Attach an uploaded resume to an existing Job Applicant.

    Expected request:
    multipart/form-data
    file=<PDF/DOCX/TXT>
    applicant=<Job Applicant name>
    """

    if not applicant:
        frappe.throw(_("Applicant is required."))

    if not frappe.db.exists("Job Applicant", applicant):
        frappe.throw(_("Applicant not found."))

    uploaded_file = frappe.request.files.get("file")

    if not uploaded_file:
        frappe.throw(_("Resume file is required."))

    filename = uploaded_file.filename or ""

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt",
    }

    from pathlib import Path

    extension = Path(filename).suffix.lower()

    if extension not in allowed_extensions:
        frappe.throw(
            _("Only PDF, DOCX, and TXT resumes are allowed.")
        )

    # 10 MB limit
    uploaded_file.seek(0, 2)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)

    if file_size > 10 * 1024 * 1024:
        frappe.throw(
            _("Resume must be smaller than 10 MB.")
        )

    content = uploaded_file.read()

    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "attached_to_doctype": "Job Applicant",
        "attached_to_name": applicant,
        "is_private": 1,
        "content": content,
    })

    file_doc.flags.ignore_permissions = True
    file_doc.insert()

    meta = frappe.get_meta("Job Applicant")
    fields = {df.fieldname for df in meta.fields}

    values = {}

    if "resume_attachment" in fields:
        values["resume_attachment"] = file_doc.file_url
    elif "resume_link" in fields:
        values["resume_link"] = file_doc.file_url
    else:
        frappe.throw(
            _("Job Applicant does not have a resume field.")
        )

    if "custom_processing_status" in fields:
        values["custom_processing_status"] = "Not Processed"

    frappe.db.set_value(
        "Job Applicant",
        applicant,
        values,
        update_modified=True,
    )

    frappe.db.commit()

    # Explicitly enqueue processing after resume attachment.
    frappe.enqueue(
        "unbound_hr.api.ats.process_candidate_resume",
        queue="long",
        applicant_name=applicant,
        job_name=f"unbound_hr_resume_processing::{applicant}",
        enqueue_after_commit=True,
    )

    return {
        "success": True,
        "applicant": applicant,
        "file_url": file_doc.file_url,
        "message": _("Resume uploaded successfully."),
    }


@frappe.whitelist(allow_guest=True)
def submit_application_with_resume():
    """
    Public application endpoint.

    Expects multipart/form-data:
    - job_opening
    - applicant_name
    - email
    - phone (optional)
    - cover_letter (optional)
    - source (optional)
    - file
    """

    from pathlib import Path

    form = frappe.form_dict

    job_opening = form.get("job_opening")
    applicant_name = form.get("applicant_name")
    email = form.get("email")
    phone = form.get("phone")
    cover_letter = form.get("cover_letter")
    source = form.get("source") or "Inbound"

    if not job_opening:
        frappe.throw(_("Job Opening is required."))

    if not applicant_name:
        frappe.throw(_("Full Name is required."))

    if not email:
        frappe.throw(_("Email is required."))

    email = email.strip().lower()

    if not frappe.db.exists("Job Opening", job_opening):
        frappe.throw(_("Job Opening not found."))

    opening = frappe.get_doc(
        "Job Opening",
        job_opening,
    )

    if getattr(opening, "status", None) != "Open":
        frappe.throw(
            _("This Job Opening is not accepting applications.")
        )

    existing = frappe.db.exists(
        "Job Applicant",
        {
            "email_id": email,
            "job_title": job_opening,
        },
    )

    if existing:
        return {
            "success": False,
            "duplicate": True,
            "applicant": existing,
            "message": _(
                "You have already applied for this position."
            ),
        }

    uploaded_file = frappe.request.files.get("file")

    if not uploaded_file:
        frappe.throw(_("Resume file is required."))

    filename = uploaded_file.filename or ""

    extension = Path(filename).suffix.lower()

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt",
    }

    if extension not in allowed_extensions:
        frappe.throw(
            _("Only PDF, DOCX, and TXT resumes are allowed.")
        )

    uploaded_file.seek(0, 2)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)

    if file_size > 10 * 1024 * 1024:
        frappe.throw(
            _("Resume must be smaller than 10 MB.")
        )

    content = uploaded_file.read()

    applicant = frappe.new_doc("Job Applicant")

    applicant.applicant_name = applicant_name.strip()
    applicant.email_id = email
    applicant.job_title = job_opening

    meta = frappe.get_meta("Job Applicant")
    fields = {df.fieldname for df in meta.fields}

    if phone and "phone_number" in fields:
        applicant.phone_number = phone.strip()

    if cover_letter and "cover_letter" in fields:
        applicant.cover_letter = cover_letter

    if "custom_source_type" in fields:
        applicant.custom_source_type = "Inbound"

    if "custom_processing_status" in fields:
        applicant.custom_processing_status = "Not Processed"

    if "custom_ats_stage" in fields:
        applicant.custom_ats_stage = "New Applicant"

    applicant.flags.ignore_permissions = True
    applicant.insert()

    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "attached_to_doctype": "Job Applicant",
        "attached_to_name": applicant.name,
        "is_private": 1,
        "content": content,
    })

    file_doc.flags.ignore_permissions = True
    file_doc.insert()

    values = {}

    if "resume_attachment" in fields:
        values["resume_attachment"] = file_doc.file_url
    elif "resume_link" in fields:
        values["resume_link"] = file_doc.file_url
    else:
        frappe.throw(
            _("Job Applicant does not have a resume field.")
        )

    frappe.db.set_value(
        "Job Applicant",
        applicant.name,
        values,
        update_modified=True,
    )

    frappe.db.commit()

    frappe.enqueue(
        "unbound_hr.api.applications.process_public_candidate_resume",
        queue="long",
        applicant_name=applicant.name,
        job_name=f"unbound_hr_resume_processing::{applicant.name}",
        enqueue_after_commit=True,
    )

    return {
        "success": True,
        "duplicate": False,
        "applicant": applicant.name,
        "job_opening": job_opening,
        "file_url": file_doc.file_url,
        "message": _("Application submitted successfully."),
    }


def process_public_candidate_resume(applicant_name):
    """
    Trusted background worker for public applications.

    Public submissions run as Guest, but ATS processing requires
    HR permissions. Switch to Administrator only inside the
    background worker.
    """

    frappe.set_user("Administrator")

    from unbound_hr.api.ats import process_candidate_resume

    return process_candidate_resume(
        applicant_name=applicant_name
    )


