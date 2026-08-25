frappe.pages["unbound-ats"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Unbound ATS"),
        single_column: true,
    });

    new UnboundATS(page);
};


class UnboundATS {
    constructor(page) {
        this.page = page;
        this.selected = new Set();
        this.applicants = [];

        this.make_filters();
        this.make_layout();
        this.make_actions();

        this.load_job_openings();
    }


    make_filters() {
        this.job_opening = this.page.add_field({
            label: __("Job Opening"),
            fieldtype: "Link",
            options: "Job Opening",
            fieldname: "job_opening",
            change: () => this.refresh(),
        });

        this.stage = this.page.add_field({
            label: __("ATS Stage"),
            fieldtype: "Select",
            fieldname: "ats_stage",
            options: [
                "",
                "New Applicant",
                "Processing",
                "Screening",
                "HR Review",
                "Shortlisted",
                "Selection Mail Sent",
                "Interview Scheduled",
                "Interview Round 1",
                "Interview Round 2",
                "Final Review",
                "Selected",
                "Offer Sent",
                "Joined",
                "Rejected",
                "On Hold",
            ].join("\n"),
            change: () => this.refresh(),
        });

        this.processing = this.page.add_field({
            label: __("Processing"),
            fieldtype: "Select",
            fieldname: "processing_status",
            options: [
                "",
                "Not Processed",
                "Queued",
                "Processing",
                "Completed",
                "Failed",
            ].join("\n"),
            change: () => this.refresh(),
        });

        this.sort = this.page.add_field({
            label: __("Sort"),
            fieldtype: "Select",
            fieldname: "sort",
            options: [
                { label: __("ATS Score: High to Low"), value: "score_desc" },
                { label: __("ATS Score: Low to High"), value: "score_asc" },
                { label: __("Newest"), value: "newest" },
                { label: __("Oldest"), value: "oldest" },
            ],
            default: "score_desc",
            change: () => this.refresh(),
        });
    }


    make_actions() {
        this.page.add_inner_button(
            __("Shortlist Selected"),
            () => this.shortlist_selected(),
            __("Actions")
        );

        this.page.add_inner_button(
            __("Reject Selected"),
            () => this.bulk_stage("Rejected"),
            __("Actions")
        );

        this.page.add_inner_button(
            __("Move to HR Review"),
            () => this.bulk_stage("HR Review"),
            __("Actions")
        );

        this.page.set_primary_action(
            __("Refresh"),
            () => this.refresh()
        );
    }


    make_layout() {
        this.page.main.html(`
            <div class="unbound-ats">
                <div class="ats-summary">
                    <div>
                        <div class="ats-label">Applicants</div>
                        <div class="ats-number" data-ats-count>0</div>
                    </div>

                    <div class="ats-search-wrap">
                        <input
                            type="text"
                            class="form-control ats-search"
                            placeholder="Search candidate name or email..."
                        />
                    </div>
                </div>

                <div class="ats-toolbar">
                    <div data-selection-count>0 selected</div>
                </div>

                <div class="ats-table-wrap">
                    <table class="table table-hover ats-table">
                        <thead>
                            <tr>
                                <th style="width:36px">
                                    <input type="checkbox" data-select-all />
                                </th>

                                <th>Candidate</th>
                                <th>Job Opening</th>
                                <th>Source</th>
                                <th>ATS Score</th>
                                <th>Skills</th>
                                <th>Experience</th>
                                <th>Stage</th>
                                <th>Processing</th>
                            </tr>
                        </thead>

                        <tbody data-applicant-rows>
                            <tr>
                                <td colspan="9" class="text-muted text-center">
                                    Select a Job Opening
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `);

        this.search_input = this.page.main.find(".ats-search");

        let search_timer;

        this.search_input.on("input", () => {
            clearTimeout(search_timer);

            search_timer = setTimeout(
                () => this.refresh(),
                300
            );
        });

        this.page.main
            .find("[data-select-all]")
            .on("change", (event) => {
                const checked = event.target.checked;

                this.page.main
                    .find(".ats-row-checkbox")
                    .prop("checked", checked);

                this.selected.clear();

                if (checked) {
                    this.applicants.forEach((row) => {
                        this.selected.add(row.name);
                    });
                }

                this.update_selection_count();
            });

        this.add_styles();
    }


