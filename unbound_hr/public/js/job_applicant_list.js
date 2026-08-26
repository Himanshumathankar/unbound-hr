frappe.listview_settings["Job Applicant"] = {
    onload(listview) {
        listview.page.add_inner_button(
            __("Open Unbound ATS"),
            () => {
                frappe.set_route("unbound-ats");
            }
        );
    },

    get_indicator(doc) {
        const status_colors = {
            Open: "orange",
            Replied: "blue",
            Shortlisted: "green",
            Rejected: "red",
            Hold: "orange",
            Accepted: "green",
        };

        const color =
            status_colors[doc.status] || "gray";

        return [
            __(doc.status || "Open"),
            color,
            `status,=,${doc.status || "Open"}`,
        ];
    },
};

frappe.listview_settings["Job Applicant"].formatters = {
    custom_ats_stage(value) {
        const colors = {
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

        const color = colors[value] || "gray";

        return `
            <span class="indicator-pill ${color}">
                ${frappe.utils.escape_html(value || "—")}
            </span>
        `;
    },
};

frappe.listview_settings["Job Applicant"].formatters = {
    custom_ats_stage(value) {
        const colors = {
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

        const color = colors[value] || "gray";

        return `
            <span class="indicator-pill ${color}">
                ${frappe.utils.escape_html(value || "—")}
            </span>
        `;
    },
};
