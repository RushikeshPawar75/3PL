# Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _, qb
from typing import Dict, List
from frappe.utils import money_in_words
from frappe.query_builder.functions import Coalesce, IfNull, Locate, Replace, Sum
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.get_item_details import get_bin_details, get_conversion_factor
from frappe.utils import flt, getdate , today
from erpnext.stock.stock_balance import update_bin_qty
from frappe.utils import add_days, cint, cstr, flt, get_link_to_form, getdate, nowdate, strip_html

class CustomerSalesOrder(Document):
    
	def onload(self):
		if self.doctype in ("Customer Sales Order", "Delivery Note", "Sales Invoice"):
			for item in self.get("items") + (self.get("packed_items") or []):
				item.update(get_bin_details(item.item_code, item.warehouse, include_child_warehouses=True))
	def total_qty_calculation(self):
		total_amount = 0
		total_quantity = 0
		total_weight = 0
		for item in self.get("items"):
			if item.item_code:
				total_quantity += item.qty
				total_weight += item.total_weight
				total_amount += item.amount
		self.total_quantity = total_quantity
		self.total_net_weight = total_weight
		self.total = total_amount

	def validate(self):
		self.validate_warehouse()
		self.total_qty_calculation()
		self.shipping_price_calculation()
		self.calculate_grand_total()
		if self.status:
			if self.docstatus == 0:
				self.status = "Draft"
		elif self.docstatus == 1:
				self.status = "Delivery To Be Scheduled"
		elif self.docstatus == 2:
				self.status = "Cancelled"
	def validate_warehouse(self):
		for d in self.get("items"):
			if (
				(
					frappe.get_cached_value("Item", d.item_code, "is_stock_item") == 1
				)
				and not d.warehouse
			):
				frappe.throw(_("Delivery warehouse required for stock item <b>{0}</b>").format(d.item_code))

	def shipping_price_calculation(self):
		if self.delivery_required and self.shipping_price_list:
			spl = frappe.get_doc("Shipping Price List", self.shipping_price_list)
			if not spl:
				frappe.throw("Shipping Price List Not Found")
			else:
				if not self.delivery_distance:
					frappe.throw("Delivery Distance is required for delivery charge calculation")
				price_matrix = frappe.get_all('Price Matrix', filters={
                    'parent': spl.name,
                    'from_distance': ['<=', self.delivery_distance],
                    'to_distance': ['>=', self.delivery_distance]}, fields=['parent', 'price_per_distance', 'price_per_weight'], limit=1)
				if not price_matrix:
					frappe.throw("The entered Delivery Distance is not found in the Shipping Price List")
				if price_matrix and price_matrix[0].price_per_weight:
					weight_rate = flt(price_matrix[0].price_per_weight)
					self.delivery_charges = weight_rate * flt(self.total_net_weight)
				else:
					frappe.throw("Total Net Weight is not rated in the Shipping Price List")
		elif self.delivery_required and not self.shipping_price_list:
			frappe.throw("Shipping Price List Not Found")


	def calculate_grand_total(self):
		delivery_charge = self.delivery_charges or 0
		total_amount_items = self.total or 0
		self.total_amount = total_amount_items	
		self.grand_total = delivery_charge + self.total_amount
		self.in_words = money_in_words(self.grand_total)
				
	def update_picking_status(self):
		total_picked_qty = 0.0
		total_qty = 0.0
		per_picked = 0.0

		for so_item in self.items:
			if cint(
				frappe.get_cached_value("Item", so_item.item_code, "is_stock_item")
			):
				total_picked_qty += flt(so_item.picked_qty)
				total_qty += flt(so_item.stock_qty)

		if total_picked_qty and total_qty:
			per_picked = total_picked_qty / total_qty * 100

		self.db_set("per_picked", flt(per_picked), update_modified=False)
		if flt(per_picked) == 100 and self.status == 'Delivery Scheduled':
			self.db_set("status","To Deliver and Bill")
	def on_submit(self):
		self.update_reserved_qty()
	def check_modified_date(self):
		mod_db = frappe.db.get_value("Customer Sales Order", self.name, "modified")
		date_diff = frappe.db.sql("select TIMEDIFF('%s', '%s')" % (mod_db, cstr(self.modified)))
		if date_diff and date_diff[0][0]:
			frappe.throw(_("{0} {1} has been modified. Please refresh.").format(self.doctype, self.name))
	
	@frappe.whitelist()
	def update_close_status(self):
		self.check_modified_date()
		self.db_set("status","Closed")
		self.update_reserved_qty()
	
	@frappe.whitelist()
	def update_reopen_status(self):
		self.check_modified_date()
		self.db_set("status","Delivery To Be Scheduled")
		self.update_reserved_qty()

	def update_reserved_qty(self, so_item_rows=None):
		item_wh_list = []
		def _valid_for_reserve(item_code, warehouse):
				if (
					item_code
					and warehouse
					and [item_code, warehouse] not in item_wh_list
					and frappe.get_cached_value("Item", item_code, "is_stock_item")
				):
					item_wh_list.append([item_code, warehouse])
		def get_reserved_qty(item_code, warehouse):
			reserved_qty = frappe.db.sql(
				"""
				select
					sum(dnpi_qty * ((so_item_qty - so_item_delivered_qty) / so_item_qty))
				from
					(
						(select
							qty as dnpi_qty,
							(
								select qty from `tabCustomer Sales Order Item`
								where name = dnpi.parent_detail_docname
							) as so_item_qty,
							(
								select delivered_qty from `tabCustomer Sales Order Item`
								where name = dnpi.parent_detail_docname
							) as so_item_delivered_qty,
							parent, name
						from
						(
							select qty, parent_detail_docname, parent, name
							from `tabPacked Item` dnpi_in
							where item_code = %s and warehouse = %s
							and parenttype='Customer Sales Order'
							and item_code != parent_item
							and exists (select * from `tabCustomer Sales Order` so
							where name = dnpi_in.parent and docstatus = 1 and status not in ('On Hold', 'Closed'))
						) dnpi)
					union
						(select stock_qty as dnpi_qty, qty as so_item_qty,
							delivered_qty as so_item_delivered_qty, parent, name
						from `tabCustomer Sales Order Item` so_item
						where item_code = %s and warehouse = %s
						and exists(select * from `tabCustomer Sales Order` so
							where so.name = so_item.parent and so.docstatus = 1
							and so.status not in ('On Hold', 'Closed')))
					) tab
				where
					so_item_qty >= so_item_delivered_qty
			""",
				(item_code, warehouse, item_code, warehouse),
			)

			return flt(reserved_qty[0][0]) if reserved_qty else 0

		for d in self.get("items"):
			if (not so_item_rows or d.name in so_item_rows):
				_valid_for_reserve(d.item_code, d.warehouse)

		for item_code, warehouse in item_wh_list:
			update_bin_qty(item_code, warehouse, {"reserved_qty": get_reserved_qty(item_code, warehouse)})

	@frappe.whitelist()
	def update_record(self , status,date,time,scheduled_duration,pickup_team):
		self.db_set("status",status)
		self.db_set("shipment_date",date)
		self.db_set("delivery_time",time)
		self.db_set("delivery_duration",scheduled_duration)
		self.db_set("delivery_team",pickup_team)
		self.db_set("delivery_date",date)
		self.db_update()

