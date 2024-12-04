// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pickup Entry', {
    onload: function(frm) {
        frm.set_query("customer_purchase_order", function() {
            return {
                filters: {
                    "pickup_team": frm.doc.pickup_team,
					// "pickup_request_date":frm.doc.pickup_request_date,
					"company":frm.doc.company,
					"status":"Scheduled"
                }
            }
        })
    },

    pickup_team:  function(frm) {
        frm.set_value('customer_purchase_order','')
        // frm.doc.customer_purchase_order=undefined
        // frm.refresh_field('customer_purchase_order')
           
    },
    company: function(frm) {
        // Clear the Customer Purchase Order field when company changes
        frm.set_value('customer_purchase_order', '');
    },
        
});



















    // pickup_request_date:  function(frm) {
    //     frm.set_value('customer_purchase_order','')
    //     // frm.doc.customer_purchase_order=undefined
    //     // frm.refresh_field('customer_purchase_order')
           
    // }