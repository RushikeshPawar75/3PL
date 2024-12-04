# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PickupEntry(Document):
	def on_submit(self):
		cpo = frappe.get_doc("Customer Purchase Order",self.customer_purchase_order)
		cpo.db_set("status","Order Shipped")
		cpo.db_set("pickup_entry",self.name)

	def validate(self):
		if not frappe.db.get_value("Customer Purchase Order",{"pickup_team":self.pickup_team,"company":self.company,"status":"Scheduled"}):
			frappe.throw("Company does not match customer_purchase_order")
		