@frappe.whitelist()
def create_pick_list(source_name, target_doc=None):

	def update_item_quantity(source, target, source_parent) -> None:
		picked_qty = flt(source.picked_qty) / (flt(source.conversion_factor) or 1)
		qty_to_be_picked = flt(source.qty) - max(picked_qty, flt(source.delivered_qty))

		target.qty = qty_to_be_picked
		target.stock_qty = qty_to_be_picked * flt(source.conversion_factor)

	def update_packed_item_qty(source, target, source_parent) -> None:
		qty = flt(source.qty)
		for item in source_parent.items:
			if source.parent_detail_docname == item.name:
				picked_qty = flt(item.picked_qty) / (flt(item.conversion_factor) or 1)
				pending_percent = (item.qty - max(picked_qty, item.delivered_qty)) / item.qty
				target.qty = target.stock_qty = qty * pending_percent
				return

	def should_pick_order_item(item) -> bool:
		return (
			abs(item.delivered_qty) < abs(item.qty)
		)

	doc = get_mapped_doc(
		"Customer Sales Order",
		source_name,
		{
			"Customer Sales Order": {"doctype": "Pick List", "validation": {"docstatus": ["=", 1]}},
			"Customer Sales Order Item": {
				"doctype": "Pick List Item",
				"field_map": {"parent": "customer_sales_order", "name": "customer_sales_order_item"},
				"postprocess": update_item_quantity,
				"condition": should_pick_order_item,
			},
			"Packed Item": {
				"doctype": "Pick List Item",
				"field_map": {
					"parent": "customer_sales_order",
					"name": "customer_sales_order_item",
				},
				"field_no_map": ["picked_qty"],
				"postprocess": update_packed_item_qty,
			},
		},
		target_doc,
	)
	doc.purpose = "Delivery"
	return doc

