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
            padding: 12px 0 18px;
        ">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:12px;
                margin-bottom:12px;
            ">
                <div>
                    <div style="
                        font-size:15px;
                        font-weight:600;
                    ">
                        ${__("Interview Resources")}
                    </div>
                    <div class="text-muted">
                        ${__("Resume, Google Meet and Calendar")}
                    </div>
                </div>

                <span class="indicator-pill ${statusColor}">
                    ${frappe.utils.escape_html(syncStatus)}
                </span>
            </div>

            <div style="
                display:flex;
                gap:8px;
                flex-wrap:wrap;
                align-items:center;
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
                        <button
                            class="btn btn-primary btn-sm"
                            data-generate-meet
                        >
                            ${__(
                                syncStatus === "Queued"
                                    ? "Refresh Meet"
                                    : "Generate Google Meet"
                            )}
                        </button>
                        `
                }

                ${
                    calendarUrl
                        ? `
                        <button
                            class="btn btn-default btn-sm"
                            data-open-calendar
                        >
                            ${__("Open Calendar")}
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
                            ${__("View Event")}
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

    field.$wrapper
        .find("[data-generate-meet]")
        .on("click", async () => {
            try {
                const result = await frappe.call({
                    method:
                        "unbound_hr.api.interviews.ensure_interview_google_meet",
                    args: {
                        interview_name: frm.doc.name,
                    },
                    freeze: true,
                    freeze_message:
                        __("Creating Google Meet..."),
                });

                const response =
                    result.message || {};

                if (!response.success) {
                    frappe.throw(
                        __("Unable to create Google Meet.")
                    );
                }

                frappe.show_alert({
                    message:
                        response.status === "Synced"
                            ? __("Google Meet ready")
                            : __("Google Meet is being created"),
                    indicator: "green",
                });

                await frm.reload_doc();

                // Give background worker a moment and refresh again.
                if (
                    response.status === "Queued"
                ) {
                    setTimeout(
                        () => frm.reload_doc(),
                        2500
                    );
                }
            } catch (error) {
                console.error(error);

                frappe.msgprint({
                    title: __("Google Meet Failed"),
                    indicator: "red",
                    message:
                        error?.message ||
                        __("Unable to create Google Meet."),
                });
            }
        });
}
