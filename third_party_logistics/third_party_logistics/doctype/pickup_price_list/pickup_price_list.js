// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pickup Price List', {
	onload: function(frm) {
		frm.set_query("customer", function() {
            return {
                filters: {
                    "custom_is_customer": 1
                }
            }
        });
	}
});



frappe.ui.form.on('Price Matrix', {
	weight_dependent: function(frm) {
        console.log("print the data")
		frm.refresh_field('price_matrix')
	}
});