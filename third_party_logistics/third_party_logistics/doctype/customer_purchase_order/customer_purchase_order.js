// Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt
frappe.ui.form.on("Customer Purchase Order", {
	onload: function(frm) {
        frm.set_query("customer", function() {
            return {
                filters: {
                    "custom_is_customer": 1
                }
            }
        });
		frm.set_query("delivery_address", function() {
            return {
                filters: {
                    "link_doctype": 'Company',
                    "link_name":frm.doc.company
                }
            }
        });
        frm.set_query("supplier", function() {
            return {
                filters: {
                    "custom_is_customer": 1,
                    "custom_customer": frm.doc.customer
                }
            }
        });
    },
    delivery_address: function(frm) {
		if (frm.doc.delivery_address) {
			frappe.call({
				method: 'frappe.contacts.doctype.address.address.get_address_display',
				args: {
					"address_dict": frm.doc.delivery_address
				},
				callback: function(r) {
					frm.set_value("address_display", r.message);
				}
			});
		}
		if (!frm.doc.delivery_address) {
			frm.set_value("address_display", "");
		}
	},
    company:function(frm) {
        frm.doc.delivery_address=undefined
        frm.refresh_field('delivery_address')
    },
    required_pickup: function(frm) {
        if (frm.doc.required_pickup == 1) {
            frm.doc.status = "Pickup to be Scheduled";
            frm.refresh_field('status');
        }
        else
        {
            frm.doc.status = "Draft";
            frm.refresh_field('status');
        }
    },   
    refresh: function(frm) {
        
        frm.set_query("item_code", "items", function() {
			return {
				filters: {"custom_item_customer": frm.doc.customer }
			}
		});
        if (frm.doc.status == 'To Receive and Bill'){
            frm.set_df_property('required_pickup', 'read_only', 1);
            frm.set_df_property('pickup_request_date', 'read_only', 1);
        }
        if ( frm.doc.pickup_entry && frm.doc.docstatus === 1 && frm.doc.status != 'Closed' && frm.doc.status != 'Received') {
        frm.add_custom_button(__('Customer Purchase Receipt'),function(){
            frappe.model.open_mapped_doc({
                method:"third_party_logistics.third_party_logistics.doctype.customer_purchase_order.customer_purchase_order.create_customer_pr",
                frm:frm,
            })
        },__('Create'));
    }
    if (frm.doc.docstatus === 1)
    {
            frm.add_custom_button(__('Close'), function() {
                frappe.call({
                    method: "close_order",
                    doc:frm.doc,
                    args: {            
                        status: 'Closed'
                    },
                    callback: function(r) {
                        if(r){
                            frappe.msgprint(__('Customer Purchase Order Closed Successfully.'));
                            frm.refresh_field("status")
                            cur_frm.reload_doc();
                        }
                    }
                });
            },__('Status'));
    }

        if (frm.doc.status === "Pickup to be Scheduled" && frm.doc.docstatus === 1) {
            // frm.doc.docstatus === frm.doc.status
            frm.add_custom_button(__('Schedule Pickup'), function() {
                check_and_set_availability(frm);
                
            }).addClass("btn-primary");
        }
        else if(frm.doc.status == "Scheduled" || frm.doc.status == "Pickup Overdue"){
			frm.add_custom_button(__('Reschedule Pickup'), function() {
				check_and_set_availability2(frm);
				
		
			}).addClass("btn-primary");
        }
        
        let check_and_set_availability = function(frm) {
            let selected_slot = null;
            let scheduled_duration = null;
        
            show_availability();


            function show_availability() {  
                let selected_pickup_team = '';
                let d = new frappe.ui.Dialog({
                    title: __('Schedule Pickup'),
                    fields: [
                        { fieldtype: 'Date', reqd: 1, fieldname: 'req_date', label: 'Pickup Date', 'default': frm.doc.pickup_request_date },
                        { fieldtype: 'Column Break' },
                        { fieldtype: 'Int', reqd: 1, fieldname: 'scheduled_duration', label: 'Duration (In Mins)' },
                        { fieldtype: 'Link', options: 'Employee Group', reqd: 1, fieldname: 'pickup_team', label: 'Pickup Team' , depends_on: "eval:doc.req_date"},
                        { fieldtype: 'Section Break' },
                        { fieldtype: 'HTML', fieldname: 'available_slots' }
                    ],
                    primary_action_label: __('Book'),
                    primary_action: function(values) {
                        console.log("#######")
                        let time =show_slots(d, fd)
                        console.log("33333333",time)
                        frappe.call({
                            method:"update_record",
                            doc:frm.doc,
                            args:{
                                status:"Scheduled",
                                date: values.req_date,
                                time:selected_slot,
                                
                                scheduled_duration:values.scheduled_duration,
                                pickup_team:values.pickup_team
    
                            },
                            callback:function(r){
                                frm.refresh_field("scheduled_time")
                                frm.refresh_field("scheduled_date")
                                frm.refresh_field("scheduled_duration")
                                frm.refresh_field("pickup_team")
                                frm.refresh_field("status")
                            window.location.reload()
                                
                            }
                        });
                        d.hide();
                    }
                });

                let fd = d.fields_dict;
                d.fields_dict['req_date'].df.onchange = () => {
                    show_slots(d, fd);
                };
                d.fields_dict['pickup_team'].df.onchange = () => {
                    if (d.get_value('pickup_team') && d.get_value('pickup_team') != selected_pickup_team) {
                        selected_pickup_team = d.get_value('pickup_team');
                        console.log("selected pickup team",selected_pickup_team)
                        show_slots(d, fd);
                    };
                    d.fields_dict['pickup_team'].df.onchange = () => {
                        if (d.get_value('pickup_team') && d.get_value('pickup_team') != selected_pickup_team) {
                            frappe.db.get_doc("Employee Group",d.get_value('pickup_team')).then(eg => {
                                if(eg.schedule){
                                    frappe.db.get_doc("Schedule",eg.schedule).then(sch => {
                                        if(sch.scheduled_duration){
                                            d.set_value("scheduled_duration",sch.scheduled_duration)
                                        }
                                    })
                                }
                            })
                            selected_pickup_team = d.get_value('pickup_team');
                            show_slots(d, fd);
                        }
                    };
                };

                d.show();

                function show_slots(d, fd) {
                    if (d.get_value('pickup_team')) {
                        fd.available_slots.html('');
                        frappe.call({
                            method: 'third_party_logistics.third_party_logistics.doctype.customer_purchase_order.customer_purchase_order.get_availability_data',
                            args: {
                                
                                req_date: d.get_value('req_date'),
                                emp_grp: d.get_value('pickup_team')
                            },
                            error: function(r) {
                                console.log( "Code is work",r)
                                d.get_primary_btn().attr('disabled', true);
                            },
                            callback: (r) => {
                                let data = r.message;
                                console.log("data res from show slots",r.message)
                                if (data.slot_details.length > 0) {
                                    console.log("data avial_sot",data.slot_details[0].avail_slot)
                                    let slots_name = data.slot_details[0].avail_slot.map((a)=>a.from_time)
                                    console.log("slots name",slots_name)
                                    let $wrapper = d.fields_dict.available_slots.$wrapper;
                
                                    // make buttons for each slot
                                    let slot_html = get_slots(data.slot_details, d.get_value('req_date'));
                                    console.log(slot_html)
                
                                    $wrapper
                                        .css('margin-bottom', 0)
                                        .addClass('text-center')
                                        .html(slot_html);
                
                                    // highlight button when clicked
                                    $wrapper.on('click', 'button', function() {
                                    console.log("slot button clicked")
                                        let $btn = $(this);
                                        // $wrapper.find('button').removeClass('btn-outline-primary');
                                        slots_name.forEach((sl)=>{
                                            console.log(`[data-name="${sl}"]`)
                                            let list=d.$wrapper.find(`[data-name="${sl}"]`)
                                            console.log("sl",sl,list)
                                            list.css('outline', 'none');
                                        })

                                        $btn.css('outline', '1px solid blue');
                                        $btn.addClass('btn-outline-primary');
                                        selected_slot = $btn.attr('data-name');
                                        // service_unit = $btn.attr('data-service-unit');
                                        duration = $btn.attr('data-duration');
                                        
                                            d.$wrapper.find(".opt-out-conf-div").hide();
                                        // }
                
                                        // enable primary action 'Book'
                                        d.get_primary_btn().attr('disabled', null);
                                    });

                                    d.get_primary_btn().attr('disabled', true);
                
                                } else {
                                    console.log("--------------------empty state")
                                    //	fd.available_slots.html('Please select a valid date.'.bold())
                                    show_empty_state(d.get_value('pickup_team'), d.get_value('req_date'));
                                }
                            },
                            freeze: true,
                            freeze_message: __('Fetching Schedule...')
                        });
                    } else {
                        fd.available_slots.html(__('Pickup date and Pickup Team are Mandatory').bold());
                    }
                }
                function get_slots(slot_details, appointment_date) {
                    let slot_html = '';
                    let appointment_count = 0;
                    let disabled = false;
                    let start_str, slot_start_time, slot_end_time, interval, count, count_class, tool_tip, available_slots;
                
                    slot_details.forEach((slot_info) => {
                        slot_html += `<div class="slot-info">
                            <span><b>
                            ${__('Pickup Schedule: ')} </b> ${slot_info.slot_name}
                            </span><br>`;
                
                        
                
                        slot_html += '</div><br>';
                
                        slot_html += slot_info.avail_slot.map(slot => {
                            appointment_count = 0;
                            disabled = false;
                            count_class = tool_tip = '';
                            start_str = slot.from_time;
                            slot_start_time = moment(slot.from_time, 'HH:mm:ss');
                            slot_end_time = moment(slot.to_time, 'HH:mm:ss');
                            interval = (slot_end_time - slot_start_time) / 60000 | 0;
                
                            // restrict past slots based on the current time.
                            let now = moment();
                            if((now.format("YYYY-MM-DD") == appointment_date) && slot_start_time.isBefore(now)){
                                disabled = true;
                            } else {
                                // iterate in all booked appointments, update the start time and duration
                                slot_info.appointments.forEach((booked) => {
                                    console.log("-------------booked",booked)
                                    let booked_moment = moment(booked.scheduled_time, 'HH:mm:ss');
                                    console.log("-------------booked_moment",booked_moment)
                                    let end_time = booked_moment.clone().add(booked.duration, 'minutes');
                                    console.log("-------------end_time",end_time)
                
                                    // Deal with 0 duration appointments
                                    if (booked_moment.isSame(slot_start_time) || booked_moment.isBetween(slot_start_time, slot_end_time)) {
                                        if (booked.duration == 0) {
                                            disabled = true;
                                            return false;
                                        }
                                    }
                
                                    // Check for overlaps considering appointment duration
                                    if (slot_info.allow_overlap != 1) {
                                        if (slot_start_time.isBefore(end_time) && slot_end_time.isAfter(booked_moment)) {
                                            // There is an overlap
                                            disabled = true;
                                            return false;
                                        }
                                    } else {
                                        if (slot_start_time.isBefore(end_time) && slot_end_time.isAfter(booked_moment)) {
                                            appointment_count++;
                                        }
                                        if (appointment_count >= 1) {
                                            // There is an overlap
                                            disabled = true;
                                            return false;
                                        }
                                    }
                                });
                            }
                
                            
                
                            return `
                                <button class="btn btn-secondary" data-name=${start_str}
                                    data-duration=${interval}
                                    style="margin: 0 10px 10px 0; width: auto;" ${disabled ? 'disabled="disabled"' : ""}
                                    data-toggle="tooltip" title="${tool_tip || ''}">
                                    ${start_str.substring(0, start_str.length - 3)}
                                    ${slot_info.service_unit_capacity ? `<br><span class='badge ${count_class}'> ${count} </span>` : ''}
                                </button>`;
                
                        }).join("");
                
                        if (slot_info.service_unit_capacity) {
                            slot_html += `<br/><small>${__('Each slot indicates the capacity currently available for booking')}</small>`;
                        }
                        slot_html += `<br/><br/>`;
                    });
                
                    return slot_html;
                }
            }
        };
        let check_and_set_availability2 = function(frm) {
            let selected_slot = null;
            let scheduled_duration = null;
        
            show_availability();
            function show_availability() {  
                let selected_pickup_team = '';
                let d = new frappe.ui.Dialog({
                    title: __('Reschedule Pickup'),
                    fields: [
                        { fieldtype: 'Date', reqd: 1, fieldname: 'req_date', label: 'Pickup Date', 'default': frm.doc.pickup_request_date },
                        { fieldtype: 'Column Break' },
                        { fieldtype: 'Int', reqd: 1, fieldname: 'scheduled_duration', label: 'Duration (In Mins)' ,default:0},
                        { fieldtype: 'Link', options: 'Employee Group', reqd: 1, fieldname: 'pickup_team', label: 'Pickup Team' ,depends_on: "eval:doc.req_date"},
                        { fieldtype: 'Section Break' },
                        { fieldtype: 'HTML', fieldname: 'available_slots' }
                    ],
                    primary_action_label: __('Book'),
                    primary_action: function(values) {
                        console.log("#######")
                        let time =show_slots(d, fd)
                        console.log("33333333",time)
                        frappe.call({
                            method:"update_record",
                            doc:frm.doc,
                            args:{
                                status:"Scheduled",
                                date: values.req_date,
                                time:selected_slot,
                                
                                scheduled_duration:values.scheduled_duration,
                                pickup_team:values.pickup_team
    
                            },
                            callback:function(r){
                                frm.refresh_field("scheduled_time")
                                frm.refresh_field("scheduled_date")
                                frm.refresh_field("scheduled_duration")
                                frm.refresh_field("pickup_team")
                                frm.refresh_field("status")
                                window.location.reload()
                                    d.hide();
                            }
                        });
                    
                    }
                });

                let fd = d.fields_dict;
                d.fields_dict['req_date'].df.onchange = () => {
                    show_slots(d, fd);
                };
                d.fields_dict['pickup_team'].df.onchange = () => {
                    if (d.get_value('pickup_team') && d.get_value('pickup_team') != selected_pickup_team) {
                        selected_pickup_team = d.get_value('pickup_team');
                        console.log("selected pickup team",selected_pickup_team)
                        show_slots(d, fd);
                    };
                    d.fields_dict['pickup_team'].df.onchange = () => {
                        if (d.get_value('pickup_team') && d.get_value('pickup_team') != selected_pickup_team) {
                            frappe.db.get_doc("Employee Group",d.get_value('pickup_team')).then(eg => {
                                if(eg.schedule){
                                    frappe.db.get_doc("Schedule",eg.schedule).then(sch => {
                                        if(sch.scheduled_duration){
                                            d.set_value("scheduled_duration",sch.scheduled_duration)
                                        }
                                    })
                                }
                            })
                            selected_pickup_team = d.get_value('pickup_team');
                            show_slots(d, fd);
                        }
                    };
                };

                d.show();

                function show_slots(d, fd) {
                    if (d.get_value('pickup_team')) {
                        fd.available_slots.html('');
                        frappe.call({
                            method: 'third_party_logistics.third_party_logistics.doctype.customer_purchase_order.customer_purchase_order.get_availability_data',
                            args: {
                                
                                req_date: d.get_value('req_date'),
                                emp_grp: d.get_value('pickup_team')
                            },
                            error: function(r) {
                                console.log( "Code is work",r)
                                d.get_primary_btn().attr('disabled', true);
                            },
                            callback: (r) => {
                                let data = r.message;
                                console.log("data res from show slots",r.message)
                                if (data.slot_details.length > 0) {
                                    console.log("data avial_sot",data.slot_details[0].avail_slot)
                                    let slots_name = data.slot_details[0].avail_slot.map((a)=>a.from_time)
                                    console.log("slots name",slots_name)
                                    let $wrapper = d.fields_dict.available_slots.$wrapper;
                
                                    // make buttons for each slot
                                    let slot_html = get_slots(data.slot_details, d.get_value('req_date'));
                
                                    $wrapper
                                        .css('margin-bottom', 0)
                                        .addClass('text-center')
                                        .html(slot_html);
                
                                    // highlight button when clicked
                                    $wrapper.on('click', 'button', function() {
                                    console.log("slot button clicked")
                                        let $btn = $(this);
                                        // $wrapper.find('button').removeClass('btn-outline-primary');
                                        
                                        slots_name.forEach((sl)=>{
                                            console.log(`[data-name="${sl}"]`)
                                            let list=d.$wrapper.find(`[data-name="${sl}"]`)
                                            console.log("sl",sl,list)
                                            list.css('outline', 'none');
                                        })
                        
                                        $btn.css('outline', '1px solid blue');
                                        $btn.addClass('btn-outline-primary');
                                        selected_slot = $btn.attr('data-name');
                                        // service_unit = $btn.attr('data-service-unit');
                                        duration = $btn.attr('data-duration');
                                        
                                            d.$wrapper.find(".opt-out-conf-div").hide();
                                        // }
                
                                        // enable primary action 'Book'
                                        d.get_primary_btn().attr('disabled', null);
                                    });

                                    d.get_primary_btn().attr('disabled', true);
                
                                } else {
                                    console.log("--------------------empty state")
                                    //	fd.available_slots.html('Please select a valid date.'.bold())
                                    show_empty_state(d.get_value('pickup_team'), d.get_value('req_date'));
                                }
                            },
                            freeze: true,
                            freeze_message: __('Fetching Schedule...')
                        });
                    } else {
                        fd.available_slots.html(__('Pickup date and Pickup Team are Mandatory').bold());
                    }
                }
                function get_slots(slot_details, appointment_date) {
                    let slot_html = '';
                    let appointment_count = 0;
                    let disabled = false;
                    let start_str, slot_start_time, slot_end_time, interval, count, count_class, tool_tip, available_slots;
                
                    slot_details.forEach((slot_info) => {
                        slot_html += `<div class="slot-info">
                            <span><b>
                            ${__('Pickup Schedule: ')} </b> ${slot_info.slot_name}
                            </span><br>`;
                
                        
                
                        slot_html += '</div><br>';
                
                        slot_html += slot_info.avail_slot.map(slot => {
                            appointment_count = 0;
                            disabled = false;
                            count_class = tool_tip = '';
                            start_str = slot.from_time;
                            slot_start_time = moment(slot.from_time, 'HH:mm:ss');
                            slot_end_time = moment(slot.to_time, 'HH:mm:ss');
                            interval = (slot_end_time - slot_start_time) / 60000 | 0;
                
                            // restrict past slots based on the current time.
                            let now = moment();
                            if((now.format("YYYY-MM-DD") == appointment_date) && slot_start_time.isBefore(now)){
                                disabled = true;
                            } else {
                                // iterate in all booked appointments, update the start time and duration
                                slot_info.appointments.forEach((booked) => {
                                    console.log("-------------booked",booked)
                                    let booked_moment = moment(booked.scheduled_time, 'HH:mm:ss');
                                    console.log("-------------booked_moment",booked_moment)
                                    let end_time = booked_moment.clone().add(booked.duration, 'minutes');
                                    console.log("-------------end_time",end_time)
                
                                    // Deal with 0 duration appointments
                                    if (booked_moment.isSame(slot_start_time) || booked_moment.isBetween(slot_start_time, slot_end_time)) {
                                        if (booked.duration == 0) {
                                            disabled = true;
                                            return false;
                                        }
                                    }
                
                                    // Check for overlaps considering appointment duration
                                    if (slot_info.allow_overlap != 1) {
                                        if (slot_start_time.isBefore(end_time) && slot_end_time.isAfter(booked_moment)) {
                                            // There is an overlap
                                            disabled = true;
                                            return false;
                                        }
                                    } else {
                                        if (slot_start_time.isBefore(end_time) && slot_end_time.isAfter(booked_moment)) {
                                            appointment_count++;
                                        }
                                        if (appointment_count >= 1) {
                                            // There is an overlap
                                            disabled = true;
                                            return false;
                                        }
                                    }
                                });
                            }
                
                            
                
                            return `
                                <button class="btn btn-secondary" data-name=${start_str}
                                    data-duration=${interval}
                                    style="margin: 0 10px 10px 0; width: auto;" ${disabled ? 'disabled="disabled"' : ""}
                                    data-toggle="tooltip" title="${tool_tip || ''}">
                                    ${start_str.substring(0, start_str.length - 3)}
                                    ${slot_info.service_unit_capacity ? `<br><span class='badge ${count_class}'> ${count} </span>` : ''}
                                </button>`;
                
                        }).join("");
                
                        if (slot_info.service_unit_capacity) {
                            slot_html += `<br/><small>${__('Each slot indicates the capacity currently available for booking')}</small>`;
                        }
                        slot_html += `<br/><br/>`;
                    });
                
                    return slot_html;
                }
            }
        };
    }
});
frappe.ui.form.on('Customer Purchase Order Item', {
    item_code: function(frm, cdt, cdn) {
        // if (!frm.doc.customer)
        // {
        //     frm.doc.item_code = "";  
        //     frm.refresh_field('item_code');
        //     frappe.throw(__("Please select Customer"));
        // } 
        var child_row = locals[cdt][cdn];
        // Fetch the selected item details
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Item',
                'filters': {
                    'name': child_row.item_code
                },
                'fieldname': ['stock_uom']
            },
            callback: function(response) {
                if (response && response.message) {
                    // Set the UOM value in the child row
                    frappe.model.set_value(cdt, cdn, 'uom', response.message.stock_uom);
                }
            }
        });
    },

    // Triggered when a row is deleted from the child table
    before_item_remove: function(frm, cdt, cdn) {
        var child_row = locals[cdt][cdn];

        // Clear the UOM value when the row is deleted
        frappe.model.set_value(cdt, cdn, 'uom', '');
    }
});

