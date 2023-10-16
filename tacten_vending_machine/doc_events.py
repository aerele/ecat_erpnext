import frappe,json
import calendar
from datetime import datetime
from frappe.utils import (
	add_days,
	add_months
)
from frappe.utils import today
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
def contract_before_save(self,method):
	if self.document_type and self.document_name:
		ref_doc = frappe.get_doc(self.document_type, self.document_name)
		self.custom_items = []
		for item in ref_doc.items:
			new_item = {
				"item_code": item.item_code,
				"item_name": item.item_name,
				"qty": item.qty,
				"description": item.description,
				"rate": item.rate,
				"amount": item.amount,
				"uom": item.uom,
				"conversion_factor": item.conversion_factor
			}
			self.append("custom_items", new_item)
			
		self.run_method("set_missing_values")

def qtn_before_save(self,method):
	if self.quotation_to == "Customer" and self.selling_price_list == "Standard Selling":
		pl_doc = frappe.db.exists("Price List", self.party_name)
		if not pl_doc:
			pl_doc = frappe.get_doc(dict(
				enabled= 1,
				doctype = 'Price List',
				price_list_name = self.party_name,
				currency = self.currency,
				selling = 1
			)).insert()
			
			pl_doc = pl_doc.name
		
		new_price = False
		for item in self.items:
			exists = frappe.get_list('Item Price', {"item_code": item.item_code, "price_list": pl_doc, "valid_from": self.transaction_date })
			
			if not exists:
				new_price = True
				frappe.get_doc(dict(
					doctype = 'Item Price',
					item_code= item.item_code,
					price_list= pl_doc,
					price_list_rate= item.rate,
					valid_from = self.transaction_date,
					customer = self.party_name
				)).insert()
		if self.customer_name and pl_doc:
			cus_doc= frappe.get_doc("Customer", self.customer_name)
			cus_doc.default_price_list = pl_doc
			cus_doc.save()
		
		if pl_doc:
			self.selling_price_list = pl_doc

def po_before_save(self,method):
	for item in self.items:
		item.custom_tax_rate = 0
		if item.get("item_tax_rate"):
			item_tax = json.loads(item.get("item_tax_rate"))
			for tax_row in self.taxes:
				if item_tax.get(tax_row.get("account_head")):
					item.custom_tax_rate = item.custom_tax_rate + item_tax.get(tax_row.get("account_head"))
		item.custom_tax_amount = item.amount * item.custom_tax_rate / 100

