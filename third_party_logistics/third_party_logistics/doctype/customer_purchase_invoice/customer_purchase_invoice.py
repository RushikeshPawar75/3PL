# Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _, throw
from frappe.utils import nowdate
from frappe.model.document import Document


class CustomerPurchaseInvoice(Document):
	def before_save(self):
		sum_amt = 0
		total_qty = 0
		msg = ""
		if self.items and self.total:
			for item in self.items:
				if not item.rate:
					msg += f"Row #{item.idx}: Rate is required for Item {frappe.bold(item.item_code)}<br>"
					frappe.throw(_(msg), title=_("Item Rate Required"))
				sum_amt += item.amount
				total_qty += item.qty
			if sum_amt and total_qty:
				self.total_inv_qty = total_qty
				self.total_qty_amount = sum_amt
				self.total_due_amount = self.total_qty_amount + self.total
				self.status = "Unpaid"
		elif not self.items:
			frappe.throw("Items table is mandatory")
		else:
			frappe.throw("'Total Price (Pickup & Others Charges)' not found")
	@frappe.whitelist()
	def customer_payment_entry(self):
		cpe_exist= frappe.get_all("Customer Payment Entry",{"customer_purchase_invoice":self.name,"docstatus":0},"name")
		if cpe_exist and cpe_exist[0].name:
			return True
		else:
			get_customer_pinv = frappe.get_doc("Customer Purchase Invoice", self.name)
			new_customer_pe = frappe.new_doc("Customer Payment Entry")
			new_customer_pe.payment_type = "Pay"
			new_customer_pe.posting_date = nowdate()
			new_customer_pe.mode_of_payment = "Cash"
			new_customer_pe.customer_purchase_invoice = get_customer_pinv.name
			new_customer_pe.paid_amount = get_customer_pinv.total_due_amount
			new_customer_pe.save()
			frappe.msgprint("Customer Payment Entry Created Successfully")


