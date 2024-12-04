// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Storage Bill', {
	refresh: function(frm) {
		if (!frm.is_new()){
		  frm.remove_custom_button(__('Get Items From Storage Logs'))
	  }
		frm.set_query("customer", function() {
            return {
                filters: {
                    "custom_is_customer": 1
                }
            }
        });
		// frm.trigger("company")

		if(frm.doc.docstatus < 1){
			get_items_from_storage_log(frm)
		}
	},

	customer: function(frm){
		get_items_from_storage_log(frm)
		if(!frm.doc.customer){
			frm.remove_custom_buttom('Get Items From Storage Logs');
		
		}
		frm.set_value('items', '');
            frm.set_value('str_charges', '');
            frm.set_value('total_area_of_all_items', '');

	},
	company: function (frm) {
		frm.set_value('items', '');
		frm.set_value('str_charges', '');
		frm.set_value('total_area_of_all_items', '')
    },
});

function get_items_from_storage_log(frm) {
    frm.add_custom_button(__('Get Items From Storage Logs'), function() {
        if (!frm.doc.from_date || !frm.doc.to_date) {
            frappe.msgprint(__('Please select From Date and To Date before fetching items.'));
            return; // Exit the function if validation fails
        }
        if (frm.doc.to_date < frm.doc.from_date) {
            frappe.msgprint(__('To Date cannot be less than From Date.'));
            return; // Exit the function if validation fails
        }
        frappe.call({
            method: "update_items",
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    frm.refresh_field("items");
                    console.log(r.message);
                    frm.set_value('str_charges', r.message[0]);
                    frm.set_value('total_area_of_all_items', r.message[1]);
                }
            }
        });
    }).addClass('btn-primary');
}










// function get_items_from_storage_log(frm) {
// 	frm.add_custom_button(__('Get Items From Storage Logs'), function()
//                {
//                  frappe.call({
// 					method:"update_items",
// 					doc:frm.doc,
// 					callback:function(r){
// 						frm.refresh_field("items"),
// 						console.log(r.message),
// 						frm.set_value('str_charges', r.message[0]);
// 						frm.set_value('total_area_of_all_items',r.message[1]);
// 					}
// 				 })
//                }).addClass('btn-primary');
// }


// function amt_cal(frm,cdt,cdn) {
// 	var child = locals[cdt][cdn]
// 	if(child.qty && child.volume_in_price_uom && child.rate){
// 		var amt = child.qty * child.volume_in_price_uom * child.rate
// 		frappe.model.set_value(cdt,cdn,"amount",amt)
// 	}
// 	else{
// 		frappe.model.set_value(cdt,cdn,"amount",0.0)
// 	}
// }




// frappe.ui.form.on('Storage Bill Items', {
// 	qty:function(frm,cdt,cdn){
// 		amt_cal(frm,cdt,cdn)
		
// 	},
// 	volume_in_price_uom:function(frm,cdt,cdn){
// 		amt_cal(frm,cdt,cdn)
// 	},
// 	rate:function(frm,cdt,cdn){
// 		amt_cal(frm,cdt,cdn)
// 	}

// })


	// company: function(frm) {
	// 	if(frm.doc.company){

	// 		frappe.db.get_doc("Surplus Asset Settings").then(sett => {
	// 			if(sett.storage_defaults){

	// 				$.each(sett.storage_defaults, function(i, m) {
	// 					if(m.company == frm.doc.company){

	// 						frm.set_value("cost_center",m.cost_center)
	// 						frm.refresh_field("cost_center")
							
	// 					}
	// 				});

	// 			}
				

				
	// 		})

	// 	}
	// },

	// client: function(frm){
	// 	get_items_from_storage_log(frm)
	// 	if(!frm.doc.client){
			
	// 		console.log("--------------------rmoevr")
	// 		frm.remove_custom_buttom('Get Items From Storage Logs');
		
	// 	}
	// }


	// frappe.ui.form.on('Storage Bill', {
//     customer: function (frm) {
//         if (!frm.is_new() && frm.is_dirty()) {
//             // Clear fields only if the customer is manually changed before saving
//             frm.set_value('items', '');
//             frm.set_value('str_charges', '');
//             frm.set_value('total_area_of_all_items', '');
//         }
//     },
//     company: function (frm) {
//         if (!frm.is_new() && frm.is_dirty()) {
//             // Clear fields only if the company is manually changed before saving
//             frm.set_value('items', '');
//             frm.set_value('str_charges', '');
//             frm.set_value('total_area_of_all_items', '');
//         }
//     },
// 	refresh: function(frm) {
// 		if (!frm.is_new()){
// 			  // Remove the button if the document is saved
// 			frm.remove_custom_button(__('Get Items From Storage Logs'))
// 		}
// 	}
// });


// frappe.ui.form.on('Storage Bill', {
//     customer: function (frm) {
// 		console.log("customer")
//             // Clear fields only if the customer is manually changed before saving
//             frm.set_value('items', '');
//             frm.set_value('str_charges', '');
//             frm.set_value('total_area_of_all_items', '');
//         },
//     company: function (frm) {
// 		console.log("company")
//             // Clear fields only if the company is manually changed before saving
//             frm.set_value('items', '');
//             frm.set_value('str_charges', '');
//             frm.set_value('total_area_of_all_items', '')
//     },
	// refresh: function(frm) {
		// if (!frm.is_new()){
		// 	  // Remove the button if the document is saved
		// 	frm.remove_custom_button(__('Get Items From Storage Logs'))
		// }
	// }
// });
