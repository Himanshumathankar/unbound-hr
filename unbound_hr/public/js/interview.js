frappe.ui.form.on("Interview", {
    refresh(frm) {
        render_interview_resources(frm);
    },
});

function render_interview_resources(frm) {
    const resume = frm.doc.resume_link || "";
    const meet = frm.doc.custom_google_meet_link || "";
    const calendarUrl =
        frm.doc.custom_google_calendar_event_url || "";
    const eventName =
        frm.doc.custom_calendar_event || "";
    const syncStatus =
        frm.doc.custom_calendar_sync_status || "Not Synced";

    const field =
        frm.get_field("custom_interview_resources_html");

    if (!field) {
        return;
    }

    const statusClass = {
        Synced: "green",
        Queued: "orange",
        Failed: "red",
        "Not Synced": "gray",
    }[syncStatus] || "gray";

    const html = `
        <div style="
            width:100%;
            border:1px solid var(--border-color);
            border-radius:12px;
            padding:18px;
            margin:10px 0 18px;
        ">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:12px;
                margin-bottom:16px;
            ">
                <div>
                    <div style="
                        font-size:16px;
                        font-weight:600;
                    ">
                        ${__("Interview Resources")}
                    </div>

                    <div class="text-muted">
                        ${__("Resume, Google Meet and calendar")}
                    </div>
                </div>

                <span class="indicator-pill ${statusClass}">
                    ${frappe.utils.escape_html(syncStatus)}
                </span>
            </div>

            <div style="
                display:flex;
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
                        : ""
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
                                ${__("Open Google Calendar")}
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
