frappe.ui.form.on('Sales Order', {
	refresh: function(frm) {
		if (frm.is_new() || frm.doc.docstatus !== 1) return;

		frm.add_custom_button('Upload Artwork', function() {
			frappe.db.get_list('Job Artwork', {
				filters: { sales_order: frm.doc.name },
				fields: ['name', 'version_no'],
				order_by: 'version_no desc',
				limit: 1,
			}).then(rows => {
				let next_version = rows.length ? rows[0].version_no + 1 : 1;
				frappe.new_doc('Job Artwork', {
					sales_order: frm.doc.name,
					version_no: next_version,
				});
			});
		});

		if (!frm.doc.custom_job_status || frm.doc.custom_job_status === 'Prepress') {
		frm.add_custom_button('Start Production', function() {
			frappe.confirm(
				'This will create the BOM, routing, Work Order, and a draft Material Transfer for this job. Continue?',
				function() {
					frappe.call({
						method: 'bot_print_suite.production.start_production.start_production',
						args: { sales_order_name: frm.doc.name },
						freeze: true,
						freeze_message: 'Building BOM, routing and Work Order...',
						callback: function(r) {
							if (r.message) {
								const heading = r.message.already_started ? 'Production Already Started' : 'Production Started';
								frappe.msgprint({
									title: heading,
									message: `Work Order: ${r.message.work_order}<br>Material Transfer: ${r.message.material_transfer || 'Not created'}`,
									indicator: 'green',
								});
								frm.reload_doc();
							}
						},
					});
				}
			);
		}).addClass('btn-primary');
		} else {
			frappe.db.get_value('Work Order', { sales_order: frm.doc.name }, 'name').then(r => {
				const work_order = r.message && r.message.name;
				if (work_order) {
					frm.add_custom_button('Open Work Order', () => frappe.set_route('Form', 'Work Order', work_order));
				}
			});
		}
	}
});
