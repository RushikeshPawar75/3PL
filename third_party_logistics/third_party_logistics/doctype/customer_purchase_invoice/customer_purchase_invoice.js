// Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Purchase Invoice", {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1 && frm.doc.status != 'Paid')
		{
		frm.add_custom_button(__('Create Customer Payment Entry'), function(){
			frappe.call({
				method: "customer_payment_entry",
				doc:frm.doc,
				callback: function(r){
					if(r) {
						cur_frm.reload_doc();
						frappe.throw("Already Customer Payment Entry Created. Please Submit Customer Payment Entry")
					}
					else
					{
						cur_frm.reload_doc();
					}
				}
			});
		}).addClass("btn-primary");
	}
	}
});
frappe.ui.form.on('Customer Purchase Invoice Item', {
	rate: function(frm, cdt, cdn) {
		var child_row = locals[cdt][cdn];
		var sum = child_row.rate * child_row.qty
		frappe.model.set_value(cdt, cdn, 'amount', sum);
	},
	qty: function(frm, cdt, cdn) {
		var child_row = locals[cdt][cdn];
		var sum = child_row.rate * child_row.qty
		frappe.model.set_value(cdt, cdn, 'amount', sum);
	}

});


frappe.ui.form.on('Customer Purchase Invoice', {
    onload: function(frm) {
        frm.set_query("item_code", "items", function() {
            return {
                filters: { "custom_item_customer": frm.doc.customer }
            };
        });
		frm.set_query("customer", function() {
            return {
                filters: {
                    "custom_is_customer": 1
                }
            };
        });

        // Filter customer_name based on link_doctype and link_name
        frm.set_query("delivery_address", function() {
            return {
                filters: {
                    "link_doctype": 'Company',
                    "link_name": frm.doc.company
                }
            };
        });
    },
	customer: function(frm) {
        frm.set_value('items',[])
    },
	company: function(frm) {
        frm.set_value('items',[])
    },
});
