frappe.ui.form.on("Interview", {
    refresh(frm) {
        render_unbound_interview_panel(frm);
    },
});


function render_unbound_interview_panel(frm) {
    const resume = frm.doc.resume_link || "";
    const meet = frm.doc.custom_google_meet_link || "";
    const calendarUrl =
        frm.doc.custom_google_calendar_event_url || "";
    const eventName =
        frm.doc.custom_calendar_event || "";
    const syncStatus =
        frm.doc.custom_calendar_sync_status || "Not Synced";

    const colors = {
        Synced: "green",
        Queued: "orange",
        Failed: "red",
        "Not Synced": "gray",
    };

    const indicatorColor =
        colors[syncStatus] || "gray";

    const html = `
        <div style="
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 18px;
            margin-top: 8px;
        ">
            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                margin-bottom:16px;
            ">
                <div>
                    <div style="
                        font-size:16px;
                        font-weight:600;
                    ">
                        ${__("Interview Resources")}
                    </div>

                    <div class="text-muted"
                         style="margin-top:2px;">
                        ${__("Resume, meeting and calendar details")}
                    </div>
                </div>

                <span class="indicator-pill ${indicatorColor}">
                    ${frappe.utils.escape_html(syncStatus)}
                </span>
            </div>

            <div style="
                display:grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(220px, 1fr));
                gap:12px;
            ">

                <div style="
                    border:1px solid var(--border-color);
                    border-radius:10px;
                    padding:14px;
                ">
                    <div class="text-muted">
                        ${__("Candidate Resume")}
                    </div>

                    <div style="margin-top:10px;">
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
                                        ${__("No resume attached")}
                                    </span>
                                `
                        }
                    </div>
                </div>

                <div style="
                    border:1px solid var(--border-color);
                    border-radius:10px;
                    padding:14px;
                ">
                    <div class="text-muted">
                        ${__("Google Meet")}
                    </div>

                    <div style="margin-top:10px;">
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
                                        ${
                                            syncStatus === "Queued"
                                                ? __("Meet link is being generated...")
                                                : __("No Meet link available")
                                        }
                                    </span>
                                `
                        }
                    </div>
                </div>

                <div style="
                    border:1px solid var(--border-color);
                    border-radius:10px;
                    padding:14px;
                ">
                    <div class="text-muted">
                        ${__("Google Calendar")}
                    </div>

                    <div style="
                        margin-top:10px;
                        display:flex;
                        gap:8px;
                        flex-wrap:wrap;
                    ">
                        ${
                            calendarUrl
                                ? `
                                    <button
                                        class="btn btn-default btn-sm"
                                        data-open-google-calendar
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
                                        data-open-frappe-event
                                    >
                                        ${__("View Event")}
                                    </button>
                                `
                                : ""
                        }

                        ${
                            !calendarUrl && !eventName
                                ? `
                                    <span class="text-muted">
                                        ${__("No calendar event available")}
                                    </span>
                                `
                                : ""
                        }
                    </div>
                </div>

            </div>
        </div>
    `;

    const field =
        frm.get_field("custom_interview_resources_html");

    if (!field) {
        return;
    }

    const wrapper = field.$wrapper;

    wrapper.html(html);

    wrapper
        .find("[data-view-resume]")
        .on("click", () => {
            window.open(resume, "_blank");
        });

    wrapper
        .find("[data-join-meet]")
        .on("click", () => {
            window.open(meet, "_blank");
        });

    wrapper
        .find("[data-open-google-calendar]")
        .on("click", () => {
            window.open(calendarUrl, "_blank");
        });

    wrapper
        .find("[data-open-frappe-event]")
        .on("click", () => {
            frappe.set_route(
                "Form",
                "Event",
                eventName
            );
        });
}