    add_styles() {
        if (document.getElementById("unbound-ats-styles")) {
            return;
        }

        const style = document.createElement("style");

        style.id = "unbound-ats-styles";

        style.innerHTML = `
            .unbound-ats {
                padding: 18px 0;
            }

            .ats-summary {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 24px;
                padding: 18px;
                border: 1px solid var(--border-color);
                border-radius: 10px;
                margin-bottom: 16px;
                background: var(--card-bg);
            }

            .ats-label {
                color: var(--text-muted);
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: .05em;
            }

            .ats-number {
                font-size: 30px;
                font-weight: 600;
            }

            .ats-search-wrap {
                width: min(460px, 100%);
            }

            .ats-toolbar {
                display: flex;
                justify-content: flex-end;
                margin-bottom: 8px;
                color: var(--text-muted);
                font-size: 13px;
            }

            .ats-table-wrap {
                border: 1px solid var(--border-color);
                border-radius: 10px;
                overflow-x: auto;
                background: var(--card-bg);
            }

            .ats-table {
                margin-bottom: 0;
            }

            .ats-table th {
                white-space: nowrap;
                font-size: 12px;
                color: var(--text-muted);
            }

            .candidate-link {
                font-weight: 600;
                cursor: pointer;
            }

            .candidate-email {
                color: var(--text-muted);
                font-size: 12px;
                margin-top: 3px;
            }

            .ats-score {
                font-weight: 600;
            }

            .ats-stage {
                display: inline-flex;
                padding: 4px 8px;
                border-radius: 999px;
                background: var(--subtle-fg);
                font-size: 12px;
                white-space: nowrap;
            }

            .unbound-candidate-detail {
                padding: 8px 4px;
            }

            .candidate-detail-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 24px;
            }

            .candidate-detail-header h3 {
                margin-top: 0;
                margin-bottom: 6px;
            }

            .candidate-score-box {
                min-width: 120px;
                text-align: center;
                border: 1px solid var(--border-color);
                border-radius: 10px;
                padding: 14px;
            }

            .candidate-score-label {
                font-size: 11px;
                color: var(--text-muted);
            }

            .candidate-score-value {
                font-size: 30px;
                font-weight: 700;
            }

            .candidate-metric {
                font-size: 22px;
                font-weight: 600;
                margin-top: 5px;
            }

            .candidate-section {
                margin-top: 18px;
            }

            .candidate-detail-actions {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
        `;

        document.head.appendChild(style);
    }


    async load_job_openings() {
        try {
            const result = await frappe.call({
                method: "unbound_hr.api.ats.get_job_openings",
            });

            const openings = result.message || [];

            if (openings.length === 1) {
                this.job_opening.set_value(openings[0].name);
                await this.refresh();
            }
        } catch (error) {
            console.error(error);
        }
    }


    async refresh() {
        const job_opening = this.job_opening.get_value();

        if (!job_opening) {
            this.render_empty(
                __("Select a Job Opening to view applicants.")
            );

            return;
        }

        this.selected.clear();
        this.update_selection_count();

        this.render_loading();

        try {
            const response = await frappe.call({
                method: "unbound_hr.api.ats.get_applicants",

                args: {
                    job_opening,
                    search: this.search_input.val() || "",
                    ats_stage: this.stage.get_value() || "",
                    processing_status: this.processing.get_value() || "",
                    sort: this.sort.get_value() || "score_desc",
                },
            });

            const result = response.message || {};

            this.applicants = result.applicants || [];

            this.page.main
                .find("[data-ats-count]")
                .text(result.count || 0);

            this.render_rows();
        } catch (error) {
            console.error(error);

            this.render_empty(
                __("Unable to load applicants.")
            );
        }
    }


    render_loading() {
        this.page.main
            .find("[data-applicant-rows]")
            .html(`
                <tr>
                    <td colspan="9" class="text-center text-muted">
                        Loading applicants...
                    </td>
                </tr>
            `);
    }


    render_empty(message) {
        this.applicants = [];

        this.page.main
            .find("[data-ats-count]")
            .text("0");

        this.page.main
            .find("[data-applicant-rows]")
            .html(`
                <tr>
                    <td colspan="9" class="text-center text-muted">
                        ${frappe.utils.escape_html(message)}
                    </td>
                </tr>
            `);
    }


