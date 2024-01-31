frappe.ui.form.on('Sales Invoice', {
	setup:function(frm){
        frm.set_query("custom_contract", () => {
			return {
				filters: {
					party_name: frm.doc.customer,
					is_signed : 1,
					docstatus : 1,
					start_date:["<=",frm.doc.posting_date],
					end_date:[">=",frm.doc.posting_date]
				}
			};
		});
	},
	refresh:function(frm){
		setTimeout(() => {
			cur_frm.page.remove_inner_button("Delivery Note","Get Items From")
			cur_frm.add_custom_button("Delivery Note",
			function() {
				if(!frm.doc.custom_contract){
					frappe.throw("Select Contract to fetch Delivery Notes")
				}
				erpnext.utils.map_current_doc({
					method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
					source_doctype: "Delivery Note",
					target: me.frm,
					date_field: "posting_date",
					setters: {
						customer: me.frm.doc.customer || undefined
					},
					get_query: function() {
						var filters = {
							docstatus: 1,
							company: me.frm.doc.company,
							posting_date:me.frm.doc.posting_date,
							contract:me.frm.doc.custom_contract,
							all_open_items:frm.doc.custom_show_all_open_items,
							is_return: 0
						};
						if(me.frm.doc.customer) filters["customer"] = me.frm.doc.customer;
						return {
							query: "tacten_vending_machine.doc_events.fetch_delivery_notes",
							filters: filters
						};
					}
				});
			},"Get Items From")
		},1000)

		
	},
	custom_contract:function(frm){
		if(frm.doc.custom_contract){
			frappe.db.get_list("Contract",{filters:{"name":frm.doc.custom_contract},fields:["custom_billing_type","custom_package_rate"]}).then((r)=>{
				if(r && r[0]["custom_billing_type"] == "Cup Based Billing"){
					frappe.db.get_list(
						"Cup Definition" , {filters:{"parent":frm.doc.custom_contract,"parenttype":"Contract"}, fields:['cup_name','cup_rate']}
					).then((res) => {
						frm.doc.items = []
						for(var i=0 ; i<res.length ; i++){
							let row = frm.add_child("items");
							row.item_code = res[i]["cup_name"]
							row.qty = 0
							row.rate = res[i]["cup_rate"]
							auto_fill_item_details(frm, res[i]["cup_name"],row)
						}
						frm.refresh_field("items")
					});
				}
				else if(r && r[0]["custom_billing_type"] == "Slab Based Billing"){
					frm.doc.items = []
					frappe.db.get_list(
						"Qtn Contract Items" , {filters:{"parent":frm.doc.custom_contract,"parenttype":"Contract"}, fields:['item_code','qty','rate','amount']}
					).then((qi) => {
						// for(var i=0 ; i<qi.length ; i++){
						// 	let row = frm.add_child("items");
						// 	row.item_code = qi[i]["item_code"]
						// 	row.qty = qi[i]["qty"]
						// 	row.rate = qi[i]["rate"]
						// 	row.amount = qi[i]['amount']
						// 	auto_fill_item_details(frm,qi[i]["item_code"],row)
						// }

					}).then(() => {
						let row = frm.add_child("items");
						row.item_code = "Vending Machine Rentals"
						row.qty = 1
						row.rate = 0
						auto_fill_item_details(frm,"Vending Machine Rentals",row)

					})
					
				}
				else if(r && r[0]["custom_billing_type"] == "Package Based Billing"){
					frappe.db.get_list(
						"Package Definition"  , {filters:{"parent":frm.doc.custom_contract,"parenttype":"Contract"}, fields:['item','qty']}
					).then((res) => {
						frm.doc.items = []
					// 	for(var i=0 ; i<res.length ; i++){
					// 		let row = frm.add_child("items");
					// 		row.item_code = res[i]["item"]
					// 		row.qty = res[i]["qty"]
					// 		row.rate = 0
					// 		row.amount = 0
					// 		auto_fill_item_details(frm,res[i]["item"],row)
							
					// 	}
						let row = frm.add_child("items");
						row.item_code = "Package Rental"
						row.qty = 1
						row.rate = r[0]["custom_package_rate"]
						row.amount = row.qty * r[0]["custom_package_rate"]
						auto_fill_item_details(frm,"Package Rental",row)
						frm.refresh_field("items")
					})
				}
			})
			
		}
	},
	
	
});
function auto_fill_item_details(frm,item_name,row){
	frappe.call({
		method: "erpnext.stock.get_item_details.get_item_details",
		args:{
			args: {
			item_code: item_name,
			barcode: row.barcode,
			serial_no: row.serial_no,
			batch_no: row.batch_no,
			set_warehouse: frm.doc.set_warehouse,
			warehouse: row.warehouse,
			customer: frm.doc.customer || frm.doc.party_name,
			quotation_to: frm.doc.quotation_to,
			supplier: frm.doc.supplier,
			currency: frm.doc.currency,
			conversion_rate: frm.doc.conversion_rate,
			price_list: frm.doc.selling_price_list || frm.doc.buying_price_list,
			price_list_currency: frm.doc.price_list_currency,
			plc_conversion_rate: frm.doc.plc_conversion_rate,
			company: frm.doc.company,
			order_type: frm.doc.order_type,
			is_pos: cint(frm.doc.is_pos),
			is_return: cint(frm.doc.is_return),
			is_subcontracted: frm.doc.is_subcontracted,
			ignore_pricing_rule: frm.doc.ignore_pricing_rule,
			doctype: frm.doc.doctype,
			name: frm.doc.name,
			project: row.project || frm.doc.project,
			qty: row.qty || 1,
			net_rate: row.rate,
			stock_qty: row.stock_qty,
			conversion_factor: row.conversion_factor,
			weight_per_unit: row.weight_per_unit,
			uom: row.uom,
			weight_uom: row.weight_uom,
			manufacturer: row.manufacturer,
			stock_uom: row.stock_uom,
			pos_profile: cint(frm.doc.is_pos) ? frm.doc.pos_profile : '',
			cost_center: row.cost_center,
			tax_category: frm.doc.tax_category,
			item_tax_template: row.item_tax_template,
			child_docname: row.name,
			is_old_subcontracting_flow: frm.doc.is_old_subcontracting_flow
			}
		},
		callback:function(r){
			var item = r.message
			row.item_name = item.item_name
			row.description = item.description
			row.uom = item.uom
			row.gst_hsn_code = item.gst_hsn_code
			row.income_account = item.income_account
			row.expense_account = item.expense_account
			row.warehouse = item.warehouse
			row.batch_no = item.batch_no
			frm.refresh_field("items")
			
		}
	})
}
// frappe.ui.form.on("Sales Invoice Item",{
// 	item_code(frm, cdt, cdn) {
// 		debugger
// 		var item = frappe.get_doc(cdt, cdn);
// 		var update_stock = 0, show_batch_dialog = 0;

