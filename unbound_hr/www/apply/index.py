import frappe
from frappe.sessions import get_csrf_token

no_cache = 1


def get_context(context):
    context.no_cache = 1
    context.job_opening = None
    context.csrf_token = get_csrf_token()

    path = frappe.request.path.strip("/").split("/")

    if len(path) < 2:
        context.invalid_opening = True
        return context

    job_opening = path[-1]

    if not frappe.db.exists("Job Opening", job_opening):
        context.invalid_opening = True
        return context

    opening = frappe.get_doc(
        "Job Opening",
        job_opening,
    )

    if getattr(opening, "status", None) != "Open":
        context.invalid_opening = True
        return context

    context.invalid_opening = False

    context.job_opening = {
        "name": opening.name,
        "job_title": opening.job_title,
        "designation": getattr(opening, "designation", None),
        "department": getattr(opening, "department", None),
        "location": getattr(opening, "location", None),
        "description": getattr(opening, "description", None),
    }

    return context
