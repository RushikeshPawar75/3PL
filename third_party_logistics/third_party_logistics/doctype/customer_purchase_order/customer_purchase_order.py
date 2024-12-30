# Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

from erpnext.regional.report.uae_vat_201.uae_vat_201 import standard_rated_expenses_emiratewise
import frappe
from frappe import _
from frappe.utils import flt, getdate , today
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
import json

class CustomerPurchaseOrder(Document):
    @frappe.whitelist()
    def close_order(self, status):          
        if self.status == 'Closed':
            frappe.throw('This Customer PO is already closed.')
        else:
            self.db_set("status",status)
            return True

    @frappe.whitelist()
    def update_record(self , status,date,time,scheduled_duration,pickup_team):
        print("*********####",date)
        print("*********####",time)
        print("*********####",scheduled_duration)
        self.db_set("status",status)
        self.db_set("scheduled_date",date)
        self.db_set("scheduled_time",time)
        self.db_set("scheduled_duration",scheduled_duration)
        self.db_set("pickup_team",pickup_team)
        self.db_set("customer_purchase_order",self.name)
        self.db_update()
        print("*****updated_record")
        
    # total_final_price = 0sss
    # def validate(self):
    #     print("xndjyyyy"*90)
    #     print("*****insdie validate *********8")
    #     print("*****self.scheduled_duration *********8",self.scheduled_duration)
    #     print("*****self.scheduled_time *********8",self.scheduled_time)
        
    
    # def validate(self):
        # print("xndj"*90)
        # print("ff",frappe.db.get_value("Pickup Price List",{'customer':self.customer,'name':self.pickup_price_list}))
        # self.validate_transaction_date()
        # if not frappe.db.get_value("Pickup Price List",{'customer':self.customer,'name':self.pickup_price_list}):
        #     frappe.throw("Please choose the correct pickup price list")


    def validate_transaction_date(self):
        print("*******DATE*******")
        """Validate transaction_date should not be less than pickup_request_date date."""
        if self.transaction_date and self.pickup_request_date and self.transaction_date < self.pickup_request_date:
            frappe.throw(_("Required By cannot be earlier than Pickup Request Date date."),
                         frappe.ValidationError)

        if self.status == "Pickup to be Scheduled":
            self.scheduled_duration = None
            self.scheduled_time = None
        if self.status == "Draft" and not self.required_pickup:
            self.status = 'To Receive and Bill'    
                                                                                                                                                          

    def validate(self):
        self.validate_transaction_date()
        if not frappe.db.get_value("Pickup Price List",{'customer':self.customer,'name':self.pickup_price_list}):
            frappe.throw("Please choose the correct pickup price list")

        total_net_weight = 0
        total_net_volume = 0
        total_net_area = 0
        total_quantity = 0
        total_weight = 0
        total_volume = 0
        total_area = 0
        total_charges_amt = 0
        total = 0

        for item in self.get("items"):
                if item.item_code:
                    _spc = frappe.get_value("Item", item.item_code, "custom_special_skill_charges_per_unit")
                    _hcp = frappe.get_value("Item", item.item_code, "custom_handling_charges_per_unit")

                    item.conversion_factor = get_uom_conversion_factor(item.item_code, item.uom)
                    _stq = item.conversion_factor * item.qty
                    item.stock_qty = _stq
                    total_quantity += item.stock_qty
                    total_weight += flt(item.weight_per_unit * item.stock_qty)
                    volume_per_unit_of_item = frappe.get_value("Item", item.item_code, "custom_volume_per_unit")
                    item.volume_per_unit = volume_per_unit_of_item
                    total_volume += volume_per_unit_of_item * item.qty
                    area_per_unit_of_item = frappe.get_value("Item", item.item_code, "custom_area_per_unit")
                    item.area_per_unit = area_per_unit_of_item
                    total_area += area_per_unit_of_item * item.qty
                    item.total_weight = total_weight
                    item.total_volume = total_volume
                    item.total_area = total_area
                    total_net_weight += total_weight
                    total_net_volume += total_volume
                    total_net_area += total_area

                    if _spc:
                        item.special_skill_charges_per_unit = flt(item.stock_qty * _spc)
                    else:
                        item.special_skill_charges_per_unit = 0.0

                    if _hcp:
                        item.handling_charges_per_unit = flt(item.stock_qty * _hcp)
                    else:
                        item.handling_charges_per_unit = 0.0

                    item.customer_purchase_order = self.name
                    if self.required_pickup:
                        sum_of_charges = item.special_skill_charges_per_unit + item.handling_charges_per_unit
                        total_charges_amt += sum_of_charges

                    item.opening_stock = frappe.get_value("Item", item.item_code, "opening_stock")
                    received_percentage = flt((item.stock_qty / item.opening_stock) * 100) if item.opening_stock > 0 else 0

        self.total_qty = total_quantity
        self.total_net_weight = total_net_weight
        self.total_net_volume = total_net_volume
        self.total_net_area = total_net_area       

        custom_pickup_charges_applicable = frappe.get_value("Customer", self.customer, "custom_pickup_charges_applicable")
        if custom_pickup_charges_applicable == 1:
            print("triger------------------------")
            pickup_distance = self.pickup_distance
            customer = self.customer
            from_date = self.transaction_date
            to_date = today()
        
            if self.required_pickup:
                print("inside 1st----->")
                if not self.pickup_price_list:
                    print("inside 2st----------->")
                    price_list = self.get_matching_pickup_price_list(pickup_distance, total_weight, customer, from_date, to_date)
                    self.pickup_price_list = price_list.get('parent')

                    if price_list and price_list.get('price_per_distance'):
                        self.applied_price_per_distance = price_list.get('price_per_distance')
                        price_per_distance = flt(price_list.get('price_per_distance'))
                        price_per_weight = flt(price_list.get('price_per_weight')) if 'price_per_weight' in price_list else 0

                        if price_per_weight:
                            total = price_per_distance * flt(self.total_net_weight) + price_per_weight * flt(self.total_net_weight) + total_charges_amt
                            print("price_per_distance * flt(self.total_net_weight) + price_per_weight * flt(self.total_net_weight) + total_charges_amt",
                                 price_per_distance, self.total_net_weight, price_per_weight, self.total_net_weight, total_charges_amt)
                        else:
                            total = price_per_distance * flt(self.total_net_weight) + total_charges_amt
                            print("price_per_distance * flt(self.total_net_weight) + total_charges_amt",price_per_distance,self.total_net_weight,total_charges_amt)

                    self.total = total
                    self.db_set("total",total)

                else:
                    price_list_data = self.selected_pickuplist()
                    print("price list data------------------",price_list_data)
                    self.pickup_price_list = price_list_data.get('parent')

                    print("vdv v d-----------------------",price_list_data.get('price_per_distance'))

                    if price_list_data or price_list_data.get('price_per_distance'):
                        print("working else----------------------")

                        self.applied_price_per_distance = price_list_data.get('price_per_distance')
                        price_per_distance = flt(price_list_data.get('price_per_distance'))
                        price_per_weight = flt(price_list_data.get('price_per_weight')) if 'price_per_weight' in price_list_data else 0
                        print("price_per_weight-0----------------",price_per_weight)

                        if price_per_weight:
                            total = price_per_distance * flt(self.total_net_weight) + price_per_weight * flt(self.total_net_weight) + total_charges_amt
                            print("price_per_distance * flt(self.total_net_weight) + price_per_weight * flt(self.total_net_weight) + total_charges_amt",
                                 price_per_distance, self.total_net_weight, price_per_weight, self.total_net_weight, total_charges_amt)
                        else:
                            total = price_per_distance * flt(self.total_net_weight) + total_charges_amt

                            print("totsl; nc djv--------------------------------",total)

                    self.total = total
                    self.db_set("total",total)
        else:
            self.db_set("total",total)
        

    # def before_save(self):
    #     total_net_weight = 0
    #     total_net_volume = 0
    #     total_net_area = 0
    #     total_quantity = 0
    #     total_weight = 0
    #     total_volume = 0
    #     total_area = 0
    #     total_charges_amt = 0
    #     for item in self.get("items"):
    #         if item.item_code:
    #             _spc = frappe.get_value("Item", item.item_code, "custom_special_skill_charges_per_unit")
    #             _hcp = frappe.get_value("Item", item.item_code, "custom_handling_charges_per_unit")

    #             item.conversion_factor = get_uom_conversion_factor(item.item_code, item.uom)
    #             print("<---item.conversion_factor--->",item.conversion_factor)
    #             _stq = item.conversion_factor * item.qty
    #             print("<---stq--->",_stq)
    #             item.stock_qty = _stq
    #             print("<---item.stock_qty--->",item.stock_qty)
    #             total_quantity = total_quantity + item.stock_qty
    #             print("<---total_quantity,total_quantity + item.stock_qty--->",item.stock_qty,total_quantity,item.stock_qty)
    #             total_weight = flt(item.weight_per_unit * item.stock_qty)
    #             print("<---total_weight,flt(item.weight_per_unit * item.stock_qty)--->",total_weight,item.weight_per_unit ,item.stock_qty)
    #             volume_per_unit_of_item = frappe.get_value("Item", item.item_code, "custom_volume_per_unit")
    #             item.volume_per_unit = volume_per_unit_of_item
    #             total_volume = volume_per_unit_of_item * item.qty
    #             area_per_unit_of_item = frappe.get_value("Item", item.item_code, "custom_area_per_unit")
    #             item.area_per_unit = area_per_unit_of_item
    #             total_area = area_per_unit_of_item * item.qty
    #             item.total_weight = total_weight
    #             item.total_volume = total_volume
    #             item.total_area = total_area
    #             total_net_weight = total_net_weight + total_weight
    #             total_net_volume = total_net_volume + total_volume
    #             total_net_area = total_net_area + total_area
    #             if _spc:
    #                 item.special_skill_charges_per_unit = flt(item.stock_qty * _spc)
    #             else:
    #                 item.special_skill_charges_per_unit = 0.0
    #             if _hcp:
    #                 item.handling_charges_per_unit = flt(item.stock_qty * _hcp)
    #             else:
    #                 item.handling_charges_per_unit = 0.0
    #             item.customer_purchase_order = self.name
    #             if self.required_pickup:
    #                 sum_of_charges = item.special_skill_charges_per_unit + item.handling_charges_per_unit
    #                 total_charges_amt += sum_of_charges
    #             item.opening_stock = frappe.get_value("Item", item.item_code, "opening_stock")
    #             received_percentage = flt((item.stock_qty / item.opening_stock) * 100) if item.opening_stock > 0 else 0
    #             # item.db_set("received", received_percentage)
                
    #             # Calculate total_final_price for the item by considering both spc and hcp
    #             # item_total_final_price = total_charges_amt
    #     total_final_price = total_charges_amt
    #     print("<---total_final_price--->",total_final_price)
    #     self.total_qty = total_quantity
    #     print("<---total_qty--->",self.total_qty)
    #     self.total_net_weight = total_net_weight
    #     print("<---total_net_weight--->",total_net_weight)
    #     self.total_net_volume = total_net_volume
    #     print("<---total_net_volume--->",total_net_volume)
    #     self.total_net_area = total_net_area
    #     print("<---total_net_area--->",total_net_area)
    #     pickup_distance = self.pickup_distance
    #     print("<---pickup_distance--->",pickup_distance)
    #     total_weight = self.total_net_weight
    #     print("<---total_weight--->",total_weight)
    #     total_volume = self.total_net_volume
    #     print("<---total_volume--->",total_volume)
    #     total_area = self.total_net_area
    #     print("<---total_area--->",total_area)
    #     customer = self.customer
    #     print("<---customer--->",customer)
    #     from_date = self.transaction_date
    #     print("**** date****",from_date)
    #     to_date = today()
    #     print("*****today date***",to_date)
    #     total = 0
    #     print("<---total--->",total)


    #     if self.required_pickup:
    #         if self.pickup_price_list == None:
    #             print('******8npot selcted pcikup losy ')
    #             price_list = self.get_matching_pickup_price_list(pickup_distance, total_weight, customer, from_date,to_date)
    #             print('pricelis******',price_list)

    #             self.pickup_price_list = price_list.get('parent')
    #             print("****self.pickup_price_list*****",self.pickup_price_list)

    #             if price_list and price_list.get('price_per_distance'):
    #                 self.applied_price_per_distance = price_list.get('price_per_distance')

    #                 price_per_distance = flt(price_list.get('price_per_distance'))
    #                 price_per_weight = flt(price_list.get('price_per_weight')) if 'price_per_weight' in price_list else 0

    #                 if price_per_weight:
    #                     # self.total_final_price = price_per_distance * flt(self.applied_price_per_distance) + price_per_weight * flt(self.total_weight)
    #                     total = price_per_distance * flt(self.total_net_weight) + price_per_weight * flt(self.total_net_weight) + total_final_price
    #                     self.total = total 
    #                     print('****1****total ',total)
    #                     print("price_per_distance * flt(self.total_net_weight) + price_per_weight * flt(self.total_net_weight) + total_final_price",
    #                           self.total_net_weight,price_per_weight,self.total_net_weight,total_final_price)
    #                     print("self.total 1---->",self.total)
    #                 else:
    #                     total = price_per_distance * flt(self.total_net_weight) + total_final_price 
    #                     self.total = total 
    #                     print('****2****total--->price_per_distance * flt(self.total_net_weight) + total_final_price ',total,
    #                           price_per_distance,self.total_net_weight,total_final_price)
    #                     print("self.total 2---->",self.total)
    #             else:
    #                 self.applied_price_per_distance = 0
    #                 # self.pickup_price_list = None
    #                 self.total = total 
    #                 print('***3*****total ',total)
    #                 print("self.total 3---->",self.total)

    #         else:
    #             price_list_data = self.selected_pickuplist()
    #             print("price_list_data---->",price_list_data)
    #             self.pickup_price_list = price_list_data.get('parent')
    #             if price_list_data and price_list_data.get('price_per_distance'):
    #                 self.applied_price_per_distance = price_list_data.get('price_per_distance')

    #                 price_per_distance = flt(price_list_data.get('price_per_distance'))
    #                 price_per_weight = flt(price_list_data.get('price_per_weight')) if 'price_per_weight' in price_list_data else 0

    #                 if price_per_weight:
    #                     # self.total_final_price = price_per_distance * flt(self.applied_price_per_distance) + price_per_weight * flt(self.total_weight)
    #                     total = price_per_distance * flt(self.total_net_weight) + price_per_weight * flt(self.total_net_weight) + total_final_price
    #                     self.total = total 
    #                     print('****1****$$$$$$$total ',total)
    #                 else:
    #                     total = price_per_distance * flt(self.total_net_weight) + total_final_price 
    #                     self.total = total 
    #                     print('****2############# ',total)
    #             else:
    #                 self.applied_price_per_distance = 0
    #                 # self.pickup_price_list = None
    #                 self.total = total 
    #                 print('***3*****total ',total)


    def selected_pickuplist(self):
            print("mnvjfbjfdjvbfdjbvf-------------------",self.pickup_price_list,"****",self.pickup_distance,"****",self.pickup_distance,"****",self.total_net_weight,"****",self.total_net_weight)
            price_matrix = frappe.get_all('Price Matrix', filters={
                'parent': self.pickup_price_list,
                'from_distance': ['<=', self.pickup_distance],
                'to_distance': ['>=', self.pickup_distance],
                'from_weight': ['<=', self.total_net_weight],
                'to_weight': ['>=', self.total_net_weight]
            }, fields=['parent', 'price_per_distance', 'price_per_weight'], limit=1)


            print("****priceMatrix***",price_matrix)
        
            if price_matrix:
                print("****priceMatrixvvuyhj***",price_matrix)
                price_info = price_matrix[0]
                if 'price_per_weight' in price_info:
                    return price_info
            else:
                frappe.throw("Pickup Price List Not Found or The Total Net Weight and Pickup Distance does not matching with the price list")
            return None


    def get_matching_pickup_price_list(self, pickup_distance, total_weight, customer, from_date,to_date):
        price_list = frappe.get_all('Pickup Price List', filters={
        'customer': customer,
        # 'from_date': ['<=', from_date],
        # 'to_date': ['>=', from_date]
        }, fields=['name'])

        print("**** 234 Price lidst",price_list)
        if price_list:
            print("****478 Price lidst",price_list)
            for record in price_list:
                print("****record****",record)
                price_matrix = frappe.get_all('Price Matrix', filters={
                    'parent': record.name,
                    'from_distance': ['<=', pickup_distance],
                    'to_distance': ['>=', pickup_distance],
                    'from_weight': ['<=', total_weight],
                    'to_weight': ['>=', total_weight]
                }, fields=['parent', 'price_per_distance', 'price_per_weight'], limit=1)

                print("****priceMatrix***",price_matrix)
               
                if price_matrix:
                    print("****priceMatrixvvuyhj***",price_matrix)
                    price_info = price_matrix[0]
                    if 'price_per_weight' in price_info:
                        return price_info
                    
                
        else:
                frappe.throw("Pickup Price List Not Found or The Total Net Weight and Pickup Distance does not matching with the price list")
        return None

    
