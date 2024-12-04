from frappe import _

# @frappe.whitelist()
def get_data():
    return {
        "fieldname": "pickup_entry",
       
        "transactions": [
            {"label": _("Customer Purchase Order"), "items": ["Customer Purchase Order"]},
            
        ],
    }