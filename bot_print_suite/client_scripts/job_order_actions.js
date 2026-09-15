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
								frappe.msgprint({
									title: 'Production Started',
									message: `Work Order <a href="/app/work-order/${r.message.work_order}">${r.message.work_order}</a> created and submitted.<br>` +
										`Material Transfer <a href="/app/stock-entry/${r.message.material_transfer}">${r.message.material_transfer}</a> left as a draft for you to review.`,
									indicator: 'green',
								});
								frm.reload_doc();
							}
						},
					});
				}
			);
		}).addClass('btn-primary');
	}
});