def get_uom_conversion_factor(item_code, uom):
    conversion_factor = frappe.get_value("UOM Conversion Detail", 
                                        filters={
                                            "parent": item_code,
                                            "uom": uom
                                        },
                                        fieldname=["conversion_factor"],
                                        as_dict=True)
    return flt(conversion_factor.conversion_factor) if conversion_factor else 1
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

def autochange_status():
    ovd_cpo = frappe.get_all("Customer Purchase Order", ["transaction_date" ,"name", "required_pickup", "scheduled_date", "status" , "docstatus"])
    t = getdate(today())
    print("****ovd_cpu***",ovd_cpo)
    if ovd_cpo:
        for i in ovd_cpo:
            ovd = frappe.get_doc("Customer Purchase Order", i.name)
            if getdate(ovd.scheduled_date) >= t and ovd.docstatus == 1 and ovd.required_pickup == 1:
                ovd.status = "Scheduled"

                ovd.save()
                if ovd.required_pickup == 1 and ovd.docstatus == 1 and  getdate(ovd.scheduled_date) <= t and ovd.status == "Scheduled":
                    ovd.status = "Pickup Overdue"
                    ovd.save()
            elif ovd.required_pickup == 0 and ovd.docstatus == 1 and  getdate(ovd.transaction_date) >= t and ovd.status == "To Receive and Bill":
                    ovd.status = "Delivery Overdue"
                    ovd.save()

