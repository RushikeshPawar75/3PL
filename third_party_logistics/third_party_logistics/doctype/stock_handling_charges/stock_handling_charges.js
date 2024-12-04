// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt


frappe.ui.form.on('Stock Handling Charges', {
	validate:function(frm){
		frappe.call({
            method: 'update_record',
            doc: frm.doc,
            callback: function(response) {
                frm.refresh_field("pickup_charges");
				frm.refresh_field("material_handling_charges");
            }
        })
	},
	customer: function(frm) {
        const customer = frm.doc.customer;
        if (customer) {
            frappe.db.get_value('Customer', customer, 'customer_name', (data) => {
                const customerName = data.customer_name;
                console.log("#########",customerName);
                frm.set_value('customer_name', customerName);
            });
        } else {
            frm.set_value('customer_name', '');
        }
    },
    on_submit: function(frm) {
        console.log("DONE--------------->")
	},
	onload: function(frm) {
        frm.set_query("customer", function() {
            return {
                filters: {
                    "custom_is_customer": 1
                }
            }
        });
    },
});