frappe.ui.form.on("Customer Purchase Order", {

    onload: function(frm) {
        // Filter customer based on custom_is_customer field
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
        // Fetch and set query for pickup price list based on the selected customer
        frm.set_query("pickup_price_list", function() {
            console.log("frappe.datetime.now_date()",frappe.datetime.now_date())
            return {
                filters: {
                    "customer": frm.doc.customer,
                    "from_date":['<=',frappe.datetime.now_date()],
                    // "to_date":['>=',frappe.datetime.now_date()],
                    "company":frm.doc.company
                    
                }
            };
        });

        // Automatically fetch and set pickup price list if only one exists for the customer
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Pickup Price List",
                filters: {
                    "customer": frm.doc.customer,
                    "from_date":['<=',frappe.datetime.now_date()],
                    // "to_date":['>=',frappe.datetime.now_date()],
                    
                },
                fields: ["name"]
            },
            callback: function(r) {
                if (r.message && r.message.length === 1) {
                    frm.set_value("pickup_price_list", r.message[0].name);
                }
            },
        });
    },
    pickup_price_list:function(frm) {
        if (!frm.doc.customer) {
            frappe.msgprint(__("Please select a customer first before choosing a pickup price list."));
    }

}});


frappe.ui.form.on('Customer Purchase Order', {
    onload: function(frm) {
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
    }
});


