import frappe
from frappe import _
from erpnext.assets.doctype.asset_capitalization.asset_capitalization import AssetCapitalization
from frappe.utils import cint, flt, get_link_to_form
from erpnext.assets.doctype.asset_category.asset_category import get_asset_category_account

class CustomAssetCapitalization(AssetCapitalization):
	def before_submit(self):
		self.validate_source_mandatory()
		if self.entry_type == "Capitalization":
			self.create_target_asset()

	def create_target_asset(self):
		total_target_asset_value = flt(self.total_value, self.precision("total_value"))
		asset_doc = frappe.new_doc("Asset")
		asset_doc.company = self.company
		asset_doc.item_code = self.target_item_code
		asset_doc.is_existing_asset = 1
		asset_doc.location = self.target_asset_location
		asset_doc.available_for_use_date = self.posting_date
		asset_doc.purchase_date = self.posting_date
		asset_doc.gross_purchase_amount = total_target_asset_value
		asset_doc.purchase_receipt_amount = total_target_asset_value
		serial_no = ""
		for item in self.stock_items:
			if item.serial_no:
				serial_no = item.serial_no
		asset_doc.custom_asset_serial_no = serial_no
		asset_doc.flags.ignore_validate = True
		asset_doc.insert()
		self.target_asset = asset_doc.name
		self.target_fixed_asset_account = get_asset_category_account(
			"fixed_asset_account", item=self.target_item_code, company=asset_doc.company
		)
		frappe.msgprint(
			_(
				"Asset {0} has been created. Please set the depreciation details if any and submit it."
			).format(get_link_to_form("Asset", asset_doc.name))
		)
