frappe.ui.form.on('Sales Order', {
	refresh: function(frm) {
		if (frm.is_new()) return;
		frappe.call({
			method: 'bot_print_suite.production.job_tracker.get_job_tracker_data',
			args: { sales_order: frm.doc.name },
			callback: function(r) {
				if (!r.message) return;
				render_job_tracker(frm, r.message);
			}
		});
	}
});

function render_job_tracker(frm, data) {
	const stages = data.stages;
	const completed = data.completed;
	const current = data.current_index;
	const n = stages.length;

	let dots = '';
	for (let i = 0; i < n; i++) {
		const cx = 5 + i * (90 / (n - 1));
		let color = '#d1d5db'; // gray - not yet reached
		let r = 5;
		if (completed[i]) { color = '#1D9E75'; } // teal - done
		if (i === current) { color = '#EF9F27'; r = 7; } // amber - current
		dots += `<circle cx="${cx}%" cy="18" r="${r}" fill="${color}"></circle>`;
		dots += `<text x="${cx}%" y="34" font-size="9" text-anchor="middle" fill="#6b7280">${stages[i]}</text>`;
	}

	const progress_pct = (current / (n - 1)) * 100;
	const line = `<div style="position:relative;height:2px;background:#e5e7eb;margin:0 5%;">
		<div style="position:absolute;left:0;top:0;height:2px;width:${progress_pct}%;background:#1D9E75;"></div>
	</div>`;

	const html = `
		<div style="padding:10px 0 24px 0;">
			<svg width="100%" height="40" style="overflow:visible;">${dots}</svg>
			<div style="text-align:center;font-size:12px;color:#374151;margin-top:2px;">
				<b>${stages[current]}</b> — ${data.status_line}
			</div>
		</div>`;

	if (!frm.job_tracker_wrapper) {
		frm.job_tracker_wrapper = $('<div class="job-tracker-strip"></div>').prependTo(frm.layout.wrapper);
	}
	frm.job_tracker_wrapper.html(html);
}
