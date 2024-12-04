// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Storage Price List', {
	// refresh: function(frm) {

	// },
	onload:function(frm){
		frm.set_query("customer", function() {
            return {
                filters: {
                    "custom_is_customer": 1
                }
            }
        });
	},
});




frappe.ui.form.on('Storage Price List', {
    price_as_per: function(frm) {
        // Reset the fields when the dropdown value changes
        frm.set_value("area_uom", "");
        frm.set_value("weight_uom", "");
        frm.set_value("volume_uom", "");

        // Refresh the fields to reflect the changes
        frm.refresh_field("area_uom");
        frm.refresh_field("weight_uom");
        frm.refresh_field("volume_uom");
    }
});

