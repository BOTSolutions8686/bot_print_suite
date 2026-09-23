frappe.web_form.after_load = function() {
		const optional_section = frappe.web_form.fields_dict.sb_additional;
		if (!optional_section) return;

		// Web Form Field does not carry DocField's `collapsible` property,
		// even though both use the same Section renderer. Enable the native
		// accessible section behavior here and start it closed, so customers
		// see only the six essentials unless they ask for more.
		optional_section.df.collapsible = 1;
		optional_section.head.addClass("collapsible").attr("tabindex", 0);
		optional_section.indicator.show();
		optional_section.head.off("click.optional-details").on("click.optional-details", function() {
			optional_section.collapse();
		});
		optional_section.head.off("keydown.optional-details").on("keydown.optional-details", function(event) {
			if (event.key === "Enter" || event.key === " ") {
				event.preventDefault();
				optional_section.collapse();
			}
		});
		optional_section.collapse(true);
};
