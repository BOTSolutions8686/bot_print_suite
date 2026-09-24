frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		if (frm.is_new()) return;

		frappe.call({
			method: "bot_print_suite.production.job_tracker.get_job_tracker_data",
			args: { sales_order: frm.doc.name },
			callback(r) {
				if (r.message) render_job_tracker(frm, r.message);
			},
		});
	},
});

const JOB_STAGE_AR = {
	Enquiry: "الاستفسار",
	Estimate: "التكلفة",
	Quote: "عرض السعر",
	Approved: "الموافقة",
	Artwork: "التصميم",
	Production: "الإنتاج",
	Delivery: "التسليم",
	Invoiced: "الفاتورة",
};

function render_job_tracker(frm, data) {
	add_job_tracker_styles();

	const stages = data.stages || [];
	const current = Number(data.current_index || 0);
	const steps = stages.map((stage, index) => {
		const is_current = index === current;
		const is_done = Boolean(data.completed?.[index]) && !is_current;
		const state_class = is_current ? "is-current" : is_done ? "is-done" : "is-upcoming";
		const state_text = is_current ? __("Current step") : is_done ? __("Done") : __("Not started");
		const icon = is_done ? "✓" : String(index + 1);

		return `
			<li class="bps-job-step ${state_class}" aria-current="${is_current ? "step" : "false"}">
				<span class="bps-step-marker" aria-hidden="true">${icon}</span>
				<span class="bps-step-copy">
					<strong>${__(stage)}</strong>
					<span class="bps-step-ar" dir="rtl">${JOB_STAGE_AR[stage] || ""}</span>
					<small>${state_text}</small>
				</span>
			</li>`;
	}).join("");

	const next_action = get_next_action(data);
	const html = `
		<section class="bps-job-tracker" aria-label="${__("Job progress")}">
			<div class="bps-tracker-heading">
				<div>
					<div class="bps-eyebrow">${__("JOB PROGRESS")} · <span dir="rtl">مراحل العمل</span></div>
					<h3>${__("Current step")}: ${__(stages[current] || "")}</h3>
					<p>${__(data.status_line || "")}</p>
				</div>
				<div class="bps-progress-count">${current + 1} / ${stages.length}</div>
			</div>
			<ol class="bps-job-steps">${steps}</ol>
			<div class="bps-next-action">
				<span class="bps-next-icon" aria-hidden="true">→</span>
				<div><strong>${__("What happens next")}</strong><br>${__(next_action)}</div>
			</div>
		</section>`;

	if (!frm.job_tracker_wrapper) {
		frm.job_tracker_wrapper = $('<div class="job-tracker-strip"></div>').prependTo(frm.layout.wrapper);
	}
	frm.job_tracker_wrapper.html(html);
}

function get_next_action(data) {
	const status = data.status_line || "";
	const actions = {
		"Awaiting approval": "A sales manager reviews and approves the quotation.",
		"Artwork not uploaded": "Upload the customer artwork, then send it for approval.",
		"Artwork pending": "Send the artwork to the customer for approval.",
		"Awaiting customer approval": "Wait for the customer to approve the artwork.",
		"Revision requested": "Upload the revised artwork and send it to the customer again.",
		"Ready for production": "Start Production to create the work order and material request.",
		"Out for delivery": "Complete delivery, then create the sales invoice.",
		"Invoiced": "This job is complete. No further action is required.",
	};
	return actions[status] || "Complete the current step, then the job will move forward automatically.";
}

function add_job_tracker_styles() {
	if (document.getElementById("bps-job-tracker-styles")) return;

	$("<style>", {
		id: "bps-job-tracker-styles",
		text: `
			.bps-job-tracker { margin: 0 0 22px; padding: 20px; border: 1px solid #d8dee8; border-radius: 12px; background: #fff; box-shadow: 0 2px 8px rgba(15,23,42,.06); color: #1f2937; }
			.bps-tracker-heading { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:18px; }
			.bps-eyebrow { color:#64748b; font-size:12px; font-weight:700; letter-spacing:.08em; margin-bottom:5px; }
			.bps-tracker-heading h3 { margin:0 0 4px; font-size:20px; line-height:1.35; color:#172554; }
			.bps-tracker-heading p { margin:0; font-size:15px; color:#475569; }
			.bps-progress-count { flex:0 0 auto; min-width:64px; padding:8px 10px; border-radius:8px; background:#eff6ff; color:#1d4ed8; font-size:16px; font-weight:700; text-align:center; }
			.bps-job-steps { display:grid; grid-template-columns:repeat(8,minmax(92px,1fr)); gap:8px; padding:0; margin:0; list-style:none; overflow-x:auto; }
			.bps-job-step { min-height:108px; padding:12px 9px; border:2px solid #e2e8f0; border-radius:10px; background:#f8fafc; text-align:center; }
			.bps-step-marker { display:flex; align-items:center; justify-content:center; width:34px; height:34px; margin:0 auto 7px; border-radius:50%; background:#e2e8f0; color:#475569; font-size:16px; font-weight:800; }
			.bps-step-copy { display:flex; flex-direction:column; gap:1px; }
			.bps-step-copy strong { font-size:14px; color:#334155; }
			.bps-step-ar { min-height:17px; font-size:13px; color:#64748b; }
			.bps-step-copy small { margin-top:3px; font-size:11px; font-weight:700; color:#64748b; }
			.bps-job-step.is-done { border-color:#86efac; background:#f0fdf4; }
			.bps-job-step.is-done .bps-step-marker { background:#15803d; color:#fff; }
			.bps-job-step.is-done small { color:#166534; }
			.bps-job-step.is-current { border-color:#f59e0b; background:#fffbeb; box-shadow:0 0 0 2px rgba(245,158,11,.12); }
			.bps-job-step.is-current .bps-step-marker { background:#b45309; color:#fff; }
			.bps-job-step.is-current small { color:#92400e; }
			.bps-next-action { display:flex; align-items:center; gap:12px; margin-top:16px; padding:13px 15px; border-radius:9px; background:#eff6ff; color:#1e3a8a; font-size:14px; line-height:1.5; }
			.bps-next-icon { font-size:24px; font-weight:800; }
			@media (max-width: 991px) { .bps-job-steps { grid-template-columns:repeat(8,112px); } }
			@media (max-width: 575px) { .bps-job-tracker { padding:15px; } .bps-tracker-heading h3 { font-size:18px; } .bps-progress-count { font-size:14px; } }
		`,
	}).appendTo("head");
}
