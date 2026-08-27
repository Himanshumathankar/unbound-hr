frappe.ui.form.on("Interview", {
    refresh(frm) {
        render_interview_resources(frm);
    },
});

function render_interview_resources(frm) {
    const field =
        frm.get_field("custom_interview_resources_html");

    if (!field) {
        return;
    }

    const resume =
        frm.doc.resume_link || "";

    const meet =
        frm.doc.custom_google_meet_link || "";

    const calendarUrl =
        frm.doc.custom_google_calendar_event_url || "";

    const eventName =
        frm.doc.custom_calendar_event || "";

    const syncStatus =
        frm.doc.custom_calendar_sync_status ||
        "Not Synced";

    const statusColor = {
        Synced: "green",
        Queued: "orange",
        Failed: "red",
        "Not Synced": "gray",
    }[syncStatus] || "gray";

    const html = `
        <div style="
            width: 100%;
            padding: 16px 0 20px;
        ">
            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                gap:16px;
                margin-bottom:14px;
            ">
                <div>
                    <div style="
                        font-size:15px;
                        font-weight:600;
                    ">
                        ${__("Candidate & Meeting Resources")}
                    </div>

                    <div class="text-muted"
                         style="margin-top:2px;">
                        ${__("Resume, interview meeting and calendar")}
                    </div>
                </div>

                <span class="indicator-pill ${statusColor}">
                    ${frappe.utils.escape_html(syncStatus)}
                </span>
            </div>

            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                flex-wrap:wrap;
            ">
                ${
                    resume
                        ? `
                        <button
                            class="btn btn-default btn-sm"
                            data-view-resume
                        >
                            ${__("View Resume")}
                        </button>
                        `
                        : `
                        <span class="text-muted">
                            ${__("No resume")}
                        </span>
                        `
                }

                ${
                    meet
                        ? `
                        <button
                            class="btn btn-primary btn-sm"
                            data-join-meet
                        >
                            ${__("Join Google Meet")}
                        </button>
                        `
                        : `
                        <span class="text-muted">
                            ${__("Meet link not available")}
                        </span>
                        `
                }

                ${
                    calendarUrl
                        ? `
                        <button
                            class="btn btn-default btn-sm"
                            data-open-calendar
                        >
                            ${__("Open Calendar Event")}
                        </button>
                        `
                        : ""
                }

                ${
                    eventName
                        ? `
                        <button
                            class="btn btn-default btn-sm"
                            data-open-event
                        >
                            ${__("View Frappe Event")}
                        </button>
                        `
                        : ""
                }
            </div>
        </div>
    `;

    field.$wrapper.html(html);

    field.$wrapper
        .find("[data-view-resume]")
        .on("click", () => {
            window.open(resume, "_blank");
        });

    field.$wrapper
        .find("[data-join-meet]")
        .on("click", () => {
            window.open(meet, "_blank");
        });

    field.$wrapper
        .find("[data-open-calendar]")
        .on("click", () => {
            window.open(calendarUrl, "_blank");
        });

    field.$wrapper
        .find("[data-open-event]")
        .on("click", () => {
            frappe.set_route(
                "Form",
                "Event",
                eventName
            );
        });
}
