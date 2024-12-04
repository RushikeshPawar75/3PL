frappe.ui.form.on("Stock Entry", {
    stock_entry_type: function(frm) {
        if (frm.doc.stock_entry_type === "Material Receipt") {
            console.log("--->Client Purchase Order Button Is Ready To Click")
            frm.add_custom_button(__('Client Purchase Order'), function() {
                var d = new frappe.ui.form.MultiSelectDialog({
                    doctype: "Client Purchase Order",
                    target: frm,
                    setters: {
                        transaction_date: undefined,
                        status: undefined
                    },
                    add_filters_group: 1,
                    get_query() {
                        return {
                            filters: { docstatus: ['!=', 2] },
                        };
                    },
                    get_query_filters: {
                        docstatus: 1,
                        // status: ["not in", ["Closed", "Completed", "Return Issued"]],
                        is_return: 0,
                    },
                    action(selections) {
                        if (selections && selections.length > 0) {
                            frappe.call({
                                method: "third_party_logistics.third_party_logistics.doctype.client_purchase_order.client_purchase_order.get_items_from_purchase_order",
                                
                                args: {
                                    selections: selections
                                },
                                callback: function(r) {
                                    if (r.message) {
                                        // console.log("rrrrrrrrrrrrrrr",r.message)
                                        frm.clear_table("items");
                                        $.each(r.message, function(i, item) {
                                            var row = frm.add_child("items");
                                            $.each(item, function(key, value) 
                                            {
                                                row[key] = value;
                                            });
                                        });
                                        frm.refresh_field("items");
                                    }
                                }
                            });
                        }

                        d.dialog.hide();
                    },
                });
            }, __('Get Items From'));
        }
    },
    on_submit: function(frm) {
        var docname = frm.doc.name;
        if (frm.doc.docstatus === 1 && frm.doc.stock_entry_type === "Material Receipt") {
            // Fetch the linked Client Purchase Order from Stock Entry Details
            frappe.model.with_doc("Stock Entry Detail", frm.doc.items[0].name, function() {
                var stock_entry_detail = frappe.model.get_doc("Stock Entry Detail", frm.doc.items[0].name);
                var client_purchase_order = stock_entry_detail.client_purchase_order;
                if (client_purchase_order) {
                    // Update the status of the linked Client Purchase Order
                    frappe.db.set_value("Client Purchase Order", client_purchase_order, "status", "To Receive and Bill", function(response) {
                        if (!response.exc) {
                            console.log("Status updated successfully!");
                        } else {
                            console.log("Error updating status:", response.exc);
                        }
                    });
                    
                }
    
            });
        }
        frappe.call({
            method:"third_party_logistics.third_party_logistics.doctype.Custom_stock_entry.update_value",
            args:{
                docname:docname
            },
            callback:function(){
                console.log("FFFFFFFFFFFFFFFFFFFFFFFFFFFF")
            }
        })
    }
});


