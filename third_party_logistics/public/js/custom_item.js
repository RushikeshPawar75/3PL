frappe.ui.form.on("Item", {
    onload: function(frm) {
        frm.set_query("custom_client", function() {
            return {
                filters: {
                    "custom_is_client": 1
                }
            }
    });
    }
});

//Nothing
