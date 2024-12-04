// // Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// // For license information, please see license.txt
frappe.ui.form.on("Customer", {
    custom_send_otp: function(frm) {
        var docname = frm.doc.customer_name;
        var otpTimeout;

        frappe.call({
            method: "third_party_logistics.custom_two_step_authentication.send_otp",
            args: {
                docname: docname
            },
            callback: function(response) {
                var otp = response.message;

                // Show success alert for OTP sent
                frappe.show_alert({
                    message: "OTP sent successfully",
                    indicator: "green"
                });

                // Open OTP entry dialog
                var d = new frappe.ui.Dialog({
                    static: true,
                    title: 'Enter OTP',
                    fields: [
                        {
                            label: 'OTP',
                            fieldname: 'otp',
                            fieldtype: 'Data'
                        }
                    ],
                    primary_action_label: 'Submit',
                    primary_action: function(values) {
                        // Access the entered OTP value using values.otp
                        var enteredOtp = values.otp;
                        // Check if OTP field is empty
                        if (!enteredOtp) {
                            frappe.show_alert({
                                message: "Please Enter OTP",
                                indicator: "red"
                            });
                            return;
                        }
                        // Match the entered OTP with the actual OTP
                        if (enteredOtp === otp) {
                            // Set the checkbox field value to true (checked)
                            frm.set_value('custom_verified', 1);
                            frm.refresh_field('custom_verified');
                            frappe.msgprint("OTP matched successfully");
                            frappe.show_alert({
                                message: "Customer Verified Successfully",
                                indicator: "green"
                            });
                        } else {
                            // Throw an error message if OTP does not match
                            frappe.throw("Invalid OTP. Please try again.");
                        }

                        d.hide();
                    },
                    secondary_action_label: 'Cancel',
                    secondary_action: function() {
                        d.hide();
                        frappe.show_alert({
                            message: "Customer verification canceled",
                            indicator: "red"
                        });
                    },
                });

                // Manually center the dialog box
                var dialogContainer = d.$wrapper.find('.modal-dialog');
                dialogContainer.css('position', 'fixed');
                dialogContainer.css('top', '50%');
                dialogContainer.css('left', '50%');
                dialogContainer.css('transform', 'translate(-50%, -50%)');

                // Style the Cancel button with red color
                d.$wrapper.find('.modal-footer button.btn-secondary').css('background-color', 'red');
                d.$wrapper.find('.modal-footer button.btn-primary').css('background-color', 'green');
                d.show();

                // Expire OTP after 10 minutes
                otpTimeout = setTimeout(function() {
                    d.hide();
                    frappe.msgprint("OTP expired. Please try again.");
                }, 600000); // 600000 milliseconds = 10 minutes
            },
            error: function() {
                clearTimeout(otpTimeout);
            }
        });
    }
});
