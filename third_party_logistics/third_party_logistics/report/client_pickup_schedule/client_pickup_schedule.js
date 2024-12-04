// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Client Pickup Schedule"] = {
	"filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_default("company")
        },
        {
            "fieldname": "client",
            "label": __("Client"),
            "fieldtype": "Link",
            "options": "Customer",
            "depends_on": "eval: doc.based_on == 'Client'",
        },
        {
            "fieldname": "pickup_team",
            "label": __("Pickup Team"),
            "fieldtype": "Link",
            "options": "Employee Group",
            "depends_on": "eval: doc.based_on == 'Pickup_team'",
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start()
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_end()
        },
        {
            "fieldname": "based_on",
            "label": __("Based on"),
            "fieldtype": "Select",
            "options":[
				{ "value": "Client", "label": __("Client") },
				{ "value": "Pickup_team", "label": __("Pickup Team") },
			],
            "default": "Client"
        },
        {
			"fieldname":"range",
			"label": __("Period"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Weekly", "label": __("Weekly") },
				{ "value": "Monthly", "label": __("Monthly") },
				{ "value": "Quarterly", "label": __("Quarterly") },
				{ "value": "Yearly", "label": __("Yearly") }
			],
			"default": "Weekly"
		},
    ],
onload: function(report) {
	report.refresh();
},
onchange: function(report) {
	report.refresh();
},
};