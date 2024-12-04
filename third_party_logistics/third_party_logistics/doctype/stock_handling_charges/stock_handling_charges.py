# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class StockHandlingCharges(Document):
    @frappe.whitelist()
    def update_record(self):
        from_date = self.from_date
        to_date = self.to_date
        self.pickup_charges = []
        
		
        if self.customer and from_date and to_date:
            stock_entries = frappe.get_all("Stock Entry",
                filters={"docstatus": 1,
                         "posting_date": ("between", [from_date, to_date])},
                fields=["name"]
            )

            for se in stock_entries:
                stock_entry = frappe.get_doc("Stock Entry", se.name)
                for item in stock_entry.items:
                    if item.custom_customer_purchase_order:
                        cpo = frappe.get_doc("Customer Purchase Order", item.custom_customer_purchase_order)
                        if cpo.customer == self.customer:
                            items = frappe.get_all("Customer Purchase Order Item",
								filters={"parent": cpo.name},
								fields=["handling_charges_per_unit", "special_skill_charges_per_unit","qty","stock_uom","weight_uom","item_code",]
							)
                            total_handling_charges = sum(item.handling_charges_per_unit for item in items)
                            total_special_skill_charges = sum(item.special_skill_charges_per_unit for item in items)
                            # qty = sum(item.qty for item in items)
                            
                            # stock_uom = (item.stock_uom for item in items)
                            # print("QTYYYYYYYYYYYYY",stock_uom)

                            self.append("pickup_charges", {
								"stock_entry": se.name,
								"date":stock_entry.posting_date,
								"customer_po": cpo.name,
								"pickup_price_list": cpo.pickup_price_list,
								"total_weight": cpo.total_net_weight,
								"distance": cpo.pickup_distance,
								"amount": cpo.total_final_price,
								"handling_charges": total_handling_charges,
								"special_skilled_labor_charges": total_special_skill_charges
							})
                self.material_handling_charges = []
                for pickup_charge in self.pickup_charges:
                    if pickup_charge.handling_charges > 0 or pickup_charge.special_skilled_labor_charges > 0:
                        stock_entry = frappe.get_doc("Stock Entry", pickup_charge.stock_entry)
                        stock_entry_type = stock_entry.stock_entry_type
                        
                        stock_entry_items = frappe.get_all("Stock Entry Detail",
                            filters={"parent": pickup_charge.stock_entry},
                            fields=["item_code", "qty" ,"stock_uom","transfer_qty", "conversion_factor", "custom_client_purchase_order"]
                        )
                        
                        for stock_entry_item in stock_entry_items:
                            if stock_entry_item.custom_client_purchase_order == pickup_charge.customer_po:
                                cpo_item = next((item for item in items if item.item_code == stock_entry_item.item_code), None)
                                weight_uom = cpo_item.weight_uom if cpo_item else None  # Get weight_uom from Client Purchase Order Item
                                # qty = cpo_item.qty if cpo_item else None  # Get qty from Client Purchase Order Item


                                self.append("material_handling_charges", {
                                    "stock_entry": pickup_charge.stock_entry,
                                    "date": pickup_charge.date,
                                    "handling_charges": pickup_charge.handling_charges,
                                    "special_skilled_labor_charges": pickup_charge.special_skilled_labor_charges,
                                    "conversion_factor": stock_entry_item.conversion_factor, 
                                    "stock_uom": stock_entry_item.stock_uom,
                                    "item": stock_entry_item.item_code,
                                    "stock_qty": stock_entry_item.transfer_qty,
                                    "type": stock_entry_type,
                                    "weight_uom":weight_uom,
                                    "qty":stock_entry_item.qty
                                })
    def on_submit(self):
        for material_charge in self.material_handling_charges:
            if material_charge.handling_charges > 0 or material_charge.special_skilled_labor_charges > 0:
                
                sales_invoice = frappe.new_doc("Sales Invoice")
                sales_invoice.customer = self.customer  # Set the customer based on the client
                
                # Add items to the Sales Invoice
                sales_invoice.append("items", {
                    "item_code": material_charge.item,
                    "qty": material_charge.qty,
                    "uom": material_charge.stock_uom,
                    
                    # "rate": material_charge.handling_charges + material_charge.special_skilled_labor_charges,
                    # ... Set other relevant fields ...
                })

                # Save the Sales Invoice
                sales_invoice.save(ignore_permissions = True)
                frappe.msgprint(_("Sales Invoice {0} created").format(sales_invoice.name))
        

                