frappe.ui.form.on('Customer Purchase Order', {
    onload: function(frm) {
        if (frm.doc.docstatus === 1) { // Check if the document is submitted
            frm.set_df_property('pickup_request_date', 'read_only', 1);
            frm.set_df_property('pickup_distance', 'read_only', 1);
            frm.set_df_property('required_pickup', 'read_only', 1);
        }
    },
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) { // Ensure fields remain non-editable on refresh
            frm.set_df_property('pickup_request_date', 'read_only', 1);
            frm.set_df_property('pickup_distance', 'read_only', 1);
            frm.set_df_property('required_pickup', 'read_only', 1);
        }
    },
    customer: function(frm) {
        frm.set_value('items',[])
        // frm.doc.customer_purchase_order=undefined
        // frm.refresh_field('customer_purchase_order')
           
    },
    company:function(frm) {
        if (frm.doc.pickup_price_list){
            frm.set_value("pickup_price_list","")
        }
    }
});

frappe.ui.form.on('Customer Purchase Order Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    fieldname: ['disabled', 'item_name'],
                    filters: { 'name': row.item_code }
                },
                callback: function(response) {
                    if (response.message && response.message.disabled) {
                        frappe.msgprint({
                            title: __('Item Disabled'),
                            indicator: 'red',
                            message: __('The item "{0}" is disabled.', [response.message.item_name])
                        });
                        // Optionally clear the item_code field if the item is disabled
                        frappe.model.set_value(cdt, cdn, 'item_code', null);
                    }
                }
            });
        }
    }
});