@frappe.whitelist()
def create_stock_entry(source_name):
    def postprocess(source, doc):
        print("SOURCE-->", source)
        print("DOC-->", doc)

        # doc.stock_entry_type = source.stock_entry_type
        doc.posting_date = source.pickup_request_date
        doc.posting_time = source.scheduled_time
        doc.stock_entry_type = "Material Receipt"
        customer_purchase_order_item = source.get("customer_purchase_order_item")

        # Define standard_rate here before using it in the loop
        standard_rate = 0  # Initialize with a default value
        for i in source.get("items"):
            c = frappe.get_doc("Item", i.item_code)
            if c:
                standard_rate = c.standard_rate

        if customer_purchase_order_item:
            for item in customer_purchase_order_item:
                doc.append("items", {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "description": item.description,
                    "uom": item.uom,
                    "qty": item.qty,
                    "stock_uom": item.stock_uom,
                    "transfer_qty": item.stock_qty,
                    "conversion_factor": item.conversion_factor,
                    # "allow_zero_valuation_rate": 1
                })

        # Set allow_zero_valuation_rate and basic_rate for each item
        for item in doc.get("items"):
            item.allow_zero_valuation_rate = 1
            item.basic_rate = standard_rate  # Use the standard_rate here

    doc = get_mapped_doc(
        "Customer Purchase Order",
        source_name,
        {
            "Customer Purchase Order": {"doctype": "Stock Entry"},
            "Customer Purchase Order Item": {"doctype": "Stock Entry Detail"},
        },
        None,
        postprocess,
    )

    return doc

