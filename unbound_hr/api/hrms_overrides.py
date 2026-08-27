import json

import frappe
from frappe import _

from unbound_hr.api.interviews import schedule_interview as unbound_schedule_interview


@frappe.whitelist()
def schedule_interview(
    job_applicant: str,
    interview_type: str,
    scheduled_on: str,
    from_time: str | None = None,
    to_time: str | None = None,
    interviewers=None,
):
    """
    Override HRMS Job Applicant interview scheduling.

    Reuse the Unbound ATS scheduling engine so interviews
    created from native HRMS also get:
    - availability validation
    - Google Calendar event
    - Google Meet
    - attendee invitations
    - ATS stage sync
    """

    if isinstance(interviewers, str):
        interviewers = json.loads(interviewers)

    interviewer_users = []

    for entry in interviewers or []:
        if isinstance(entry, dict):
            user = entry.get("interviewer")
        else:
            user = entry

        if user:
            interviewer_users.append(user)

    result = unbound_schedule_interview(
        applicant_name=job_applicant,
        scheduled_on=scheduled_on,
        from_time=from_time,
        to_time=to_time,
        interview_type=interview_type,
        interviewers=interviewer_users or None,
    )

    if isinstance(result, dict):
        return result.get("interview")

    return result