// 		item.weight_per_unit = 0;
// 		item.weight_uom = '';
// 		item.conversion_factor = 0;

// 		if(['Sales Invoice'].includes(frm.doc.doctype)) {
// 			update_stock = cint(frm.doc.update_stock);
// 			show_batch_dialog = update_stock;
// 		}
// 		item.barcode = null;


// 		if(item.item_code || item.serial_no) {
// 			if(!validate_company_and_party()) {
// 				frm.fields_dict["items"].grid.grid_rows[item.idx - 1].remove();
// 			} else {
// 				item.pricing_rules = ''
// 				return frm.call({
// 					method: "erpnext.stock.get_item_details.get_item_details",
// 					child: item,
// 					args: {
// 						doc: frm.doc,
// 						args: {
// 							item_code: item.item_code,
// 							barcode: item.barcode,
// 							serial_no: item.serial_no,
// 							batch_no: item.batch_no,
// 							set_warehouse: frm.doc.set_warehouse,
// 							warehouse: item.warehouse,
// 							customer: frm.doc.customer || frm.doc.party_name,
// 							quotation_to: frm.doc.quotation_to,
// 							supplier: frm.doc.supplier,
// 							currency: frm.doc.currency,
// 							update_stock: update_stock,
// 							conversion_rate: frm.doc.conversion_rate,
// 							price_list: frm.doc.selling_price_list || frm.doc.buying_price_list,
// 							price_list_currency: frm.doc.price_list_currency,
// 							plc_conversion_rate: frm.doc.plc_conversion_rate,
// 							company: frm.doc.company,
// 							order_type: frm.doc.order_type,
// 							is_pos: cint(frm.doc.is_pos),
// 							is_return: cint(frm.doc.is_return),
// 							is_subcontracted: frm.doc.is_subcontracted,
// 							ignore_pricing_rule: frm.doc.ignore_pricing_rule,
// 							doctype: frm.doc.doctype,
// 							name: frm.doc.name,
// 							project: item.project || frm.doc.project,
// 							qty: item.qty || 1,
// 							net_rate: item.rate,
// 							stock_qty: item.stock_qty,
// 							conversion_factor: item.conversion_factor,
// 							weight_per_unit: item.weight_per_unit,
// 							uom: item.uom,
// 							weight_uom: item.weight_uom,
// 							manufacturer: item.manufacturer,
// 							stock_uom: item.stock_uom,
// 							pos_profile: cint(frm.doc.is_pos) ? frm.doc.pos_profile : '',
// 							cost_center: item.cost_center,
// 							tax_category: frm.doc.tax_category,
// 							item_tax_template: item.item_tax_template,
// 							child_docname: item.name,
// 							is_old_subcontracting_flow: frm.doc.is_old_subcontracting_flow,
// 						}
// 					},

