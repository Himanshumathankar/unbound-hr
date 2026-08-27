frappe.ui.form.on("Interview", {
    refresh(frm) {
        // Resume button
        if (frm.doc.resume_link) {
            frm.add_custom_button(
                __("View Resume"),
                () => {
                    window.open(
                        frm.doc.resume_link,
                        "_blank"
                    );
                }
            );
        }

        // Google Meet button
        if (frm.doc.custom_google_meet_link) {
            frm.add_custom_button(
                __("Join Google Meet"),
                () => {
                    window.open(
                        frm.doc.custom_google_meet_link,
                        "_blank"
                    );
                },
                __("Interview")
            );
        }

        // Google Calendar button
        if (
            frm.doc.custom_google_calendar_event_url
        ) {
            frm.add_custom_button(
                __("Open Calendar Event"),
                () => {
                    window.open(
                        frm.doc.custom_google_calendar_event_url,
                        "_blank"
                    );
                },
                __("Interview")
            );
        }

        // Local Frappe Event
        if (frm.doc.custom_calendar_event) {
            frm.add_custom_button(
                __("View Calendar Event"),
                () => {
                    frappe.set_route(
                        "Form",
                        "Event",
                        frm.doc.custom_calendar_event
                    );
                },
                __("Interview")
            );
        }

        // Calendar sync indicator
        const status =
            frm.doc.custom_calendar_sync_status;

        if (status) {
            const colors = {
                Queued: "orange",
                Synced: "green",
                Failed: "red",
            };

            frm.dashboard.add_indicator(
                __("Calendar: {0}", [status]),
                colors[status] || "gray"
            );
        }
    },
});
