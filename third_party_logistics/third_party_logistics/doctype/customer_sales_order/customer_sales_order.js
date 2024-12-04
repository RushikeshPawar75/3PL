// Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Sales Order", {
	onload: function(frm) {
		frm.set_query("shipping_price_list", function() {
            return {
                filters: {
                    "customer":frm.doc.customer
                }
            }
        });
        frm.set_query('warehouse', 'items', function(doc, cdt, cdn) {
			let row  = locals[cdt][cdn];
			let query = {
				filters: [
					["Warehouse", "company", "in", ["", cstr(frm.doc.company)]],
				]
			};
			if (row.item_code) {
				query.query = "erpnext.controllers.queries.warehouse_query";
				query.filters.push(["Bin", "item_code", "=", row.item_code]);
			}
			return query;
		});
    },
    date: function(frm){
        if (frm.doc.date)
        {
            if (frm.doc.date < get_today()) {
                frappe.msgprint(__("You can not select past date in Date"));
                frm.doc.date = "";
                refresh_field('date');
            }
        }
    },
	refresh: function(frm) {
        if (frm.doc.docstatus == 1 && frm.doc.status == 'Delivery To Be Scheduled')
        {
            frm.add_custom_button(__('Close'),function(){
                frappe.call({
                    method:"update_close_status",
                    doc:frm.doc,
                    callback:function(r)
                    {
                        window.location.reload()   
                    }
                });
            },__('Status'));
        }
        if (frm.doc.status == 'Closed')
        {
            frm.add_custom_button(__('Re-Open'),function(){
                frappe.call({
                    method:"update_reopen_status",
                    doc:frm.doc,
                    callback:function(r)
                    {
                        window.location.reload()   
                    }
                });
            },__('Status'));
        }
        if (frm.doc.status === "Delivery To Be Scheduled" || frm.doc.status === "Delivery Scheduled")
        {
            if (frm.doc.docstatus === 1 && frm.doc.per_picked != 100)
            {
                frm.add_custom_button(__('Pick List'),function(){
                    frappe.model.open_mapped_doc({
                        method:"third_party_logistics.third_party_logistics.doctype.customer_sales_order.customer_sales_order.create_pick_list",
                        frm:frm,
                    })
                },__('Create'));
            }
        }
		if (frm.doc.status === "Delivery To Be Scheduled" && frm.doc.docstatus === 1) 
        {
            frm.add_custom_button(__('Schedule Delivery'), function() {
                check_and_set_availability(frm);    
            }).addClass("btn-primary");
        }
        else if(frm.doc.status == "Delivery Scheduled" || frm.doc.status == "Delivery Overdue")
        {
			frm.add_custom_button(__('Reschedule Delivery'), function() {
				check_and_set_availability(frm);
			}).addClass("btn-primary");
        }
		let check_and_set_availability = function(frm) {
            let selected_slot = null;
            let scheduled_duration = null;
            show_availability();
            function show_availability() {  
                let selected_pickup_team = '';
                let d = new frappe.ui.Dialog({
                    title: __('Schedule Delivery'),
                    fields: [
                        { fieldtype: 'Link', options: 'Employee Group', reqd: 1, fieldname: 'pickup_team', label: 'Delivery Team' },
                        { fieldtype: 'Column Break' },
                        { fieldtype: 'Int', reqd: 1, fieldname: 'scheduled_duration', label: 'Duration (In Mins)', 'default': frm.doc.delivery_duration },
                        { fieldtype: 'Date', reqd: 1, fieldname: 'del_date', label: 'Delivery Date', 'default': frm.doc.delivery_date },
                        { fieldtype: 'Section Break' },
                        { fieldtype: 'HTML', fieldname: 'available_slots' }
                    ],
                    primary_action_label: __('Book'),
                    primary_action: function(values) {
                        frappe.call({
                            method:"update_record",
                            doc:frm.doc,
                            args:{
                                status:"Delivery Scheduled",
                                date: values.del_date,
                                time: selected_slot,
                                scheduled_duration: values.scheduled_duration,
                                pickup_team: values.pickup_team,
                            },
                            callback:function(r)
							{
                                frm.refresh_field("scheduled_time")
                                frm.refresh_field("scheduled_date")
                                frm.refresh_field("scheduled_duration")
                                frm.refresh_field("pickup_team")
                                frm.refresh_field("status")
                                frm.refresh_field("delivery_date")
                                frm.refresh_field("items")
								window.location.reload()   
                            }
                        });
                        d.hide();
                    }
                });

                let fd = d.fields_dict;
                d.fields_dict['del_date'].df.onchange = () => {
                    show_slots(d, fd);
                };
                d.fields_dict['pickup_team'].df.onchange = () => {
                    if (d.get_value('pickup_team') && d.get_value('pickup_team') != selected_pickup_team) {
                        selected_pickup_team = d.get_value('pickup_team');
                        show_slots(d, fd);
                    };
                d.fields_dict['pickup_team'].df.onchange = () => {
					if (d.get_value('pickup_team') && d.get_value('pickup_team') != selected_pickup_team) 
						{
						frappe.db.get_doc("Employee Group",d.get_value('pickup_team')).then(eg => {
							if(eg.schedule)
							{
								frappe.db.get_doc("Schedule",eg.schedule).then(sch => {
									if(sch.scheduled_duration)
									{
										d.set_value("scheduled_duration",sch.scheduled_duration)
                                    }})
                            }})
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
                            method: 'third_party_logistics.third_party_logistics.doctype.customer_sales_order.customer_sales_order.get_availability_data',
                            args:
							{
								req_date: d.get_value('del_date'),
                                emp_grp: d.get_value('pickup_team')
                            },
                            callback: (r) => {
                                let data = r.message;
                                if (data.slot_details.length > 0) {
                                    let $wrapper = d.fields_dict.available_slots.$wrapper;
                                    // make buttons for each slot
                                    let slot_html = get_slots(data.slot_details, d.get_value('del_date'));
                
                                    $wrapper.css('margin-bottom', 0).addClass('text-center').html(slot_html);
                
                                    // highlight button when clicked
                                    $wrapper.on('click', 'button', function() {
                                        let $btn = $(this);
                                        $wrapper.find('button').removeClass('btn-outline-primary');
                                        $btn.addClass('btn-outline-primary');
                                        selected_slot = $btn.attr('data-name');
                                        // service_unit = $btn.attr('data-service-unit');
                                        duration = $btn.attr('data-duration');
                                        
                                            d.$wrapper.find(".opt-out-conf-div").hide();
                                        // }
                
                                        // enable primary action 'Book'
                                        d.get_primary_btn().attr('disabled', null);
                                    });
                
                                } else {
                                    console.log("--------------------empty state")
                                    //	fd.available_slots.html('Please select a valid date.'.bold())
                                    show_empty_state(d.get_value('pickup_team'), d.get_value('del_date'));
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
                            if((now.format("YYYY-MM-DD") == appointment_date) && slot_start_time.isBefore(now))
							{
                                disabled = true;
                            } else 
							{
                                // iterate in all booked appointments, update the start time and duration
                                slot_info.appointments.forEach((booked) => {
                                    let booked_moment = moment(booked.scheduled_time, 'HH:mm:ss');
                                    let end_time = booked_moment.clone().add(booked.duration, 'minutes');
                
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
                
                        if (slot_info.service_unit_capacity) 
						{
                            slot_html += `<br/><small>${__('Each slot indicates the capacity currently available for booking')}</small>`;
                        }
                        slot_html += `<br/><br/>`;
                    });
                
                    return slot_html;
                }
            }
        };

	},
	delivery_date: function(frm) {
		$.each(frm.doc.items || [], function(i, d) {
			if(!d.delivery_date) d.delivery_date = frm.doc.delivery_date;
		});
		refresh_field("items");
        if (frm.doc.delivery_date)
        {
            if (frm.doc.delivery_date < get_today()) {
                frappe.msgprint(__("You can not select past date in Delivery Date"));
                frm.doc.delivery_date = "";
                refresh_field('delivery_date');
            }
        }
	},
	customer_address: function(frm){
		if (frm.doc.customer_address) {
			frappe.call({
				method: 'frappe.contacts.doctype.address.address.get_address_display',
				args: {
					"address_dict": frm.doc.customer_address
				},
				callback: function(r) {
					frm.set_value("address_display", r.message);
				}
			});
		}
		if (!frm.doc.customer_name) {
			frm.set_value("address_display", "");
		}
	},
	// customer_address: function(frm){
	// 	if (frm.doc.customer_address) {
	// 		frappe.call({
	// 			method: 'frappe.contacts.doctype.address.address.get_address_display',
	// 			args: {
	// 				"address_dict": frm.doc.customer_address
	// 			},
	// 			callback: function(r) {
	// 				frm.set_value("address_display1", r.message);
	// 			}
	// 		});
	// 	}
	// 	if (!frm.doc.customer_address) {
	// 		frm.set_value("address_display1", "");
	// 	}
	// }
});
frappe.ui.form.on("Customer Sales Order Item", {
	item_code: function(frm,cdt,cdn) {
		var row = locals[cdt][cdn];
		if (frm.doc.delivery_date) {
			row.delivery_date = frm.doc.delivery_date;
			refresh_field("delivery_date", cdn, "items");
		} else {
			frm.script_manager.copy_from_first_row("items", row, ["delivery_date"]);
		}
        // Fetch the selected item details
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Item',
                'filters': {
                    'name': row.item_code
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
	delivery_date: function(frm, cdt, cdn) {
		if(!frm.doc.delivery_date) {
			erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "items", "delivery_date");
		}
	},
	uom: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		if (row.item_code) {
			frm.call({
			  method: "erpnext.stock.get_item_details.get_conversion_factor",
			  args: {
				item_code: row.item_code,
				uom: row.uom
			  },
			  callback: function(r) {
				if (!r.exc) {
					var row = locals[cdt][cdn];
					frappe.model.set_value(cdt, cdn, "conversion_factor", r.message.conversion_factor);
					var stq_value = r.message.conversion_factor * row.qty
					frappe.model.set_value(cdt, cdn, "stock_qty", stq_value);
					if (row.stock_qty && row.weight_per_unit)
					{
						var stqty_total_weight = row.stock_qty * row.weight_per_unit
						frappe.model.set_value(cdt, cdn, "total_weight", stqty_total_weight);
					}
					else
					{
						if(row.qty)
						{
							var total_weight = row.qty * row.weight_per_unit
							frappe.model.set_value(cdt, cdn, "total_weight", total_weight);
						}
					}
				}
			  }
			});
		  }
	},
	qty: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		if (row.rate && row.qty)
		{
			var total_amt = row.rate * row.qty
			frappe.model.set_value(cdt, cdn, "amount", total_amt);
		}
		// if (row.qty && row.weight_per_unit)
		// {
		// 	if (row.stock_qty)
		// 	{
		// 		var stoqty_total_weight = row.stock_qty * row.weight_per_unit
		// 		frappe.model.set_value(cdt, cdn, "total_weight", stoqty_total_weight);
		// 	}
			
		// 	// {
		// 	// 	var total_weight = row.qty * row.weight_per_unit
		// 	// 	frappe.model.set_value(cdt, cdn, "total_weight", total_weight);
		// 	// }
		// }
		if (row.qty && row.conversion_factor)
		{
			var total_stock_qty = row.qty * row.conversion_factor
			frappe.model.set_value(cdt, cdn, "stock_qty", total_stock_qty);
			if (row.stock_qty && row.weight_per_unit)
			{
				var stoqty_total_weight = row.stock_qty * row.weight_per_unit
				frappe.model.set_value(cdt, cdn, "total_weight", stoqty_total_weight);
			}
		}
	},
	rate: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		if (row.rate && row.qty)
		{
			var total_amt = row.rate * row.qty
			frappe.model.set_value(cdt, cdn, "amount", total_amt);
		}
	}
});

