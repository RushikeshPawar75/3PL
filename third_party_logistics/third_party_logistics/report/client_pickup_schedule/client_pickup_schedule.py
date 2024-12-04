# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt


import frappe
import datetime
import calendar 
from frappe import _
from datetime import timedelta , datetime
from frappe.utils import getdate,add_months
from frappe.utils.data import flt
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


def execute(filters=None):
    columns = get_columns(filters)
    data = []
    if filters.get("range") =="Monthly":
        data = get_data_monthly(filters)
    if filters.get("range") == "Yearly":
        data = get_data_yearly(filters)
    if filters.get("range") == "Weekly":
        data = get_data_weekly(filters)
    if filters.get("range") == "Quarterly":
        data = get_data_quarterly(filters)
    return columns, data 

def get_columns(filters):
    columns = []
    quarter_end_dates = get_all_dates(filters.get("from_date"), filters.get("to_date"), "quarterly")
    based_on = filters.get("based_on")
    period = filters.get("range")
    status_list = ["Scheduled", "Completed", "Pickup Overdue"]
    if based_on == "Client":
        columns.append({
            "label": "Client",
            "fieldname": "identifier",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150,
            
        })
    if based_on == "Pickup_team":
        columns.append({
            "label": "Pickup_team",
            "fieldname": "identifier",
            "fieldtype": "Link",
            "options": "Employee Group",
            "width": 150,
            
        })

    all_dates = get_all_dates(filters.get("from_date"),filters.get("to_date"),"monthly")
    all_weeks = get_all_dates(filters.get("from_date"), filters.get("to_date"), "weekly")
    all_years = get_all_dates(filters.get("from_date"),filters.get("to_date"),"yearly")
    
    if period == "Monthly":
        for date in all_dates:
            column_label = date.strftime('%B %Y')
            columns.append({
                "label": f"{column_label} (Scheduled)",
                "fieldname": f"{column_label}_scheduled",
                "fieldtype": "Int",
                "width": 120
            })
            columns.append({
                "label": f"{column_label} (Pickup Overdue)",
                "fieldname": f"{column_label}_pickup_overdue",
                "fieldtype": "Int",
                "width": 120
            })
            columns.append({
                "label": f"{column_label} (Completed)",
                "fieldname": f"{column_label}_completed",
                "fieldtype": "Int",
                "width": 120
            })
    if period == "Yearly":
        for year in all_years:
            column_label = str(year)
            for status in status_list:
                columns.append({
                    "label": f"{column_label} ({status})",
                    "fieldname": f"{year}_{status.lower().replace(' ', '_')}",
                    "fieldtype": "Int",
                    "width": 120
                })
    if period == "Quarterly":
        for quarter_end_date in get_all_dates(filters.get("from_date"), filters.get("to_date"), "quarterly"):
            quarter = (quarter_end_date.month - 1) // 3 + 1
            year = quarter_end_date.year
            quarter_label = f"Q{quarter} {year}"
            for status in status_list:
                columns.append({
                    "label": f"{quarter_label} ({status})",
                    "fieldname": f"{quarter_label.lower().replace(' ', '_')}_{status.lower().replace(' ', '_')}",
                    "fieldtype": "Int",
                    "width": 120
                })
                print("columns:--------->",columns)
    for start_date, end_date in all_weeks:
        if period == "Weekly":
            week_label = f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}"
            for status in status_list:
                columns.append({
                    "label": f"{week_label} ({status})",
                    "fieldname": f"{week_label.replace(' ', '_')} {status.lower().replace(' ', '_')}",
                    "fieldtype": "Int",
                    "width": 120
                })
                print("columns:--------->",columns)
    return columns

def get_all_dates(from_date, to_date, frequency):
    if frequency == "monthly":
        all_dates = []

        current_date = getdate(from_date)
        end_date = getdate(to_date)
        while current_date <= end_date:
            all_dates.append(current_date)
            last_day_of_month = calendar.monthrange(current_date.year, current_date.month)[1]
            last_date_of_month = current_date.replace(day=last_day_of_month)
            # print("Last day of", current_date.strftime("%B %Y"), ":", last_date_of_month)
            current_date = add_months(current_date, 1)
        return all_dates

    if frequency == "yearly":
        all_years = []
        current_year = getdate(from_date).year
        end_year = getdate(to_date).year
        while current_year <= end_year:
            all_years.append(current_year)
            current_year += 1
        return all_years
    
    if frequency == "weekly":
        all_weeks = []
        current_date = getdate(from_date)
        end_date = getdate(to_date)

        while current_date <= end_date:
            week_start = current_date
            week_end = current_date + timedelta(days=6)
            all_weeks.append((week_start, week_end))
            current_date = current_date + timedelta(days=7)
        
        return all_weeks
    elif frequency == "quarterly":
        quarter_end_dates = []
        current_date = getdate(from_date)

        while current_date <= getdate(to_date):
            year = current_date.year
            quarter = (current_date.month - 1) // 3 + 1
            next_quarter_month = (quarter - 1) * 3 + 1
            quarter_end = datetime(year, next_quarter_month, 1) - timedelta(days=1)
            
            if quarter_end <= datetime.combine(getdate(to_date), datetime.min.time()):
                quarter_end_dates.append(quarter_end)

            current_date = add_months(current_date, 3)
        
        return quarter_end_dates
    