    render_rows() {
        const tbody = this.page.main.find(
            "[data-applicant-rows]"
        );

        if (!this.applicants.length) {
            this.render_empty(
                __("No applicants found for this Job Opening.")
            );

            return;
        }

        const rows = this.applicants.map((row) => {
            const score =
                row.custom_ats_score !== null &&
                row.custom_ats_score !== undefined
                    ? Number(row.custom_ats_score).toFixed(1)
                    : "—";

            const skills =
                row.custom_skills_match !== null &&
                row.custom_skills_match !== undefined
                    ? `${Number(row.custom_skills_match).toFixed(0)}%`
                    : "—";

            const experience =
                row.custom_experience_match !== null &&
                row.custom_experience_match !== undefined
                    ? `${Number(row.custom_experience_match).toFixed(0)}%`
                    : "—";

            return `
                <tr>
                    <td>
                        <input
                            type="checkbox"
                            class="ats-row-checkbox"
                            data-name="${frappe.utils.escape_html(row.name)}"
                        />
                    </td>

                    <td>
                        <div
                            class="candidate-link"
                            data-open-applicant="${frappe.utils.escape_html(row.name)}"
                        >
                            ${frappe.utils.escape_html(
                                row.applicant_name || row.name
                            )}
                        </div>

                        <div class="candidate-email">
                            ${frappe.utils.escape_html(
                                row.email_id || ""
                            )}
                        </div>
                    </td>

                    <td>
                        ${frappe.utils.escape_html(
                            row.job_opening_name || row.job_title || "—"
                        )}
                    </td>

                    <td>
                        ${frappe.utils.escape_html(
                            row.source || row.custom_source_type || "—"
                        )}
                    </td>

                    <td class="ats-score">
                        ${score}
                    </td>

                    <td>${skills}</td>

                    <td>${experience}</td>

                    <td>
                        <span class="ats-stage">
                            ${frappe.utils.escape_html(
                                row.custom_ats_stage || "New Applicant"
                            )}
                        </span>
                    </td>

                    <td>
                        ${frappe.utils.escape_html(
                            row.custom_processing_status || "Not Processed"
                        )}
                    </td>
                </tr>
            `;
        });

        tbody.html(rows.join(""));

        tbody
            .find(".ats-row-checkbox")
            .on("change", (event) => {
                const name = event.target.dataset.name;

                if (event.target.checked) {
                    this.selected.add(name);
                } else {
                    this.selected.delete(name);
                }

                this.update_selection_count();
            });

        tbody
            .find("[data-open-applicant]")
            .on("click", async (event) => {
                const name =
                    event.currentTarget.dataset.openApplicant;

                await window.UnboundCandidateDetail.show(
                    name,
                    this
                );
            });
    }


    update_selection_count() {
        this.page.main
            .find("[data-selection-count]")
            .text(
                __("{0} selected", [this.selected.size])
            );
    }


    async shortlist_selected() {
        if (!this.selected.size) {
            frappe.msgprint(
                __("Select at least one applicant.")
            );
            return;
        }

        frappe.confirm(
            __(
                "Shortlist {0} applicant(s) and send the selection email?",
                [this.selected.size]
            ),
            async () => {
                const result = await frappe.call({
                    method:
                        "unbound_hr.api.ats.shortlist_and_send_email",

                    args: {
                        applicants: Array.from(this.selected),
                    },

                    freeze: true,
                    freeze_message:
                        __("Sending shortlist emails..."),
                });

                const response = result.message || {};

                if (response.failed_count) {
                    frappe.msgprint({
                        title: __("Shortlisting Complete"),
                        indicator: "orange",
                        message: __(
                            "{0} email(s) queued. {1} failed.",
                            [
                                response.sent_count || 0,
                                response.failed_count || 0,
                            ]
                        ),
                    });
                } else {
                    frappe.show_alert({
                        message: __(
                            "{0} candidate(s) shortlisted",
                            [response.sent_count || 0]
                        ),
                        indicator: "green",
                    });
                }

                await this.refresh();
            }
        );
    }


    bulk_stage(stage) {
        if (!this.selected.size) {
            frappe.msgprint(
                __("Select at least one applicant.")
            );

            return;
        }

        frappe.confirm(
            __(
                "Move {0} applicant(s) to {1}?",
                [this.selected.size, stage]
            ),
            async () => {
                await frappe.call({
                    method: "unbound_hr.api.ats.bulk_update_stage",

                    args: {
                        applicants: Array.from(this.selected),
                        stage,
                    },

                    freeze: true,
                    freeze_message: __("Updating applicants..."),
                });

                frappe.show_alert({
                    message: __("Applicants updated"),
                    indicator: "green",
                });

                await this.refresh();
            }
        );
    }
}
