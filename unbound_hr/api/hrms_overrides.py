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
        if (
            result.get("success") is False
            and result.get("reason") == "calendar_conflict"
        ):
            conflicts = result.get("conflicts") or []

            details = []

            for item in conflicts:
                source = item.get("source") or "Interview"

                title = (
                    item.get("subject")
                    or item.get("interview_type")
                    or item.get("name")
                    or "Busy"
                )

                start = (
                    item.get("starts_on")
                    or item.get("from_time")
                    or ""
                )

                end = (
                    item.get("ends_on")
                    or item.get("to_time")
                    or ""
                )

                details.append(
                    f"<b>{frappe.utils.escape_html(str(title))}</b>"
                    f"<br>{frappe.utils.escape_html(str(source))}"
                    f"<br>{frappe.utils.escape_html(str(start))}"
                    f" → {frappe.utils.escape_html(str(end))}"
                )

            conflict_html = "<br><br>".join(details)

            frappe.throw(
                _(
                    "The selected interview time is unavailable."
                    "<br><br>{0}"
                    "<br><br>Please change the interview time and try again."
                ).format(conflict_html),
                title=_("Calendar Conflict"),
            )

        interview_name = result.get("interview")

        if interview_name:
            return interview_name

        frappe.throw(
            result.get("message")
            or _("Unable to schedule interview.")
        )

    return result
