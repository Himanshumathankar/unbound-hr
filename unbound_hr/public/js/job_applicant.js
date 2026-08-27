function render_interview_conflicts(dialog, conflicts) {
    const rows = (conflicts || [])
        .map((item) => {
            const source =
                item.source ||
                (item.name ? "HRMS Interview" : "Calendar");

            const title =
                item.subject ||
                item.interview_type ||
                item.name ||
                __("Busy");

            const start =
                item.starts_on ||
                item.from_time ||
                "";

            const end =
                item.ends_on ||
                item.to_time ||
                "";

            const sourceLabel =
                source === "Google Calendar"
                    ? __("Google Calendar")
                    : __("HRMS Interview");

            return `
                <div style="
                    padding: 10px 0;
                    border-bottom: 1px solid var(--border-color);
                ">
                    <div>
                        <strong>
                            ${frappe.utils.escape_html(
                                title
                            )}
                        </strong>
                    </div>

                    <div class="text-muted"
                         style="margin-top: 2px;">
                        ${frappe.utils.escape_html(
                            sourceLabel
                        )}
                    </div>

                    ${
                        item.interviewer
                            ? `
                                <div style="margin-top:4px;">
                                    ${__("Interviewer")}:
                                    ${frappe.utils.escape_html(
                                        item.interviewer
                                    )}
                                </div>
                            `
                            : ""
                    }

                    ${
                        item.calendar
                            ? `
                                <div>
                                    ${__("Calendar")}:
                                    ${frappe.utils.escape_html(
                                        item.calendar
                                    )}
                                </div>
                            `
                            : ""
                    }

                    <div style="margin-top:4px;">
                        ${frappe.utils.escape_html(
                            String(start)
                        )}
                        →
                        ${frappe.utils.escape_html(
                            String(end)
                        )}
                    </div>
                </div>
            `;
        })
        .join("");

    dialog
        .get_field("availability_result")
        .$wrapper.html(`
            <div class="alert alert-warning">
                <div style="font-weight:600;">
                    ${__("Selected time is unavailable")}
                </div>

                <div style="margin-top:6px;">
                    ${__(
                        "Change the date or time above and try again."
                    )}
                </div>

                <div style="margin-top:10px;">
                    ${rows}
                </div>
            </div>
        `);
}
frappe.ui.form.on("Job Applicant", {
    refresh(frm) {
        const status_colors = {
            Open: "orange",
            Replied: "blue",
            Shortlisted: "green",
            Rejected: "red",
            Hold: "orange",
            Accepted: "green",
        };

        const ats_colors = {
            "New Applicant": "gray",
            "Processing": "blue",
            "Screening": "blue",
            "HR Review": "orange",
            "Shortlisted": "green",
            "Selection Mail Sent": "blue",
            "Interview Scheduled": "blue",
            "Interview Round 1": "blue",
            "Interview Round 2": "blue",
            "Final Review": "purple",
            "Selected": "green",
            "Offer Sent": "green",
            "Joined": "green",
            "Rejected": "red",
            "On Hold": "orange",
            "Withdrawn": "gray",
            "Not Interested": "gray",
            "Offer Declined": "red",
        };

        const status = frm.doc.status || "Open";
        const color = status_colors[status] || "gray";

        frm.page.set_indicator(
            __(status),
            color
        );

        if (frm.doc.custom_ats_stage) {
            const ats_stage = frm.doc.custom_ats_stage;
            const ats_color =
                ats_colors[ats_stage] || "gray";

            frm.dashboard.add_indicator(
                __("ATS Stage: {0}", [ats_stage]),
                ats_color
            );
        }

        frm.add_custom_button(
            __("Open in Unbound ATS"),
            () => {
                frappe.set_route("unbound-ats");
            },
            __("ATS")
        );

        frm.add_custom_button(
            __("Schedule Interview"),
            () => {
                open_interview_scheduler(frm);
            },
            __("ATS")
        );

        frm.add_custom_button(
            __("View Interviews"),
            () => {
                frappe.set_route(
                    "List",
                    "Interview",
                    {
                        job_applicant: frm.doc.name,
                    }
                );
            },
            __("ATS")
        );
    },
});


async function open_interview_scheduler(frm) {
    try {
        const planResult = await frappe.call({
            method:
                "unbound_hr.api.interviews.get_interview_plan",
            args: {
                applicant_name: frm.doc.name,
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

        const dialog = new frappe.ui.Dialog({
            title: __("Schedule Interview"),
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "summary",
                    options: `
                        <div style="
                            padding: 14px;
                            margin-bottom: 12px;
                            border: 1px solid var(--border-color);
                            border-radius: 10px;
                        ">
                            <div>
                                <strong>
                                    ${frappe.utils.escape_html(
                                        plan.applicant_name ||
                                        frm.doc.applicant_name ||
                                        frm.doc.name
                                    )}
                                </strong>
                            </div>

                            <div class="text-muted">
                                ${frappe.utils.escape_html(
                                    plan.designation ||
                                    frm.doc.designation ||
                                    ""
                                )}
                            </div>

                            <div style="margin-top: 10px;">
                                <strong>
                                    ${__("Interview Type")}:
                                </strong>
                                ${frappe.utils.escape_html(
                                    plan.interview_type
                                )}
                            </div>

                            <div>
                                <strong>
                                    ${__("Interviewer")}:
                                </strong>
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
                            scheduled_on:
                                values.scheduled_on,
                            from_time:
                                values.from_time,
                            to_time:
                                values.to_time,
                            interviewers:
                                plan.interviewers,
                        },
                        freeze: true,
                        freeze_message: __(
                            "Checking interviewer availability..."
                        ),
                    });

                    const availability =
                        check.message || {};

                    if (!availability.available) {
                        render_interview_conflicts(
                            dialog,
                            availability.conflicts || []
                        );

                        return;
                    }

                    const result = await frappe.call({
                        method:
                            "unbound_hr.api.interviews.schedule_interview",
                        args: {
                            applicant_name:
                                frm.doc.name,
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

                    if (
                        response.success === false &&
                        response.reason ===
                            "calendar_conflict"
                    ) {
                        render_interview_conflicts(
                            dialog,
                            response.conflicts || []
                        );

                        return;
                    }

                    dialog.hide();

                    frappe.show_alert({
                        message: __(
                            "Interview {0} scheduled successfully",
                            [
                                response.interview || "",
                            ]
                        ),
                        indicator: "green",
                    });

                    await frm.reload_doc();

                } catch (error) {
                    console.error(error);

                    const errorText =
                        error?.message ||
                        error?.exc ||
                        "";

                    const isDeadlock =
                        /deadlock|concurrent conflicting|record has changed/i
                            .test(errorText);

                    frappe.msgprint({
                        title: isDeadlock
                            ? __("Scheduling Conflict")
                            : __("Interview Scheduling Failed"),
                        indicator: isDeadlock
                            ? "orange"
                            : "red",
                        message: isDeadlock
                            ? __(
                                "Another update happened at the same time. Nothing was sent to Google Calendar. Please retry with the same or a different time."
                            )
                            : (
                                errorText ||
                                __("Unable to schedule interview.")
                            ),
                    });
                }
            },
        });

        dialog.show();

    } catch (error) {
        console.error(error);

        frappe.msgprint({
            title: __("Interview Plan Failed"),
            indicator: "red",
            message:
                error?.message ||
                __("Unable to load interview plan."),
        });
    }
}