@frappe.whitelist()
def override_on_submit(self, method=None):
	for item in self.locations:
		if item.picked_qty == 0:# if the user has not entered any picked qty, set it to stock_qty, before submit
			item.picked_qty = item.stock_qty

	if not self.status:
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			if target_document_exists(self.name, self.purpose):
				self.status = "Completed"
			else:
				self.status = "Open"
		elif self.docstatus == 2:
				self.status = "Cancelled"
	so_items = []
	for item in self.locations:
		if item.customer_sales_order_item:
			so_items.append(item.customer_sales_order_item)

		if so_items:
			update_sales_order_item_qty(so_items)
	sales_orders = []
	for row in self.locations:
		if row.customer_sales_order and row.customer_sales_order not in sales_orders:
			sales_orders.append(row.customer_sales_order)
	for sales_order in sales_orders:
		frappe.get_doc("Customer Sales Order", sales_order, for_update=True).update_picking_status()
		
	def target_document_exists(pick_list_name, purpose):
		if purpose == "Delivery":
			return frappe.db.exists("Delivery Note", {"pick_list": pick_list_name})
		return stock_entry_exists(pick_list_name)
	
	def stock_entry_exists(pick_list_name):
		return frappe.db.exists("Stock Entry", {"pick_list": pick_list_name})
	
def validate_picked_qty(data):
	over_delivery_receipt_allowance = 100 + flt(
		frappe.db.get_single_value("Stock Settings", "over_delivery_receipt_allowance")
	)

	for row in data:
		if (row.picked_qty / row.stock_qty) * 100 > over_delivery_receipt_allowance:
			frappe.throw(
				_(
					"You are picking more than required quantity for the item {0}. Check if there is any other pick list created for the customer sales order {1}."
				).format(row.item_code, row.customer_sales_order)
			)
	
def update_sales_order_item_qty(so_items):
	picked_items = get_picked_items_qty(so_items)
	validate_picked_qty(picked_items)
	picked_qty = frappe._dict()
	for d in picked_items:
		picked_qty[d.customer_sales_order_item] = d.picked_qty

	for so_item in so_items:
		frappe.db.set_value("Customer Sales Order Item",so_item,"picked_qty",flt(picked_qty.get(so_item)),update_modified=False)
def get_picked_items_qty(items) -> List[Dict]:
	pi_item = frappe.qb.DocType("Pick List Item")
	return (
			frappe.qb.from_(pi_item)
			.select(
				pi_item.customer_sales_order_item,
				pi_item.item_code,
				pi_item.customer_sales_order,
				Sum(pi_item.stock_qty).as_("stock_qty"),
				Sum(pi_item.picked_qty).as_("picked_qty"),
			)
			.where((pi_item.docstatus == 1) & (pi_item.customer_sales_order_item.isin(items)))
			.groupby(
				pi_item.customer_sales_order_item,
				pi_item.customer_sales_order,
			)
			.for_update()
		).run(as_dict=True)

@frappe.whitelist()
def get_availability_data(req_date, emp_grp):
    date = getdate(req_date)
    weekday = date.strftime("%A")
    eg_doc = frappe.get_doc("Employee Group", emp_grp)
    if eg_doc.custom_schedule:
        slot_details = get_available_slots(eg_doc, date)
    else:
        frappe.throw(_("{0} does not have a Schedule. Add it in Employee Group master").format(emp_grp),
            title=_("Pickup Team Schedule Not Found"),
        )
    if not slot_details:
        frappe.throw(_("Pickup Team not available on {0}").format(weekday), title=_("Not Available"))

    return {"slot_details": slot_details}

def get_available_slots(eg_doc, date):
	available_slots = slot_details = []
	weekday = date.strftime("%A")
	pickup_team = eg_doc.name
	pickup_schedule = frappe.get_doc("Schedule", eg_doc.custom_schedule)
	if pickup_schedule and not pickup_schedule.disabled:
		available_slots = []
		for time_slot in pickup_schedule.time_slots:
			if weekday == time_slot.day:
				available_slots.append(time_slot)

		if available_slots:
			appointments = []
			filters = {
				"pickup_team": pickup_team,
				"scheduled_date": date,
				"status": ["in", ["Scheduled","Overdue"]],
			}
			slot_name = eg_doc.custom_schedule
			# fetch all appointments to delivery_team
			filters["pickup_team"] = pickup_team
			appointments = frappe.get_all("Customer Sales Order",fields=["name", "delivery_time", "delivery_duration", "status"],)
			slot_details.append(
				{
					"slot_name": slot_name,
					"avail_slot": available_slots,
					"appointments": appointments
				}
			)
	return slot_details

def autochange_status():
    ovd_cso = frappe.get_all("Customer Sales Order", ["name", "delivery_date", "status" , "docstatus"])
    t = getdate(today())
    if ovd_cso:
        for i in ovd_cso:
            ovd = frappe.get_doc("Customer Sales Order", i.name)
            if getdate(ovd.delivery_date) <= t and ovd.docstatus == 1 and ovd.delivery_required == 1 and ovd.status == "Delivery Scheduled":
                ovd.status = "Delivery Overdue"
                ovd.save()


    
	
