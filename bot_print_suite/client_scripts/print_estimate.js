// Collapses every field's help text behind a small (i) icon next to its
// label, instead of always-visible text under every field - hover or
// click the icon to see it. Uses __() so the tooltip text itself
// respects the user's own language (Arabic users see the Arabic
// translation, if one exists for that description).
function make_toggle_icon(translated_desc, $target_to_toggle) {
	const is_rtl = frappe.utils.is_rtl();
	const $icon = $('<span class="description-toggle-icon">\u24d8</span>').attr({
		title: translated_desc,
	}).css({
		cursor: 'pointer', color: '#8d99a6', fontSize: '12px',
		[is_rtl ? 'marginRight' : 'marginLeft']: '5px',
	});
	$icon.on('click', function(e) {
		e.stopPropagation();
		$target_to_toggle.toggle();
	});
	return $icon;
}

function add_description_tooltips(frm) {
	// Regular fields (including checkboxes - their label has no
	// '.control-label' class, unlike every other fieldtype, so that
	// selector needs a fallback to a plain <label>).
	Object.values(frm.fields_dict).forEach(field => {
		if (!field.df.description || !field.$wrapper) return;
		const $wrapper = field.$wrapper;
		const $help = $wrapper.find('.help-box').first();
		let $label = $wrapper.find('label.control-label').first();
		if (!$label.length) $label = $wrapper.find('label').first();
		if (!$help.length || !$label.length) return;
		if ($label.find('.description-toggle-icon').length) return;  // already added

		$help.hide();
		$label.append(make_toggle_icon(__(field.df.description), $help));
	});

	// Section-level descriptions (Section Break fields aren't in
	// fields_dict at all - they render as plain DOM, found separately).
	frm.$wrapper.find('.form-section-description').each(function() {
		const $desc = $(this);
		const $head = $desc.closest('.form-section').find('.section-head').first();
		if (!$head.length) return;
		if ($head.find('.description-toggle-icon').length) return;  // already added

		const original_text = $desc.text().trim();
		$desc.hide();
		$head.append(make_toggle_icon(__(original_text), $desc));
	});
}

// Makes Sell Price visually dominate the page - it's the one number
// that matters most, and "bold" alone (Frappe's default for this
// field) doesn't make it stand out from any other bold text.
function emphasize_sell_price(frm) {
	const field = frm.fields_dict['sell_price'];
	if (!field || !field.$wrapper) return;
	const $value = field.$wrapper.find('.control-value, input.input-with-feedback').first();
	if (!$value.length) return;
	$value.css({ fontSize: '28px', fontWeight: '700', color: '#1B2A4A' });
}

// Makes an overridden cost-driver row visually obvious at a glance in
// the grid, instead of making someone read the Source column on every
// row to notice a manual override is in play. Runs on form refresh
// (covers opening a saved doc) and on the child table's own row-level
// trigger (covers ticking the checkbox live, before the next save).
function highlight_overridden_rows(frm) {
	const grid_field = frm.fields_dict.applied_cost_drivers;
	if (!grid_field || !grid_field.grid) return;
	(grid_field.grid.grid_rows || []).forEach(row => {
		if (!row.row) return;  // not rendered yet (e.g. collapsed grid)
		row.row.toggleClass('cost-driver-overridden', !!row.doc.cost_override_enabled);
	});
}

// Same idea as highlight_overridden_rows, but for the Ups field - a
// top-level field, not a grid row, so it needs its own light styling
// rather than reusing the grid-row CSS class.
function highlight_ups_override(frm) {
	const field = frm.fields_dict['ups'];
	if (!field || !field.$wrapper) return;
	const $value = field.$wrapper.find('.control-value, input.input-with-feedback').first();
	if (!$value.length) return;
	$value.css(frm.doc.ups_override_enabled
		? { backgroundColor: '#FFF7E0' }
		: { backgroundColor: '' });
}

// These two simple finishing inputs are convenience controls for rows in
// the native Cost Items grid. Keep the row state visible immediately; the
// server remains the single authority for rates and totals when the user saves.
function sync_cost_row_enabled(frm, role, enabled) {
	const row = (frm.doc.applied_cost_drivers || []).find(r =>
		r.calculation_role === role);
	if (!row || Boolean(row.enabled) === Boolean(enabled)) return Promise.resolve();
	return frappe.model.set_value(row.doctype, row.name, 'enabled', enabled ? 1 : 0)
		.then(() => frm.refresh_field('applied_cost_drivers'));
}

