frappe.ui.form.on('Print Enquiry', {
	refresh: function(frm) {
		if (frm.is_new()) return;

		if (!frm.doc.linked_estimate) {
			frm.add_custom_button('Convert to Estimate', function() {
				if (!frm.doc.customer) {
					frappe.msgprint('Link an existing Customer before converting to an estimate.');
					return;
				}
				frm.call('make_print_estimate').then(r => {
					if (r.message) {
						frappe.set_route('Form', 'Print Estimate', r.message);
					}
				});
			}).addClass('btn-primary');
		} else {
			frm.add_custom_button('View Estimate', function() {
				frappe.set_route('Form', 'Print Estimate', frm.doc.linked_estimate);
			});
		}
	}
});