@frappe.whitelist()
def get_items_from_purchase_order(selections):
    items = []
    selections = json.loads(selections)
    source_table_data = []
    for po in selections:
        doc = frappe.get_doc("Customer Purchase Order", po)
        source_table = doc.get('items')
        # basic_rate = frappe.get_doc("Item",)
        
        # if doc and doc.items:
        for row in source_table:
            source_table_data.append({
                "item_code": row.get("item_code"),
                "item_name": row.get("item_name"),
                "description": row.get("description"),
                "uom": row.get("uom"),
                "qty": row.get("qty"),
                # "basic_rate":standard_rate,
                "stock_uom": row.get("stock_uom"),
                "conversion_factor":row.get("conversion_factor"),
                "transfer_qty":row.get("stock_qty"),
                "allow_zero_valuation_rate": 1,  # Set the checkbox value here
                "customer_purchase_order":row.get("parent"),
                "customer_purchase_order_item":row.get("name")
            })
    return source_table_data

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@frappe.whitelist()
def get_availability_data(req_date, emp_grp):
    date = getdate(req_date)
    weekday = date.strftime("%A")

    eg_doc = frappe.get_doc("Employee Group", emp_grp)


    if eg_doc.custom_schedule:
        slot_details = get_available_slots(eg_doc, date)
    else:
        frappe.throw(
            _(
                "{0} does not have a  Schedule. Add it in Employee Group master"
            ).format(emp_grp),
            title=_("Pickup Team Schedule Not Found"),
        )

    if not slot_details:
        # TODO: return available slots in nearby dates
        frappe.throw(
            _("Pickup Team not available on {0}").format(weekday), title=_("Not Available")
        )

    return {"slot_details": slot_details}