// 					callback: function(r) {
// 						if(!r.exc) {
// 							frappe.run_serially([
// 								() => {
// 									var d = locals[cdt][cdn];
// 									add_taxes_from_item_tax_template(d.item_tax_rate);
// 									if (d.free_item_data && d.free_item_data.length > 0) {
// 										apply_product_discount(d);
// 									}
// 								},
// 								() => {
// 									// for internal customer instead of pricing rule directly apply valuation rate on item
// 									if ((frm.doc.is_internal_customer || frm.doc.is_internal_supplier) && frm.doc.represents_company === frm.doc.company) {
// 										get_incoming_rate(item, frm.posting_date, frm.posting_time,
// 											frm.doc.doctype, frm.doc.company);
// 									} else {
// 										frm.script_manager.trigger("price_list_rate", cdt, cdn);
// 									}
// 								},
// 								() => {
// 									if (frm.doc.is_internal_customer || frm.doc.is_internal_supplier) {
// 										calculate_taxes_and_totals();
// 									}
// 								},
// 								() => toggle_conversion_factor(item),
// 								() => {
// 									if (show_batch_dialog)
// 										return frappe.db.get_value("Item", item.item_code, ["has_batch_no", "has_serial_no"])
// 											.then((r) => {
// 												if (r.message &&
// 												(r.message.has_batch_no || r.message.has_serial_no)) {
// 													frappe.flags.hide_serial_batch_dialog = false;
// 												}
// 											});
// 								},
// 								() => {
// 									// check if batch serial selector is disabled or not
// 									if (show_batch_dialog && !frappe.flags.hide_serial_batch_dialog)
// 										return frappe.db.get_single_value('Stock Settings', 'disable_serial_no_and_batch_selector')
// 											.then((value) => {
// 												if (value) {
// 													frappe.flags.hide_serial_batch_dialog = true;
// 												}
// 											});
// 								},
// 								() => {
// 									if(show_batch_dialog && !frappe.flags.hide_serial_batch_dialog) {
// 										var d = locals[cdt][cdn];
// 										$.each(r.message, function(k, v) {
// 											if(!d[k]) d[k] = v;
// 										});

// 										if (d.has_batch_no && d.has_serial_no) {
// 											d.batch_no = undefined;
// 										}

// 										erpnext.show_serial_batch_selector(frm, d, (item) => {
// 											frm.script_manager.trigger('qty', item.doctype, item.name);
// 											if (!frm.doc.set_warehouse)
// 												frm.script_manager.trigger('warehouse', item.doctype, item.name);
// 											// apply_price_list(item, true);
// 										}, undefined, !frappe.flags.hide_serial_batch_dialog);
// 									}
// 								},
// 								() => conversion_factor(doc, cdt, cdn, true),
// 								() => remove_pricing_rule(item),
// 								() => {
// 									if (item.apply_rule_on_other_items) {
// 										let key = item.name;
// 										apply_rule_on_other_items({key: item});
// 									}
// 								},
// 								() => {
// 									var company_currency = get_company_currency();
// 									update_item_grid_labels(company_currency);
// 								}
// 							]);
// 						}
// 					}
// 				});
// 			}
// 		}
// 	}
// });