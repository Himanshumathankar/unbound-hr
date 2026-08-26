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

        // Native form header status indicator.
        frm.page.set_indicator(
            __(status),
            color
        );

        // Add a convenient ATS button on each applicant.
        frm.add_custom_button(
            __("Open in Unbound ATS"),
            () => {
                frappe.set_route("unbound-ats");
            }
        );

        // Give ATS Stage a visible indicator in the dashboard area.
        if (frm.doc.custom_ats_stage) {
            const ats_stage = frm.doc.custom_ats_stage;
            const ats_color =
                ats_colors[ats_stage] || "gray";

            frm.dashboard.add_indicator(
                __("ATS Stage: {0}", [ats_stage]),
                ats_color
            );
        }
    },
});
