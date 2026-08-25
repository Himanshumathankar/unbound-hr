import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


ATS_CUSTOM_FIELDS = {
    "Job Applicant": [
        {
            "fieldname": "custom_ats_section",
            "label": "Unbound ATS",
            "fieldtype": "Section Break",
            "insert_after": "status",
        },
        {
            "fieldname": "custom_ats_stage",
            "label": "ATS Stage",
            "fieldtype": "Select",
            "options": "\nNew Applicant\nProcessing\nScreening\nHR Review\nShortlisted\nSelection Mail Sent\nInterview Scheduled\nInterview Round 1\nInterview Round 2\nFinal Review\nSelected\nOffer Sent\nJoined\nRejected\nOn Hold\nWithdrawn\nNot Interested\nOffer Declined",
            "default": "New Applicant",
            "insert_after": "custom_ats_section",
            "in_list_view": 1,
            "in_standard_filter": 1,
        },
        {
            "fieldname": "custom_processing_status",
            "label": "Processing Status",
            "fieldtype": "Select",
            "options": "\nNot Processed\nQueued\nProcessing\nCompleted\nFailed",
            "default": "Not Processed",
            "insert_after": "custom_ats_stage",
            "in_standard_filter": 1,
        },
        {
            "fieldname": "custom_screening_status",
            "label": "Screening Status",
            "fieldtype": "Select",
            "options": "\nPending\nAI Reviewed\nHR Reviewed\nNeeds Review",
            "default": "Pending",
            "insert_after": "custom_processing_status",
        },
        {
            "fieldname": "custom_ats_column",
            "fieldtype": "Column Break",
            "insert_after": "custom_screening_status",
        },
        {
            "fieldname": "custom_ats_score",
            "label": "ATS Score",
            "fieldtype": "Float",
            "precision": "2",
            "insert_after": "custom_ats_column",
            "read_only": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "custom_skills_match",
            "label": "Skills Match %",
            "fieldtype": "Percent",
            "insert_after": "custom_ats_score",
            "read_only": 1,
        },
        {
            "fieldname": "custom_experience_match",
            "label": "Experience Match %",
            "fieldtype": "Percent",
            "insert_after": "custom_skills_match",
            "read_only": 1,
        },
        {
            "fieldname": "custom_education_match",
            "label": "Education Match %",
            "fieldtype": "Percent",
            "insert_after": "custom_experience_match",
            "read_only": 1,
        },
        {
            "fieldname": "custom_ats_analysis_section",
            "label": "Candidate Intelligence",
            "fieldtype": "Section Break",
            "insert_after": "custom_education_match",
            "collapsible": 1,
        },
        {
            "fieldname": "custom_ai_summary",
            "label": "AI Summary",
            "fieldtype": "Text Editor",
            "insert_after": "custom_ats_analysis_section",
            "read_only": 1,
        },
        {
            "fieldname": "custom_strengths",
            "label": "Strengths",
            "fieldtype": "Text Editor",
            "insert_after": "custom_ai_summary",
            "read_only": 1,
        },
        {
            "fieldname": "custom_concerns",
            "label": "Concerns / Gaps",
            "fieldtype": "Text Editor",
            "insert_after": "custom_strengths",
            "read_only": 1,
        },
        {
            "fieldname": "custom_recruiter_notes",
            "label": "Recruiter Notes",
            "fieldtype": "Small Text",
            "insert_after": "custom_concerns",
        },
        {
            "fieldname": "custom_source_type",
            "label": "Source Type",
            "fieldtype": "Select",
            "options": "\nInbound\nOutbound\nReferral\nInternal\nOther",
            "insert_after": "custom_recruiter_notes",
            "in_standard_filter": 1,
        },
        {
            "fieldname": "custom_ats_audit_section",
            "label": "ATS Audit",
            "fieldtype": "Section Break",
            "insert_after": "custom_source_type",
            "collapsible": 1,
        },
        {
            "fieldname": "custom_shortlisted_on",
            "label": "Shortlisted On",
            "fieldtype": "Datetime",
            "insert_after": "custom_ats_audit_section",
            "read_only": 1,
        },
        {
            "fieldname": "custom_rejected_on",
            "label": "Rejected On",
            "fieldtype": "Datetime",
            "insert_after": "custom_shortlisted_on",
            "read_only": 1,
        },
    ]
}


def create_ats_custom_fields():
    create_custom_fields(
        ATS_CUSTOM_FIELDS,
        update=True,
    )
    frappe.clear_cache(doctype="Job Applicant")
