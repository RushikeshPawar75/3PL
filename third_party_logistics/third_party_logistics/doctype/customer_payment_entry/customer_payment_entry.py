# Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from erpnext.stock.doctype.item.test_item import make_item


class CustomerPaymentEntry(Document):
	def on_submit(self):
		if self.customer_purchase_invoice:
			cpi = frappe.get_doc("Customer Purchase Invoice",self.customer_purchase_invoice)
			get_purchase_receipt = frappe.get_doc("Customer Purchase Receipt",cpi.customer_purchase_receipt)
			if get_purchase_receipt.total_qty == cpi.total_inv_qty:
				get_purchase_receipt.db_set("per_billed", "100")
				get_purchase_receipt.db_set("status", "Submitted")
				cpi.db_set('status', 'Paid')
			else:
				if get_purchase_receipt.total_qty and cpi.total_inv_qty:
					cpo_per_rec = ((cpi.total_inv_qty/get_purchase_receipt.total_qty)*100)
					cpi.db_set("status","Partly Paid")
					get_purchase_receipt.db_set("per_billed", cpo_per_rec)
			new_sales_inv = frappe.new_doc("Sales Invoice")
			new_sales_inv.customer = cpi.customer
			for item in cpi.items:
				new_sales_inv.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "uom": item.stock_uom,
					"rate":item.rate,
					"amount":item.amount})
			#ADD Charges inside the child table in Sales Invoice
			if not frappe.db.exists("Item", 'PAOC-001'):
				new_item = frappe.new_doc("Item")
				new_item.item_code = "PAOC-001"
				new_item.item_name = "PICKUP_AND_OTHER_CHARGES"
				new_item.stock_uom = "Nos"
				new_item.item_group ="All Item Groups"
				# cod = cpi.items
				for i in cpi.items:
					code = i.item_code
					print("**code **",code)
					item_doc = frappe.get_doc('Item',code)
					new_item.custom_item_length = item_doc.custom_item_length
					new_item.custom_item_breadth = item_doc.custom_item_breadth
					new_item.custom_item_height = item_doc.custom_item_height
				new_item.save()
			if frappe.db.exists("Item", 'PAOC-001'):
				new_sales_inv.append("items", {"item_code": "PAOC-001","qty": 1,"uom":"Nos","rate":cpi.total})
			new_sales_inv.total_qty = cpi.total_inv_qty
			new_sales_inv.save()
			frappe.msgprint("Sales Invoice {0} created".format(new_sales_inv.name))
