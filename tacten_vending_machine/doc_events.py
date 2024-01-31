import frappe,json
import calendar
from datetime import datetime
from frappe.utils import (
	add_days,
	add_months,
	today
)
from frappe.utils import today
from erpnext.controllers.queries import get_fields
from frappe.desk.reportview import get_filters_cond, get_match_cond
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
def contract_before_save(self,method):
	if self.document_type and self.document_name:
		ref_doc = frappe.get_doc(self.document_type, self.document_name)
		item_dict = {}
		for item in self.custom_items:
			item_dict[item.item_code] = item.is_rental
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
				"conversion_factor": item.conversion_factor,
				"is_rental":item_dict[item.item_code] if item.item_code in item_dict else 0
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
	elif frappe.db.exists("Price List", self.party_name):
		for item in self.items:
			if item.item_code:
				frappe.db.set_value("Item Price",{"price_list":self.party_name,"item_code":item.item_code,"selling":1,"customer":self.party_name,"currency":self.currency},"valid_from",self.transaction_date)
				frappe.db.set_value("Item Price",{"price_list":self.party_name,"item_code":item.item_code,"selling":1,"customer":self.party_name,"currency":self.currency},"price_list_rate",item.rate)
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
	if not self.custom_contract:
		frappe.throw("Select Contract in this Invoice")
	contracts = self.custom_contract
	# contracts = frappe.db.get_value("Contract",{"start_date":["<=",self.posting_date],"end_date":[">=",self.posting_date],"party_name":self.customer,"is_signed":1,"docstatus":1})
	doc = frappe.get_doc("Contract",contracts)
	item_dict = {}
	for item in doc.custom_items:
		item_dict[item.item_code] = item.is_rental
	cycle_day = 0
	if not doc.custom_is_monthly_billing:
		frappe.throw("Please set Monthly Billing period in Contract to bill")
	billing_cycle = doc.custom_monthly_billing_cycle or "End of the Month"
	year = datetime.strptime(self.posting_date, "%Y-%m-%d").year
	month = datetime.strptime(self.posting_date, "%Y-%m-%d").month
	if not billing_cycle == "End of the Month":
		cycle_day = int(billing_cycle.split(" ")[1].replace("st","").replace("nd","").replace("rd","").replace("th",""))
	else:
		cycle_day = int(calendar.monthrange(year, month)[1])
	end_date = get_date_of_day(year,month,cycle_day)
	start_date = add_days(end_date,-29)
	out_contract_dn = []
	total_amt = 0
	if len(out_contract_dn):
		frappe.throw("Invoice consists of Delivery Notes out of contract Period<br>{0}".format(", ".join(["<b>{0}</b>".format(f) for f in out_contract_dn])))
	if doc.custom_billing_type == "Slab Based Billing":
		for item in self.items:
			if (not item.item_code == "Vending Machine Rentals") and item.item_code in item_dict and item_dict[item.item_code]:
				total_amt += item.amount
			if item.delivery_note:
				if frappe.db.get_value("Delivery Note",{"name":item.delivery_note,"posting_date":["<",start_date]}) or frappe.db.get_value("Delivery Note",{"name":item.delivery_note,"posting_date":[">",end_date]}):
					out_contract_dn.append(item.delivery_note)
		i = rent = 0
		total_qty = frappe.db.sql('''select sum(no_of_vending_machines) as total_qty from `tabSlab Definition` where parent = '{0}' '''.format(doc.name),as_dict=1) or 0
		if len(total_qty) and "total_qty" in total_qty[0]:
			total_qty = total_qty[0]["total_qty"]
		while total_qty>0 and i < len(doc.custom_slab_definitions):
			st = doc.custom_slab_definitions[i]
			avail_qty = total_amt // st.consumable_amount
			if avail_qty >= st.no_of_vending_machines:
				rent += st.no_of_vending_machines * st.in_range_rent
			else:
				rent += (avail_qty * st.in_range_rent) + ((st.no_of_vending_machines - avail_qty)*st.out_range_rent)
			total_qty -= st.no_of_vending_machines
			i += 1
			total_amt -= (st.no_of_vending_machines * st.consumable_amount)
			if total_amt < 0:
				total_amt = 0
		for item in self.items:
			if item.item_code == "Vending Machine Rentals":
				item.rate = rent
				item.amount = item.qty * rent
	elif doc.custom_billing_type == "Package Based Billing":
		item_list = {}
		non_package_items = []
		package_item_list = frappe.db.get_list("Package Definition",{"parent":doc.name},["item","qty"])
		package_items = [i["item"] for i in package_item_list]
		for item in self.items:
			if not item.item_code in item_list:
				item_list[item.item_code] = {"qty":item.qty,"rate":item.rate}
			elif item.item_code in item_list:
				item_list[item.item_code]["qty"] += item.qty
			if item.item_code not in package_items:
				non_package_items.append(item.item_code)
		f = 0
		self.items = []
		for item in package_item_list:
			if item["item"] in item_list:
				if item_list[item["item"]]["qty"] < item["qty"]:
					self.append("items",{
						"item_code":item["item"],
						"qty":item_list[item["item"]]["qty"],
						"rate":item_list[item["item"]]["rate"]
					})
					f = 1
				elif item_list[item["item"]]["qty"] > item["qty"]:
					self.append("items",{
						"item_code":item["item"],
						"qty":item_list[item["item"]]["qty"] - item["qty"],
						"rate":item_list[item["item"]]["rate"]
					})
		rate = 0
		for item in non_package_items:
			if item in item_list:
				rate = item_list[item]["rate"]
				for row in doc.custom_items:
					if item == row.item_code:
						self.append("items",{
							"item_code":item,
							"qty":item_list[item]["qty"],
							"rate":row.rate
						})
					else:
						self.append("items",{
							"item_code":item,
							"qty":item_list[item]["qty"],
							"rate":rate
						})


		# if not total_amt >= doc.custom_package_rate:
		# 	for item in self.items:
		# 		if item.item_group == "Coffee Vending Machine":
		# 			item.rate = doc.custom_noncompliance_rental_amount
		# 			item.amount = doc.custom_noncompliance_rental_amount*item.qty
		# if len(non_package_items):
		# 	frappe.msgprint("Invoice consists of non - package items:<br>{0}".format(", ".join(["<b>{0}</b>".format(f) for f in non_package_items])))
		# for contract in doc.custom_package_definition:
		# 	if contract.item in item_list and item_list[contract.item]["qty"] > (contract.qty+contract.carry_forwarded_qty):
		# 		extra_qty_items[contract.item] = {"additional_qty":item_list[contract.item]["qty"]-(contract.qty+contract.carry_forwarded_qty)}
		# if len(extra_qty_items):
		# 	frappe.msgprint("Invoice consists of items with additional package quantities:<br>{0}".format("<br>".join(["<b>{0}</b> - <b>{1} units</b>".format(f,extra_qty_items[f]["additional_qty"]) for f in extra_qty_items])))
	# elif doc.custom_billing_type == "Cup Based Billing":
	# 	item_list = {}
	# 	cup_items = frappe.db.get_list("Cup Definition" ,{"parent":doc.name},pluck="cup_name")
	# 	for item in self.items:
	# 		if not item.item_code in item_list and item.item_code not in cup_items:
	# 			item_list[item.item_code] = {"qty":item.qty,"rate":item.rate,"item_name":item.item_name,"description":item.description,"uom":item.uom,"income_account":item.income_account,"expense_account":item.expense_account,"warehouse":item.warehouse,"batch_no":item.batch_no}
	# 		elif item.item_code in item_list and item.item_code not in cup_items:
	# 			item_list[item.item_code]["qty"] += item.qty
	# 	pb_items = frappe.db.sql('''select pb.parent as cup_name,pb.item_code as item,pb.qty as qty from `tabProduct Bundle Item` as pb join `tabCup Definition` as cd on cd.cup_name = pb.parent where cd.parent = '{0}' '''.format(doc.name),as_dict=1)
	# 	pb_final = {}
	# 	for pb in pb_items:
	# 		for cup in self.items:
	# 			if cup.item_code in cup_items and cup.item_code == pb["cup_name"]:
	# 				pb["qty"] = pb["qty"]*cup.qty
	# 				if pb["item"] in pb_final:
	# 					pb_final[pb["item"]] += pb["qty"]
	# 				else:
	# 					pb_final[pb["item"]] = pb["qty"]
	# 	bundle_less_qty =  {}
	# 	without_bundle_items = []
	# 	for item in pb_final:
	# 		if item in item_list:
	# 			if item_list[item]["qty"] >= pb_final[item]:
	# 				item_list[item]["qty"] = item_list[item]["qty"]-pb_final[item]
	# 			elif item_list[item]["qty"] < pb_final[item]:
	# 				bundle_less_qty[item] = pb_final[item]-item_list[item]["qty"]
	# 		else:
	# 			without_bundle_items.append(item)
	# 	if bundle_less_qty:
	# 		frappe.msgprint("Additional {0} needed".format(','.join(["<b>{0}</b> units of Constituent <b>{1}</b>".format(bundle_less_qty[q],q) for q in bundle_less_qty])))
	# 	if len(without_bundle_items):
	# 		frappe.throw("Cup Constituents not found<br>{0}".format(",".join(["<b>{0}</b>".format(con) for con in without_bundle_items])))
	# 	del_item = []
	# 	for item in self.items:
	# 		if item.item_code not in cup_items:
	# 			del_item.append(item)
	# 	for i in del_item:
	# 		self.items.remove(i)
	# 	for key,val in item_list.items():
	# 		if not val["qty"]:
	# 			continue
	# 		item_list[key]["item_code"] = key
	# 		self.append("items",val)
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

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def fetch_delivery_notes(doctype=None, txt=None, searchfield=None, start=None, page_len=None, filters=None, as_dict=False):
	doctype = "Delivery Note"
	flag = 0
	conditions = ""
	cup_constituent = []
	if filters and "contract" in filters and "posting_date" in filters:
		doc = frappe.get_doc("Contract",filters["contract"])
		billing_cycle = doc.custom_monthly_billing_cycle
		cycle_day = int(billing_cycle.split(" ")[1].replace("st","").replace("nd","").replace("rd","").replace("th",""))
		year = datetime.strptime(filters["posting_date"], "%Y-%m-%d").year
		month = datetime.strptime(filters["posting_date"], "%Y-%m-%d").month
		end_date = get_date_of_day(year,month,cycle_day)
		start_date = add_days(end_date,-29)
		del filters["contract"] 
		del filters["posting_date"]
		if start_date and end_date and (("all_open_items"  not in filters) or (not filters["all_open_items"])):
			conditions += "and `tabDelivery Note`.posting_date >= '{0}' and `tabDelivery Note`.posting_date <= '{1}' ".format(start_date,end_date)
		if "all_open_items" in filters:
			del filters["all_open_items"]
		if doc.custom_billing_type == "Cup Based Billing":
			cup_constituent = frappe.db.get_list("Cup Constituents",{"parent":doc.name},pluck="constituent")
			flag = 1
	fields = get_fields(doctype, ["name", "customer", "posting_date"])
	if not flag:
		return frappe.db.sql(
			"""
			select %(fields)s
			from `tabDelivery Note`
			where `tabDelivery Note`.`%(key)s` like %(txt)s and
				`tabDelivery Note`.docstatus = 1
				and status not in ('Stopped', 'Closed') %(fcond)s
				and (
					(`tabDelivery Note`.is_return = 0 and `tabDelivery Note`.per_billed < 100)
					or (`tabDelivery Note`.grand_total = 0 and `tabDelivery Note`.per_billed < 100)
					or (
						`tabDelivery Note`.is_return = 1
						and return_against in (select name from `tabDelivery Note` where per_billed < 100)
					)
				){0}
				%(mcond)s order by `tabDelivery Note`.`%(key)s` asc limit %(page_len)s offset %(start)s
		""".format(conditions)
			% {
				"fields": ", ".join(["`tabDelivery Note`.{0}".format(f) for f in fields]),
				"key": searchfield,
				"fcond": get_filters_cond(doctype, filters, []),
				"mcond": get_match_cond(doctype),
				"start": start,
				"page_len": page_len,
				"txt": "%(txt)s",
			},
			{"txt": ("%%%s%%" % txt)},
			as_dict=as_dict,
		)
	else:
		return frappe.db.sql(
			"""
			select %(fields)s
			from `tabDelivery Note` join `tabDelivery Note Item` on `tabDelivery Note Item`.parent = `tabDelivery Note`.name
			where `tabDelivery Note Item`.item_code not in ({0}) and `tabDelivery Note`.`%(key)s` like %(txt)s and
				`tabDelivery Note`.docstatus = 1
				and status not in ('Stopped', 'Closed') %(fcond)s
				and (
					(`tabDelivery Note`.is_return = 0 and `tabDelivery Note`.per_billed < 100)
					or (`tabDelivery Note`.grand_total = 0 and `tabDelivery Note`.per_billed < 100)
					or (
						`tabDelivery Note`.is_return = 1
						and return_against in (select name from `tabDelivery Note` where per_billed < 100)
					)
				){1}
				%(mcond)s order by `tabDelivery Note`.`%(key)s` asc limit %(page_len)s offset %(start)s
		""".format(",".join(['"{0}"'.format(cp) for cp in cup_constituent]),conditions)
			% {
				"fields": ", ".join(["`tabDelivery Note`.{0}".format(f) for f in fields]),
				"key": searchfield,
				"fcond": get_filters_cond(doctype, filters, []),
				"mcond": get_match_cond(doctype),
				"start": start,
				"page_len": page_len,
				"txt": "%(txt)s",
			},
			{"txt": ("%%%s%%" % txt)},
			as_dict=as_dict,
		)
