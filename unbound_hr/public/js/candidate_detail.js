window.UnboundCandidateDetail = {
    async show(applicantName, atsPage) {
        const response = await frappe.call({
            method: "unbound_hr.api.ats.get_candidate_details",
            args: {
                applicant_name: applicantName,
            },
            freeze: true,
            freeze_message: __("Loading candidate..."),
        });

        const c = response.message || {};

        const safe = (value) =>
            frappe.utils.escape_html(
                value === null || value === undefined || value === ""
                    ? "—"
                    : String(value)
            );

        const score = (value) => {
            if (value === null || value === undefined || value === "") {
                return "—";
            }
            return Number(value).toFixed(1);
        };

        const percent = (value) => {
            if (value === null || value === undefined || value === "") {
                return "—";
            }
            return `${Number(value).toFixed(0)}%`;
        };

        const dialog = new frappe.ui.Dialog({
            title: c.applicant_name || c.name,
            size: "extra-large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "candidate_details",
                },
            ],
            primary_action_label: __("Open Full Record"),
            primary_action() {
                frappe.set_route("Form", "Job Applicant", c.name);
                dialog.hide();
            },
        });

        const html = `
            <div class="unbound-candidate-detail">
                <div class="candidate-detail-header">
                    <div>
                        <h3>${safe(c.applicant_name)}</h3>
                        <div class="text-muted">
                            ${safe(c.email_id)}
                            ${c.phone_number ? ` · ${safe(c.phone_number)}` : ""}
                        </div>
                        <div class="text-muted mt-1">
                            ${safe(c.job_opening || c.designation)}
                        </div>
                    </div>

                    <div class="candidate-score-box">
                        <div class="candidate-score-label">ATS SCORE</div>
                        <div class="candidate-score-value">
                            ${score(c.ats_score)}
                        </div>
                    </div>
                </div>

                <hr>

                <div class="row">
                    <div class="col-md-4">
                        <strong>Stage</strong>
                        <div>${safe(c.ats_stage)}</div>
                    </div>
                    <div class="col-md-4">
                        <strong>Source</strong>
                        <div>${safe(c.source || c.source_type)}</div>
                    </div>
                    <div class="col-md-4">
                        <strong>Processing</strong>
                        <div>${safe(c.processing_status)}</div>
                    </div>
                </div>

                <hr>

                <div class="row">
                    <div class="col-md-4">
                        <strong>Skills Match</strong>
                        <div class="candidate-metric">
                            ${percent(c.skills_match)}
                        </div>
                    </div>
                    <div class="col-md-4">
                        <strong>Experience Match</strong>
                        <div class="candidate-metric">
                            ${percent(c.experience_match)}
                        </div>
                    </div>
                    <div class="col-md-4">
                        <strong>Education Match</strong>
                        <div class="candidate-metric">
                            ${percent(c.education_match)}
                        </div>
                    </div>
                </div>

                <hr>

                <div class="candidate-section">
                    <h5>AI Summary</h5>
                    <div>
                        ${c.ai_summary || '<span class="text-muted">Not processed yet</span>'}
                    </div>
                </div>

                <div class="candidate-section">
                    <h5>Strengths</h5>
                    <div>
                        ${c.strengths || '<span class="text-muted">Not processed yet</span>'}
                    </div>
                </div>

                <div class="candidate-section">
                    <h5>Concerns / Gaps</h5>
                    <div>
                        ${c.concerns || '<span class="text-muted">Not processed yet</span>'}
                    </div>
                </div>

                <div class="candidate-section">
                    <h5>Recruiter Notes</h5>
                    <div>${safe(c.recruiter_notes)}</div>
                </div>

                ${
                    c.resume
                        ? `
                            <div class="candidate-section">
                                <a
                                    class="btn btn-default btn-sm"
                                    href="${safe(c.resume)}"
                                    target="_blank"
                                >
                                    View Resume
                                </a>
                            </div>
                        `
                        : ""
                }

                <hr>

                <div class="candidate-detail-actions">
                    <button
                        class="btn btn-primary btn-sm"
                        data-process-resume
                    >
                        Process Resume
                    </button>

                    <button class="btn btn-success btn-sm" data-stage="Shortlisted">
                        Shortlist
                    </button>

                    <button
                        class="btn btn-primary btn-sm"
                        data-schedule-interview
                    >
                        Schedule Interview
                    </button>

                    <button class="btn btn-default btn-sm" data-stage="On Hold">
                        Hold
                    </button>
                    <button class="btn btn-danger btn-sm" data-stage="Rejected">
                        Reject
                    </button>
                </div>
            </div>
        `;

        dialog.fields_dict.candidate_details.$wrapper.html(html);

        dialog.fields_dict.candidate_details.$wrapper
            .find("[data-process-resume]")
            .on("click", async () => {
                try {
                    const result = await frappe.call({
                        method: "unbound_hr.api.ats.process_candidate_resume",
                        args: {
                            applicant_name: c.name,
                        },
                        freeze: true,
                        freeze_message: __("Processing resume and matching JD..."),
                    });

                    const response = result.message || {};
                    const match = response.match || {};

                    frappe.show_alert({
                        message: __(
                            "Resume processed. ATS Score: {0}",
                            [match.ats_score ?? "—"]
                        ),
                        indicator: "green",
                    });

                    dialog.hide();

                    if (
                        atsPage &&
                        typeof atsPage.refresh === "function"
                    ) {
                        await atsPage.refresh();
                    }
                } catch (error) {
                    console.error(error);

                    frappe.msgprint({
                        title: __("Resume Processing Failed"),
                        indicator: "red",
                        message: __("Unable to process this candidate's resume."),
                    });
                }
            });

        dialog.fields_dict.candidate_details.$wrapper
            .find("[data-schedule-interview]")
            .on("click", async () => {
                try {
                    const planResult = await frappe.call({
                        method: "unbound_hr.api.interviews.get_interview_plan",
                        args: {
                            applicant_name: c.name,
                        },
                        freeze: true,
                        freeze_message: __("Loading interview plan..."),
                    });

                    const plan = planResult.message || {};

                    if (!plan.interview_type) {
                        frappe.msgprint({
                            title: __("Interview Rounds Complete"),
                            indicator: "blue",
                            message:
                                plan.message ||
                                __("Required interview rounds are complete."),
                        });

                        return;
                    }

                    const interviewerNames = (
                        plan.interviewers || []
                    ).join(", ");

                    const scheduleDialog = new frappe.ui.Dialog({
                        title: __("Schedule Interview"),
                        fields: [
                            {
                                fieldtype: "HTML",
                                fieldname: "candidate_summary",
                                options: `
                                    <div style="
                                        padding: 12px 14px;
                                        margin-bottom: 12px;
                                        border: 1px solid var(--border-color);
                                        border-radius: 10px;
                                        background: var(--card-bg);
                                    ">
                                        <div>
                                            <strong>${frappe.utils.escape_html(
                                                plan.applicant_name || c.applicant_name || c.name
                                            )}</strong>
                                        </div>

                                        <div class="text-muted">
                                            ${frappe.utils.escape_html(
                                                plan.designation || c.designation || ""
                                            )}
                                        </div>

                                        <div style="margin-top: 8px;">
                                            <strong>${__("Interview Type")}:</strong>
                                            ${frappe.utils.escape_html(
                                                plan.interview_type
                                            )}
                                        </div>

                                        <div>
                                            <strong>${__("Interviewer")}:</strong>
                                            ${frappe.utils.escape_html(
                                                interviewerNames
                                            )}
                                        </div>
                                    </div>
                                `,
                            },
                            {
                                label: __("Scheduled On"),
                                fieldname: "scheduled_on",
                                fieldtype: "Date",
                                reqd: 1,
                                default: frappe.datetime.get_today(),
                            },
                            {
                                fieldtype: "Column Break",
                            },
                            {
                                label: __("Start Time"),
                                fieldname: "from_time",
                                fieldtype: "Time",
                                reqd: 1,
                            },
                            {
                                label: __("End Time"),
                                fieldname: "to_time",
                                fieldtype: "Time",
                                reqd: 1,
                            },
                            {
                                fieldtype: "Section Break",
                            },
                            {
                                fieldtype: "HTML",
                                fieldname: "availability_result",
                            },
                        ],
                        primary_action_label: __("Schedule Interview"),
                        primary_action: async (values) => {
                            try {
                                const check = await frappe.call({
                                    method:
                                        "unbound_hr.api.interviews.check_interviewer_availability",
                                    args: {
                                        scheduled_on: values.scheduled_on,
                                        from_time: values.from_time,
                                        to_time: values.to_time,
                                        interviewers: plan.interviewers,
                                    },
                                    freeze: true,
                                    freeze_message: __(
                                        "Checking interviewer availability..."
                                    ),
                                });

                                const availability =
                                    check.message || {};

                                if (!availability.available) {
                                    const conflicts =
                                        availability.conflicts || [];

                                    const rows = conflicts
                                        .map((item) => {
                                            return `
                                                <div style="margin-bottom: 8px;">
                                                    <strong>
                                                        ${frappe.utils.escape_html(
                                                            item.interviewer || ""
                                                        )}
                                                    </strong><br>
                                                    ${frappe.utils.escape_html(
                                                        item.name || ""
                                                    )}
                                                    —
                                                    ${frappe.utils.escape_html(
                                                        String(item.from_time || "")
                                                    )}
                                                    to
                                                    ${frappe.utils.escape_html(
                                                        String(item.to_time || "")
                                                    )}
                                                </div>
                                            `;
                                        })
                                        .join("");

                                    scheduleDialog
                                        .get_field("availability_result")
                                        .$wrapper.html(`
                                            <div class="alert alert-warning">
                                                <strong>
                                                    ${__("Interviewer conflict found")}
                                                </strong>
                                                <div style="margin-top: 8px;">
                                                    ${rows}
                                                </div>
                                            </div>
                                        `);

                                    return;
                                }

                                const result = await frappe.call({
                                    method:
                                        "unbound_hr.api.interviews.schedule_interview",
                                    args: {
                                        applicant_name: c.name,
                                        interview_type:
                                            plan.interview_type,
                                        interviewers:
                                            plan.interviewers,
                                        scheduled_on:
                                            values.scheduled_on,
                                        from_time:
                                            values.from_time,
                                        to_time:
                                            values.to_time,
                                    },
                                    freeze: true,
                                    freeze_message: __(
                                        "Scheduling interview..."
                                    ),
                                });

                                const response =
                                    result.message || {};

                                scheduleDialog.hide();
                                dialog.hide();

                                frappe.show_alert({
                                    message: __(
                                        "Interview {0} scheduled successfully",
                                        [
                                            response.interview ||
                                            "",
                                        ]
                                    ),
                                    indicator: "green",
                                });

                                if (
                                    atsPage &&
                                    typeof atsPage.refresh ===
                                        "function"
                                ) {
                                    await atsPage.refresh();
                                }
                            } catch (error) {
                                console.error(error);

                                frappe.msgprint({
                                    title: __("Interview Scheduling Failed"),
                                    indicator: "red",
                                    message:
                                        error?.message ||
                                        __("Unable to schedule interview."),
                                });
                            }
                        },
                    });

                    scheduleDialog.show();
                } catch (error) {
                    console.error(error);

                    frappe.msgprint({
                        title: __("Interview Plan Failed"),
                        indicator: "red",
                        message:
                            error?.message ||
                            __("Unable to load the interview plan."),
                    });
                }
            });


        dialog.fields_dict.candidate_details.$wrapper
            .find("[data-stage]")
            .on("click", async (event) => {
                const stage = event.currentTarget.dataset.stage;

                if (stage === "Shortlisted") {
                    const result = await frappe.call({
                        method: "unbound_hr.api.ats.shortlist_and_send_email",
                        args: {
                            applicants: [c.name],
                        },
                        freeze: true,
                        freeze_message: __("Sending shortlist email..."),
                    });

                    const response = result.message || {};

                    if (response.failed_count) {
                        frappe.msgprint({
                            title: __("Shortlist Email"),
                            indicator: "orange",
                            message: __(
                                "{0} email(s) queued successfully. {1} failed.",
                                [
                                    response.sent_count || 0,
                                    response.failed_count || 0,
                                ]
                            ),
                        });
                    } else {
                        frappe.show_alert({
                            message: __("Candidate shortlisted and email queued"),
                            indicator: "green",
                        });
                    }
                } else {
                    await frappe.call({
                        method: "unbound_hr.api.ats.bulk_update_stage",
                        args: {
                            applicants: [c.name],
                            stage,
                        },
                        freeze: true,
                        freeze_message: __("Updating candidate..."),
                    });

                    frappe.show_alert({
                        message: __("Candidate moved to {0}", [stage]),
                        indicator: "green",
                    });
                }

                dialog.hide();

                if (atsPage && typeof atsPage.refresh === "function") {
                    await atsPage.refresh();
                }
            });

        dialog.show();
    },
};
