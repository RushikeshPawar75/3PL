import frappe
from frappe.model.document import Document
from frappe.utils import flt

@frappe.whitelist()
def update_value(docname):
    stock_entry = frappe.get_doc("Stock Entry", docname)
    
    for i in stock_entry.items:
        if i:
            sqty = i.get("qty")
            s_cpo = i.get("custom_customer_purchase_order")

            cpo = frappe.get_doc("Customer Purchase Order", s_cpo)
            
            total_recived_qty = 0
            total_c_qty = 0
            
            for j in cpo.items:
                if j.name == i.custom_customer_purchase_order_item:
                    if j:
                        c_qty = j.get("qty")
                        
                        if sqty: 
                            recived_qty = j.recived_qty + i.qty
                            received = j.received + ((sqty / c_qty) * 100)
                            total_recived_qty += recived_qty
                            total_c_qty += c_qty
                            j.db_set("received", received)
                            j.db_set("recived_qty", recived_qty)
            
            if total_c_qty > 0:
                recived_per = (total_recived_qty / total_c_qty) * 100
                cpo.db_set("received_per", recived_per)  # Set the received percentage for the Client Purchase Order
                print("Total recived_per:", recived_per)
