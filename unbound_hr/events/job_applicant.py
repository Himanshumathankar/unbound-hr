import frappe


def queue_resume_processing(doc, method=None):
    """
    Automatically queue resume processing when a Job Applicant
    has a resume and has not already been successfully processed.
    """

    if not doc or not doc.name:
        return

    resume_url = (
        getattr(doc, "resume_attachment", None)
        or getattr(doc, "resume_link", None)
    )

    if not resume_url:
        return

    processing_status = getattr(
        doc,
        "custom_processing_status",
        None,
    )

    # Don't automatically re-process candidates that are already
    # completed or currently being processed.
    if processing_status in {"Queued", "Processing", "Completed"}:
        return

    # A Job Opening is required for JD matching.
    if not getattr(doc, "job_title", None):
        return

    job_name = (
        "unbound_hr_resume_processing::"
        + doc.name
    )

    frappe.db.set_value(
        "Job Applicant",
        doc.name,
        "custom_processing_status",
        "Queued",
        update_modified=False,
    )

    frappe.enqueue(
        "unbound_hr.api.ats.process_candidate_resume",
        queue="long",
        job_name=job_name,
        applicant_name=doc.name,
        enqueue_after_commit=True,
    )
