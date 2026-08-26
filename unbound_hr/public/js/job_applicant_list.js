frappe.listview_settings["Job Applicant"] = {
    onload(listview) {
        listview.page.add_inner_button(
            __("Open Unbound ATS"),
            () => {
                frappe.set_route("unbound-ats");
            }
        );
    },
};