def get_conditions(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " AND po.company ='{}'".format(filters.get('company'))
    if filters.get("client"):
        conditions += " AND po.client = '{}'".format(filters.get('client'))
    if filters.get("pickup_team"):
        conditions += " AND po.pickup_team = '{}'".format(filters.get('pickup_team'))
    return conditions

def get_data_monthly(filters):
    based_on = filters.get("based_on")
    conditions = get_conditions(filters)

    all_dates = get_all_dates(filters.get("from_date"), filters.get("to_date"), "monthly")
    
    
    data_dict = {}  # Use a dictionary to organize data
    for date in all_dates:
        last_day_of_month = calendar.monthrange(date.year, date.month)[1]
        end_date_of_month = date.replace(day=last_day_of_month)
        client_purchase_order = frappe.db.sql("""
            SELECT {based_on} as identifier, count(po.name) as po_count , DATE_FORMAT(po.transaction_date, '%Y-%m') as month_year ,
            COUNT(CASE WHEN po.status = 'Scheduled' THEN 1 END) AS scheduled,
            COUNT(CASE WHEN po.status = 'Pickup Overdue' THEN 1 END) AS pickup_overdue,
            COUNT(CASE WHEN po.status = 'Completed' THEN 1 END) AS completed
            FROM `tabClient Purchase Order` as po
            WHERE po.docstatus = 1 {conditions}
            AND po.transaction_date BETWEEN "{0}" AND "{1}"
            GROUP BY {based_on} , month_year
        """.format(date, end_date_of_month, based_on=based_on, conditions=conditions), as_dict=True)

        print("CPOOOOOOOOOOOOOOOOOOOO",client_purchase_order)
        
        for cpo in client_purchase_order:
            identifier = cpo.identifier
            # po_count = cpo.get("po_count")
            scheduled = cpo.get("scheduled")
            Pickup_overdue = cpo.get("pickup_overdue")
            completed = cpo.get("completed")
            print("SCHEDULED:-------->",scheduled)
            print("Pickup_overdue:-------->",Pickup_overdue)
            print("Completed:-------->",cpo.get("completed"))

            column_label = f"{date.strftime('%B %Y')}"
            print("COLUMN_LABEL:----",column_label)
            
            if identifier not in data_dict:
                data_dict[identifier] = {"identifier": identifier}
            
            data_dict[identifier][f"{column_label}_scheduled"] = scheduled
            data_dict[identifier][f"{column_label}_pickup_overdue"] = Pickup_overdue
            data_dict[identifier][f"{column_label}_completed"] = completed
    
    data = list(data_dict.values())  # Convert the dictionary values to a list
    print("DATA:----------------->>>>>>",data)
    return data

def get_data_yearly(filters):
    based_on = filters.get("based_on")
    conditions = get_conditions(filters)

    all_years = get_all_dates(filters.get("from_date"), filters.get("to_date"), "yearly")
    
    data_dict = {}  # Use a dictionary to organize data
    for year in all_years:
        client_purchase_order = frappe.db.sql("""
            SELECT {based_on} as identifier, count(po.name) as po_count , DATE_FORMAT(po.transaction_date, '%Y') as year ,
            COUNT(CASE WHEN po.status = 'Scheduled' THEN 1 END) AS scheduled,
            COUNT(CASE WHEN po.status = 'Pickup Overdue' THEN 1 END) AS pickup_overdue,
            COUNT(CASE WHEN po.status = 'Completed' THEN 1 END) AS completed
            FROM `tabClient Purchase Order` as po
            WHERE po.docstatus = 1 {conditions}
            AND po.transaction_date BETWEEN "{0}-01-01" AND "{1}-12-31"
            GROUP BY {based_on} , year
        """.format(year, year, based_on=based_on, conditions=conditions), as_dict=True)

        for cpo in client_purchase_order:
            identifier = cpo.identifier
            scheduled = cpo.get("scheduled")
            pickup_overdue = cpo.get("pickup_overdue")
            completed = cpo.get("completed")
            column_label = str(year)
            
            if identifier not in data_dict:
                data_dict[identifier] = {"identifier": identifier}
            
            data_dict[identifier][f"{column_label}_scheduled"] = scheduled
            data_dict[identifier][f"{column_label}_pickup_overdue"] = pickup_overdue
            data_dict[identifier][f"{column_label}_completed"] = completed
    
    data = list(data_dict.values())  # Convert the dictionary values to a list
    return data

def get_data_weekly(filters):
    based_on = filters.get("based_on")
    conditions = get_conditions(filters)

    all_dates = get_all_dates(filters.get("from_date"), filters.get("to_date"), "weekly")

    data_dict = {}  # Use a dictionary to organize data
    for start_date, end_date in all_dates:
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        client_purchase_order = frappe.db.sql("""
            SELECT {based_on} as identifier, count(po.name) as po_count,
            COUNT(CASE WHEN po.status = 'Scheduled' THEN 1 END) AS scheduled,
            COUNT(CASE WHEN po.status = 'Pickup Overdue' THEN 1 END) AS pickup_overdue,
            COUNT(CASE WHEN po.status = 'Completed' THEN 1 END) AS completed
            FROM `tabClient Purchase Order` as po
            WHERE po.docstatus = 1 {conditions}
            AND po.transaction_date BETWEEN "{0}" AND "{1}"
            GROUP BY {based_on}
        """.format(start_date_str, end_date_str, based_on=based_on, conditions=conditions), as_dict=True)
        
        for cpo in client_purchase_order:
            identifier = cpo.get("identifier")
            scheduled = cpo.get("scheduled")
            pickup_overdue = cpo.get("pickup_overdue")
            completed = cpo.get("completed")
            print("identifier",identifier)
            print("SCHEDULED:-------->",scheduled)
            print("Pickup_overdue:-------->",pickup_overdue)
            print("Completed:-------->",completed) 

            if identifier not in data_dict:
                data_dict[identifier] = {"identifier": identifier}

            week_label = f"{start_date.strftime('%Y-%m-%d')}_-_{end_date.strftime('%Y-%m-%d')}"
            data_dict[identifier][f"{week_label} scheduled"] = scheduled
            data_dict[identifier][f"{week_label} pickup Overdue"] = pickup_overdue
            data_dict[identifier][f"{week_label} completed"] = completed
            print("Data_dict:-------->",data_dict)

    
    data = list(data_dict.values())
    print("data:--------------->",data)  # Convert the dictionary values to a list
    return data
def get_data_quarterly(filters):
    based_on = filters.get("based_on")
    conditions = get_conditions(filters)

    quarter_end_dates = get_all_dates(filters.get("from_date"), filters.get("to_date"), "quarterly")
    
    data_dict = {}
    for quarter_end_date in quarter_end_dates:
        year = quarter_end_date.year
        quarter = (quarter_end_date.month - 1) // 3 + 1
        quarter_start_date = datetime(year, (quarter - 1) * 3 + 1, 1)
        print("eeeeeeeeeeeeeeeeeeeeeeeee", quarter)
        print("yyyyyyyyyyyyyyyyyyy",quarter_start_date)
        print("wwwwwwwwwwwwwwwwww",quarter_end_date)
        end_date_of_quarter = quarter_end_date
        quarter_label = quarter_end_date.strftime(f"Q{quarter} {year}")
        
        client_purchase_order = frappe.db.sql("""
            SELECT {based_on} as identifier, count(po.name) as po_count, 
            COUNT(CASE WHEN po.status = 'Scheduled' THEN 1 END) AS scheduled,
            COUNT(CASE WHEN po.status = 'Pickup Overdue' THEN 1 END) AS pickup_overdue,
            COUNT(CASE WHEN po.status = 'Completed' THEN 1 END) AS completed
            FROM `tabClient Purchase Order` as po
            WHERE po.docstatus = 1 {conditions}
            AND po.transaction_date BETWEEN "{0}" AND "{1}"
            GROUP BY {based_on}
        """.format(quarter_start_date, end_date_of_quarter, based_on=based_on, conditions=conditions), as_dict=True)
        
        for cpo in client_purchase_order:
            identifier = cpo.identifier
            scheduled = cpo.get("scheduled")
            pickup_overdue = cpo.get("pickup_overdue")
            completed = cpo.get("completed")

            if identifier not in data_dict:
                data_dict[identifier] = {"identifier": identifier}
            
            data_dict[identifier][f"{quarter_label.lower().replace(' ', '_')}_scheduled"] = scheduled
            data_dict[identifier][f"{quarter_label.lower().replace(' ', '_')}_pickup_overdue"] = pickup_overdue
            data_dict[identifier][f"{quarter_label.lower().replace(' ', '_')}_completed"] = completed
            print("DATA_DICT:------->",data_dict)
    
    data = list(data_dict.values())
    return data
