// Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt
// rename customer_name to delivery_address deleted which is link with address

frappe.ui.form.on("Customer Purchase Receipt", {
	refresh: function(frm) {
        if (frm.doc.status == 'To Bill')
        {
		frm.add_custom_button(__('Customer Purchase Invoice'),function(){
            frappe.model.open_mapped_doc({
                method:"third_party_logistics.third_party_logistics.doctype.customer_purchase_receipt.customer_purchase_receipt.create_customer_inv",
                frm:frm,
            })
        },__('Create'));
    }
    if (frm.doc.status == 'To Bill' || frm.doc.status == 'Completed')
    {
        frm.add_custom_button(__('Close'),function(){
            frappe.model.open_mapped_doc({
                method:"third_party_logistics.third_party_logistics.doctype.customer_purchase_receipt.customer_purchase_receipt.create_customer_inv",
                frm:frm,
            })
        },__('Status'));
    }
	},
    customer: function(frm) {
        frm.set_value('items',[])
    },
    company: function(frm) {
        frm.set_value('items',[])
    },
    onload: function(frm) {
        frm.set_query("customer", function() {
            return {
                filters: {
                    "custom_is_customer": 1,
                }
            }
        });
        frm.set_query('accepted_warehouse', function() {
            return {
                filters: {
                    company: frm.doc.company,  // Filter by the company field in the form
                    "is_group": 0
                }
            };
        });
        
        frm.set_query('rejected_warehouse', function() {
            return {
                filters: {
                    company: frm.doc.company,
                    "is_group": 0
                }
            };
        });
        frm.set_query("item_code", "items", function() {
			return {
				filters: {"custom_item_customer": frm.doc.customer }
			}
		});
    } 
});