def on_validate_asset_cptzn(self,method):
	for item in self.stock_items:
		if item.item_code:
			serial_nos = frappe.db.get_list("Serial No",{"item_code":item.item_code,"warehouse":item.warehouse,"status":"Active"},pluck = "serial_no",order_by="creation")
			serial_str = ""
			idx = item.stock_qty
			item.serial_no = ""
			for sr in serial_nos:
				if idx == 0:
					break
				serial_str += sr+"\n"
				idx -= 1
			item.serial_no = serial_str

def on_save_dn(self, method):
	if not frappe.db.get_value("Contract",{"party_name":self.customer,"is_signed":1,"custom_invoice_with_dn":1}):
		return
	frappe.msgprint("Customer <b>{0}</b> is eligible for Invoicing with Consumable delivery".format(self.customer))

def autobill_invoice():
	contracts = frappe.get_list("Contract",{"is_signed":1,"custom_is_monthly_billing":1,"custom_enable_autobilling":1,"status":"Active"},pluck = "name")
	print(contracts)
	for name in contracts[0:1]:
		doc = frappe.get_doc("Contract",name)
		billing_cycle = doc.custom_monthly_billing_cycle or "End of the Month"
		year = datetime.strptime(today(), "%Y-%m-%d").year
		month = datetime.strptime(today(), "%Y-%m-%d").month
		if not billing_cycle == "End of the Month":
			cycle_day = int(billing_cycle.split(" ")[1].replace("st","").replace("nd","").replace("rd","").replace("th",""))
		else:
			cycle_day = int(calendar.monthrange(year, month)[1])
		end_date = get_date_of_day(year,month,cycle_day)
		if end_date == today():
			new_doc = frappe.new_doc("Sales Invoice")
			new_doc.customer = doc.party_name
			new_doc.posting_date = today()
			new_doc.custom_contract = doc.name
			filters = {
				"docstatus": 1,
				"company": new_doc.company,
				"posting_date":today(),
				"contract":doc.name,
				"all_open_items":0,
				"is_return": 0,
				"customer":doc.party_name
			}
			dns = fetch_delivery_notes(doctype="Delivery Note",txt="",searchfield="name",start=0,page_len=25,filters=filters,as_dict=True)
			dn_items = frappe.db.sql('''select item_code,qty,rate,amount from `tabDelivery Note Item` where parent in ({0})'''.format(",".join(["'{0}'".format(i["name"]) for i in dns])),as_dict = 1)
			for row in dn_items:
				new_doc.append("items",row)
			if doc.custom_billing_type == "Package Based Billing":
				print("true")
				new_doc.append("items",{
					"item_code":"Package Rental",
					"qty":1,
					"rate":doc.custom_package_rate
				})
			elif doc.custom_billing_type == "Slab Based Billing":
				new_doc.append("items",{
					"item_code":"Vending Machine Rentals",
					"qty":1,
					"rate":0
				})
			elif doc.custom_billing_type == "Cup Based Billing":
				for item in doc.custom_cup_definitions:
					new_doc.append("items",{
						"item_code":item.cup_name,
						"qty":1,
						"rate":item.cup_rate
					})
			new_doc.save(ignore_permissions = True)
			# print('''select item_code,qty,rate,amount from `tabDelivery Note Item` where parent in ({0})'''.format(",".join(["'{0}'".format(i["name"]) for i in dns])))


		

