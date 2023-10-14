frappe.ui.form.on('Quotation', {
	selling_price_list: function(frm) {
		cur_frm.refresh_field("selling_price_list");
	}
});

frappe.ui.form.on('Quotation Item', {
	item_code: function(frm, cdt, cdn) {
		cur_frm.trigger("selling_price_list");
	}
});