function sync_packing_override(frm) {
	const row = (frm.doc.applied_cost_drivers || []).find(r =>
		r.calculation_role === 'Packing');
	if (!row) return Promise.resolve();
	const manual = Boolean(frm.doc.packing_cost_override_enabled);
	frm.__bps_syncing_packing = true;
	return frappe.model.set_value(row.doctype, row.name, {
		cost_override_enabled: manual ? 1 : 0,
		cost_override: manual ? flt(frm.doc.packing_cost) : row.cost_override,
		override_reason: manual && !row.override_reason
			? __('Entered in Finishing & Delivery') : row.override_reason,
	}).then(() => frm.refresh_field('applied_cost_drivers'))
		.finally(() => { frm.__bps_syncing_packing = false; });
}

function prompt_finishing_recalculation(frm) {
	if (frm.is_new()) {
		frappe.show_alert({message: __('Save the estimate to calculate costs.'), indicator: 'blue'});
		return;
	}
	if (!frm.is_dirty()) return;
	frappe.show_alert({message: __('Finishing changed — click Save to recalculate costs.'), indicator: 'orange'}, 7);
}

// Injected once per page load - Frappe has no clean "add doctype CSS"
// hook for child table rows, so this is the standard escape hatch.
if (!document.getElementById('cost-driver-override-style')) {
	$('<style id="cost-driver-override-style">')
		.text('.cost-driver-overridden { background-color: #FFF7E0 !important; } ' +
			'.cost-driver-overridden .form-control:disabled { background-color: transparent !important; }')
		.appendTo('head');
}

frappe.ui.form.on('Print Estimate', {
	refresh: function(frm) {
		add_description_tooltips(frm);
		emphasize_sell_price(frm);
		highlight_overridden_rows(frm);
		highlight_ups_override(frm);

		// Small summary banner so a reviewer doesn't have to scroll the
		// whole cost table to notice something was manually adjusted.
		const overridden = (frm.doc.applied_cost_drivers || []).filter(r => r.cost_override_enabled);
		const notes = overridden.map(r => r.cost_driver);
		if (frm.doc.ups_override_enabled) notes.push('Ups per Sheet');
		if (notes.length && frm.dashboard && frm.dashboard.set_headline_alert) {
			frm.dashboard.set_headline_alert(
				`\u26A0\uFE0F ${notes.length} item${notes.length > 1 ? 's' : ''} manually overridden: ${frappe.utils.escape_html(notes.join(', '))}`,
				'orange'
			);
		}

		// The reconciliation table is stored as raw HTML in a hidden
		// Long Text field (an HTML fieldtype alone has no database
		// column - it can only show STATIC content baked into the
		// doctype, not a per-document computed value). This injects
		// the real, computed content into its own visible HTML field.
		if (frm.doc.reconciliation_table_data && frm.fields_dict.reconciliation_table_display) {
			const $container = frm.fields_dict.reconciliation_table_display.$wrapper;
			$container.html(frm.doc.reconciliation_table_data);

			// Formula icons in that table are plain server-rendered
			// HTML (not real Frappe fields), so a native `title`
			// attribute was the first attempt - but that's hover-only,
			// which doesn't work on touch and isn't discoverable for
			// someone not used to hovering. Delegated click handler
			// instead: a clear, unmissable popup, works the same on
			// mouse or touch. `.off().on()` avoids stacking a duplicate
			// handler on every refresh.
			$container.off('click', '.formula-icon').on('click', '.formula-icon', function() {
				frappe.msgprint({
					title: __($(this).data('item')),
					message: `<div style="font-size:14px;">${$(this).data('formula')}</div>`,
					indicator: 'blue',
				});
			});
		}

		// Apply Template button - for RE-applying or switching templates
		// on an estimate that's already been saved once. The FIRST
		// application happens automatically on save (see validate() in
		// print_estimate.py) - no click needed for the common case of
		// just picking a template on a new estimate.
		if (frm.doc.product_template && !frm.is_new()) {
			frm.add_custom_button('Apply Template', function() {
				frm.call('apply_template').then(() => frm.reload_doc());
			});
		}

		if (frm.is_new() || frm.is_dirty()) return;
		if (!frm.doc.sell_price) return;  // not yet computed - nothing to quote

		frm.add_custom_button('Create Quotation', function() {
			let qty_options = [frm.doc.quantity];
			(frm.doc.computed_breaks || []).forEach(r => qty_options.push(r.qty));

			if (qty_options.length === 1) {
				frm.call('create_quotation').then(r => {
					if (r.message) frappe.set_route('Form', 'Quotation', r.message);
				});
			} else {
				let d = new frappe.ui.Dialog({
					title: 'Which quantity should this quotation be for?',
					fields: [{
						fieldname: 'qty', fieldtype: 'Select', label: 'Quantity',
						options: qty_options.map(q => String(q)), reqd: 1,
						default: String(frm.doc.quantity),
					}],
					primary_action_label: 'Create Quotation',
					primary_action: (values) => {
						d.hide();
						frm.call('create_quotation', { qty: values.qty }).then(r => {
							if (r.message) frappe.set_route('Form', 'Quotation', r.message);
						});
					},
				});
				d.show();
			}
		}).addClass('btn-primary');
	},
	ups_override_enabled: function(frm) {
		highlight_ups_override(frm);
	},
	glue_sides: function(frm) {
		if (frm.__bps_syncing_finishing) return;
		frm.__bps_syncing_finishing = true;
		sync_cost_row_enabled(frm, 'Glue', cint(frm.doc.glue_sides) > 0)
			.finally(() => {
				frm.__bps_syncing_finishing = false;
				prompt_finishing_recalculation(frm);
			});
	},
	lamination_required: function(frm) {
		if (frm.__bps_syncing_finishing) return;
		frm.__bps_syncing_finishing = true;
		sync_cost_row_enabled(frm, 'Lamination', Boolean(frm.doc.lamination_required))
			.finally(() => {
				frm.__bps_syncing_finishing = false;
				prompt_finishing_recalculation(frm);
			});
	},
	packing_cost: function(frm) {
		if (frm.__bps_syncing_packing) return;
		sync_packing_override(frm).finally(() => prompt_finishing_recalculation(frm));
	},
	packing_cost_override_enabled: function(frm) {
		if (frm.__bps_syncing_packing) return;
		sync_packing_override(frm).finally(() => prompt_finishing_recalculation(frm));
	},
});