frappe.ui.form.on('Customer Purchase Order', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 2) { 
            frm.remove_custom_button('Reschedule Pickup');
            frm.remove_custom_button('Schedule Pickup');
        }
    },
    // refresh: function(frm) {
    //     if (frm.doc.docstatus === 1) { 
    //         frm.remove_custom_button('Reschedule Pickup');
    //         frm.remove_custom_button('Schedule Pickup');
    //     }
    // },
    supplier: function (frm) {
        // Ensure the 'customer' field is set before selecting a supplier
        if (!frm.doc.customer) {
            console.log("supplier")
            frappe.msgprint(__("Please select a customer first before choosing a supplier."));
            // frm.set_value("supplier", " ")
            frm.doc.supplier=undefined
            refresh_field("supplier")
            
        }
    },     
});





















// frappe.ui.form.on("Customer Purchase Order", {

//     onload: function(frm) {
//         frm.set_query("customer", function() {
//             return {
//                 filters: {
//                     "custom_is_customer": 1
//                 }
//             };
//         });

//         frm.set_query("customer_name", function() {
//             return {
//                 filters: {
//                     "link_doctype": 'Company',
//                     "link_name": frm.doc.company
//                 }
//             };
//         });
//     },

//     customer: function(frm) {
//         // Fetch and set query for pickup price list based on selected customer
//         frm.set_query("pickup_price_list", function() {
//             return {
//                 filters: {
//                     "customer": frm.doc.customer
//                 }
//             };
//         });
//     }

// });