def get_available_slots(eg_doc, date):
    available_slots = slot_details = []
    weekday = date.strftime("%A")
    pickup_team = eg_doc.name
    # for schedule_entry in practitioner_doc.pickup_schedules:
    # validate_pickup_schedules(schedule_entry, pickup_team)
    pickup_schedule = frappe.get_doc("Schedule", eg_doc.custom_schedule)

    if pickup_schedule and not pickup_schedule.disabled:
        available_slots = []
        for time_slot in pickup_schedule.time_slots:
            if weekday == time_slot.day:
                available_slots.append(time_slot)

        if available_slots:
            appointments = []
            # fetch all appointments to pickup_team by service unit
            filters = {
                "pickup_team": pickup_team,
                "scheduled_date": date,
                "status": ["in", ["Scheduled","Overdue"]],
            }
            
            slot_name = eg_doc.custom_schedule
            # fetch all appointments to pickup_team without service unit
            filters["pickup_team"] = pickup_team

            appointments = frappe.get_all(
				"Schedule",
			)

            slot_details.append(
                {
                    "slot_name": slot_name,
                    "avail_slot": available_slots,
                    "appointments": appointments
                }
            )
            print("*************",slot_details)
    return slot_details

@frappe.whitelist()
def create_customer_pr(source_name):
    def postprocess(source, doc):
        doc.posting_date = source.pickup_request_date
        doc.posting_time = source.scheduled_time
        doc.accepted_warehouse = source.accepted_warehouse
        for items in doc.items:
            if items.qty > items.pr_received_qty:
                items.qty = items.qty - items.pr_received_qty
                items.received_qty = items.qty 
            else:
                doc.items.pop(items.idx - 1)
        #Update index

        idx = 0
        for items in doc.items:
            items.idx = idx + 1
        # Define standard_rate here before using it in the loop
        standard_rate = 0  # Initialize with a default value
    doc = get_mapped_doc(
        "Customer Purchase Order",
        source_name,
        {
            "Customer Purchase Order": {"doctype": "Customer Purchase Receipt"},
            "Customer Purchase Order Item": {"doctype": "Customer Purchase Receipt Item"},
            
        },
        None,
        postprocess,
    )

    return doc