// Live row highlight the instant someone ticks the checkbox, without
// waiting for a save - the checkbox change fires on the child doctype,
// not the parent, so it needs its own handler even though the CSS
// class and helper function are shared with the parent's refresh.
frappe.ui.form.on('Print Estimate Cost Driver Line', {
	cost_override_enabled: function(frm, cdt, cdn) {
		highlight_overridden_rows(frm);
		const row = locals[cdt] && locals[cdt][cdn];
		if (!row || frm.__bps_syncing_packing ||
			row.calculation_role !== 'Packing') return;
		frm.__bps_syncing_packing = true;
		Promise.all([
			frm.set_value('packing_cost_override_enabled', row.cost_override_enabled ? 1 : 0),
			frm.set_value('packing_cost', row.cost_override_enabled ? flt(row.cost_override) : null),
		])
			.finally(() => { frm.__bps_syncing_packing = false; });
	},
	cost_override: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (frm.__bps_syncing_packing || !row.cost_override_enabled ||
			row.calculation_role !== 'Packing') return;
		frm.__bps_syncing_packing = true;
		frm.set_value('packing_cost', flt(row.cost_override))
			.finally(() => { frm.__bps_syncing_packing = false; });
	},
	enabled: function(frm, cdt, cdn) {
		if (frm.__bps_syncing_finishing) return;
		const row = locals[cdt][cdn];
		frm.__bps_syncing_finishing = true;
		let update = Promise.resolve();
		if (row.calculation_role === 'Lamination') {
			update = frm.set_value('lamination_required', row.enabled ? 1 : 0);
		} else if (row.calculation_role === 'Glue') {
			update = frm.set_value('glue_sides', row.enabled ? Math.max(1, cint(frm.doc.glue_sides)) : 0);
		}
		Promise.resolve(update).finally(() => {
			frm.__bps_syncing_finishing = false;
			prompt_finishing_recalculation(frm);
		});
	},
});
