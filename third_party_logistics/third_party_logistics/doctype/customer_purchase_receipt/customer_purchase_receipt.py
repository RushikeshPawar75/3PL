# Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _, throw
from frappe.utils import cint, flt, getdate, nowdate
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class CustomerPurchaseReceipt(Document):
	def before_save(self):
		total_weight = 0
		total_net_weight = 0
		if not self.accepted_warehouse:
			frappe.throw("Accepted Warehouse is mandatory.")
		total_received_qty = 0
		if self.items:
			for items in self.items:
				# items.received_qty = items.qty
				items.rejected_qty = items.received_qty - items.qty
				print("qty",items.received_qty)
				print("ttq",total_received_qty)
				total_received_qty = total_received_qty + items.received_qty
				print("total_received_qty",total_received_qty)
				total_weight = flt(items.weight_per_unit * items.received_qty)
				items.total_weight = total_weight
				total_net_weight = total_net_weight + total_weight
		self.total_received_qty = total_received_qty
		self.total_net_weight = total_net_weight
	def validate(self):
		if self._action == 'submit' and self.items:
			# self.status = "To Bill"
			for items in self.items:
				cpo = items.customer_purchase_order
				if frappe.db.get_value("Customer Purchase Order",{"name":cpo},"billable"):
					self.db_set("status", "To Bill")
					break
				else:
					self.db_set("status", "Completed")
		self.po_required()
		if getdate(self.posting_date) > getdate(nowdate()):
			throw(_("Posting Date cannot be future date"))
			print("posting_date",self.posting_date)
		#QC
		if self.items:
			msg = ''
			for item in self.items:
				print("******ITEM:::: *****",item)

				if frappe.db.get_value("Item",item.item_code,'inspection_required_before_purchase') and not item.quality_control_inspection:
					msg += f"Row #{item.idx}: Quality Inspection is required for Item {frappe.bold(item.item_code)}<br>"
			if msg:
				if self.docstatus == 1:
					frappe.throw(_(msg), title=_("Inspection Required"))
				else:
					frappe.msgprint(_(msg), title=_("Inspection Required"), indicator="blue")

	def on_submit(self):
		# self.posting_time = frappe.utils.datetime().now()
		# if self.total:
		# 	self.db_set("status", "To Bill")
		if self.items:
			for items in self.items:
				cpo = items.customer_purchase_order
				if cpo:
					print("****cpo  is   ",cpo)
					
					cpo_doc = frappe.get_doc("Customer Purchase Order",cpo)
					child_table_items = cpo_doc.get("items")

					print("***child_table_items",child_table_items)


					for ch_item in child_table_items:
						print(f"Item Code: {ch_item.item_code}, Quantity: {ch_item.qty}")
						if items.item_code == ch_item.item_code:
							if items.received_qty > ch_item.qty:
								msg = f"Row #{items.idx}: Received qty is greater than Customer Purchase Ordered qty. Item - {frappe.bold(items.item_code)}"
								frappe.throw(_(msg), title=_("More than ordered Qty"))
							else:
								cpo_child_id = frappe.db.get_value("Customer Purchase Order Item", {"customer_purchase_order": cpo, "item_code": items.item_code}, "name")
								if cpo_child_id:
									doc_cpo_id = frappe.get_doc("Customer Purchase Order Item", cpo_child_id)
									doc_cpo_id.db_set("pr_received_qty", items.received_qty)

							
			if cpo and self.total_received_qty:
				doc_cpo = frappe.get_doc("Customer Purchase Order", cpo)
				if self.total_received_qty == doc_cpo.total_qty:
					doc_cpo.db_set("status", "Received")
					doc_cpo.db_set("per_received", "100")
				else:
					if self.total_received_qty and doc_cpo.total_qty:
						cpo_per_rec = ((self.total_received_qty / doc_cpo.total_qty) * 100)
						doc_cpo.db_set("status", "Partially Received")
						doc_cpo.db_set("per_received", cpo_per_rec)

		new_stock = frappe.new_doc("Stock Entry")
		new_stock.posting_date = self.posting_date
		new_stock.posting_time = self.posting_time
		new_stock.accepted_warehouse = self.accepted_warehouse
		new_stock.stock_entry_type = "Material Receipt"
		new_stock.custom_customer_purchase_order = cpo
		print("new Stock----->",new_stock)

		doc_cpo = frappe.get_doc("Customer Purchase Order",cpo)
		customer_purchase_order_item = doc_cpo.items
		new_stock.custom_customer = doc_cpo.customer

		print("*****cpitems****",customer_purchase_order_item)

		if customer_purchase_order_item:
			for item in customer_purchase_order_item:
				print('***item*666666****',item.item_code)
				new_stock.append("items", {
					"item_code": item.item_code,
					"item_name": item.item_name,
					"description": item.description,
					"uom": item.uom,
					"qty": item.qty,
					"t_warehouse":self.accepted_warehouse,
					"stock_uom": item.stock_uom,
					"transfer_qty": item.stock_qty,
					"conversion_factor": item.conversion_factor,
					"custom_customer_purchase_order": item.customer_purchase_order,
					"allow_zero_valuation_rate": '1'
				})
		new_stock.save()
		new_stock.submit()

	def po_required(self):
		if frappe.db.get_value("Buying Settings", None, "po_required") == "Yes":
			for d in self.get("items"):
				if not d.purchase_order:
					frappe.throw(_("Purchase Order number required for Item {0}").format(d.item_code))			

@frappe.whitelist()
def create_customer_inv(source_name):
	def postprocess(source, doc):
		doc.posting_date = source.posting_date
		doc.customer_purchase_receipt = source.name
		print("postprocess----->",postprocess)
	
	doc = get_mapped_doc(
        "Customer Purchase Receipt",
        source_name,
        {
            "Customer Purchase Receipt": {"doctype": "Customer Purchase Invoice"},
            "Customer Purchase Receipt Item": {"doctype": "Customer Purchase Invoice Item"},
        },
        None,
        postprocess,
    )
	return doc