def si_before_save(self,method):
	contracts = frappe.db.get_value("Contract",{"start_date":["<=",self.posting_date],"end_date":[">=",self.posting_date],"party_name":self.customer,"is_signed":1,"docstatus":1})
	if not contracts:
		return
	doc = frappe.get_doc("Contract",contracts)
	if not doc.custom_is_monthly_billing:
		frappe.throw("Please set Monthly Billing period in Contract to bill")
	if doc.custom_is_monthly_billing:
		billing_cycle = doc.custom_monthly_billing_cycle
		cycle_day = int(billing_cycle.split(" ")[1].replace("st","").replace("nd","").replace("rd","").replace("th",""))
		year = datetime.strptime(self.posting_date, "%Y-%m-%d").year
		month = datetime.strptime(self.posting_date, "%Y-%m-%d").month
		end_date = get_date_of_day(year,month,cycle_day)
		start_date = add_days(end_date,-29)
		out_contract_dn = []
		total_amt = machine_qty = 0
		for item in self.items:
			if frappe.db.get_value("Item",{"name":item.item_code,"item_group":"Coffee Vending Machine"}):
				machine_qty += item.qty
			else:
				total_amt += item.amount
			if item.delivery_note:
				if frappe.db.get_value("Delivery Note",{"name":item.delivery_note,"posting_date":["<",start_date]}) or frappe.db.get_value("Delivery Note",{"name":item.delivery_note,"posting_date":[">",end_date]}):
					out_contract_dn.append(item.delivery_note)
		if len(out_contract_dn):
			frappe.throw("Invoice consists of Delivery Notes out of contract Period<br>{0}".format(", ".join(["<b>{0}</b>".format(f) for f in out_contract_dn])))
	if doc.custom_billing_type == "Slab Based Billing":
		rental_rate = orig_qty = is_in_range_full = is_out_range = is_in_range_partial= 0
		for slab in doc.custom_slab_definitions:
			if total_amt >= slab.consumable_amount:
				
				if (total_amt//slab.consumable_amount) >= machine_qty:
					is_in_range_full = 1
					orig_qty = machine_qty
					rental_rate = slab.out_range_rent
				else:
					is_in_range_partial = 1
					orig_qty = abs((total_amt//slab.consumable_amount)-machine_qty)
					rental_rate_out = slab.out_range_rent
					rental_rate_in = slab.in_range_rent
			else:
				is_out_range = 1
				rental_rate = slab.in_range_rent
				orig_qty = machine_qty
		for item in self.items:
			if frappe.db.get_value("Item",{"name":item.item_code,"item_group":"Coffee Vending Machine"}):
				if is_in_range_full:
					item.qty = orig_qty
					item.rate = rental_rate
					item.amount = item.qty*rental_rate
				elif is_out_range:
					item.rate = rental_rate
					item.amount = orig_qty*rental_rate
				elif is_in_range_partial:
					extra_row = item.as_dict()
					item.qty = orig_qty
					item.rate = rental_rate_in

					
		if is_in_range_partial and orig_qty!=machine_qty:
			del extra_row["name"]
			del extra_row["modified"]
			del extra_row["creation"]
			del extra_row["idx"]
			extra_row["qty"] = extra_row["qty"]-orig_qty
			extra_row["rate"] = rental_rate_out
			extra_row["amount"] = extra_row["qty"]*extra_row["rate"]
			self.append("items",extra_row)
	elif doc.custom_billing_type == "Package Based Billing":
		item_list = {}
		total_amt = 0
		non_package_items = []
		extra_qty_items = {}
		package_items = frappe.db.get_list("Package Definition",{"parent":doc.name},pluck="item")
		for item in self.items:
			if not item.item_code in item_list and item.item_code in package_items:
				item_list[item.item_code] = {"qty":item.qty,"amount":item.amount}
				total_amt += item.amount
			elif item.item_code in item_list and item.item_code in package_items:
				item_list[item.item_code]["qty"] += item.qty
				item_list[item.item_code]["amount"] += item.amount
				total_amt += item.amount
			if item.item_code not in package_items and item.item_group!="Coffee Vending Machine":
				non_package_items.append(item.item_code)
		if not total_amt >= doc.custom_package_rate:
			for item in self.items:
				if item.item_group == "Coffee Vending Machine":
					item.rate = doc.custom_noncompliance_rental_amount
					item.amount = doc.custom_noncompliance_rental_amount*item.qty
		if len(non_package_items):
			frappe.msgprint("Invoice consists of non - package items:<br>{0}".format(", ".join(["<b>{0}</b>".format(f) for f in non_package_items])))
		for contract in doc.custom_package_definition:
			if contract.item in item_list and item_list[contract.item]["qty"] > (contract.qty+contract.carry_forwarded_qty):
				extra_qty_items[contract.item] = {"additional_qty":item_list[contract.item]["qty"]-(contract.qty+contract.carry_forwarded_qty)}
		if len(extra_qty_items):
			frappe.msgprint("Invoice consists of items with additional package quantities:<br>{0}".format("<br>".join(["<b>{0}</b> - <b>{1} units</b>".format(f,extra_qty_items[f]["additional_qty"]) for f in extra_qty_items])))
	super(SalesInvoice, self).validate()

def get_date_of_day(year, month, target_day):
	try:
		last_day = calendar.monthrange(year, month)[1]
		if 1 <= target_day <= last_day:
			return f"{year}-{month:02d}-{target_day:02d}"
		return f"{year}-{month:02d}-{last_day:02d}"

	except ValueError:
		return "Invalid date"

def set_carry_fwd_qty_in_pkg():
	frst_month = datetime.now()
	if not frst_month.day == 1:
		return
	contract_list = frappe.db.get_list("Contract",{"custom_billing_type":"Package Based Billing","is_signed":1,"docstatus":1,"start_date":["<=",today()],"end_date":[">=",today()]},pluck="name")
	for contract in contract_list:
		doc = frappe.get_doc("Contract",contract)
		billing_cycle = doc.custom_monthly_billing_cycle
		cycle_day = int(billing_cycle.split(" ")[1].replace("st","").replace("nd","").replace("rd","").replace("th",""))
		year = datetime.strptime(today(), "%Y-%m-%d").year
		month = datetime.strptime(today(), "%Y-%m-%d").month-1
		end_date = get_date_of_day(year,month,cycle_day)
		start_date = add_days(end_date,-29)
		pkg_items = frappe.db.get_list("Package Definition",{"parent":contract},pluck="item")
		data = frappe.db.sql('''select di.item_code as item,sum(di.qty) as qty from `tabDelivery Note` as d join `tabDelivery Note Item` as di on di.parent=d.name where d.posting_date >= '{0}' and d.posting_date <= '{1}' and 
		d.docstatus = 1 and d.customer = '{2}' and di.item_code in ({3}) group by di.item_code '''.format(start_date,end_date,doc.party_name,",".join("'{0}'".format(f) for f in pkg_items)),as_dict = 1)
		# pkg_details = frappe.db.get_list("Package Definition",{"parent":contract},["item","qty","carry_forwarded_qty"])
		for pkg_item in doc.custom_package_definition:
			for item in data:
				if item["item"] == pkg_item.item and item["qty"] < (pkg_item.qty+pkg_item.carry_forwarded_qty):
					cfq = (pkg_item.qty+pkg_item.carry_forwarded_qty)-item["qty"]
					frappe.db.sql('''update `tabPackage Definition` set carry_forwarded_qty = {0} where parent = '{1}' and item = '{2}' '''.format(cfq,contract,pkg_item.item))
					frappe.db.commit()
					break





