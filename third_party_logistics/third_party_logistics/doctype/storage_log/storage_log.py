import frappe
from datetime import date
import traceback
from frappe import db
from frappe.model.document import Document
from frappe.utils import get_datetime , getdate

class StorageLog(Document):
	pass
    # def before_save(self):
    #     self.fetch_serial_no()

def fetch_serial_no(tdate=None):
    snos = frappe.db.sql(""" SELECT  sle.serial_no,
                                        sle.batch_no,
                                        sle.stock_uom,
                                        sle.company,
                                        sle.actual_qty,
                                        sle.posting_date,
                                        sle.warehouse,
                                        sle.item_code,
                                        sle.is_cancelled,
                                        sle.voucher_no,
                                        se_detail.item_code AS se_item_code,
                                        se_detail.uom AS se_uom,
                                        se.custom_customer_purchase_order AS customer_purchase_order,
                                        se_detail.serial_and_batch_bundle AS serial_batch_bundle,
                                        se.custom_customer As custom_customer,
                                        cpo.total_net_volume AS total_volume,
                                        ci.volume_per_unit AS unit_volume
                                FROM
                                    `tabStock Ledger Entry` AS sle
                                JOIN
                                    `tabStock Entry` AS se ON sle.voucher_no = se.name
                                JOIN
                                    `tabStock Entry Detail` AS se_detail ON se.name = se_detail.parent
                                LEFT JOIN
                                    `tabCustomer Purchase Order` AS cpo ON se.custom_customer_purchase_order = cpo.name
                                LEFT JOIN
                                    `tabCustomer Purchase Order Item` AS ci ON cpo.name = ci.parent 
                                WHERE
                                    sle.is_cancelled = 0
                         
                                """,as_dict=1)
    print("--------------------------------------------------sno",snos)
    if snos:
        return snos


@frappe.whitelist()
def create_slogs(tdate=None):
    print('Calling API--------------------------')
    tdate = tdate or get_datetime()
    sno = fetch_serial_no(tdate)
    
    if sno:
        for i in sno:
            serial_nos = i.get("serial_no")
            bundle_id = i.get("serial_batch_bundle")
            batch_nos = i.get("batch_no")

            if bundle_id:
                print("Processing Serial Batch Bundle ID:", bundle_id)
                serial_batch_data = frappe.db.sql("""
                    SELECT entry.serial_no, entry.batch_no
                    FROM `tabSerial and Batch Bundle` AS bundle
                    JOIN `tabSerial and Batch Entry` AS entry ON bundle.name = entry.parent
                    WHERE bundle.name = %s
                """, (bundle_id), as_dict=True)

                for entry in serial_batch_data:
                    print("*****entry creating for bundle ****")
                    create_or_skip_storage_log(entry, i)

            elif serial_nos and isinstance(serial_nos, str):
                for serial_no in serial_nos.split('\n'):
                    if serial_no:
                        create_or_skip_storage_log({"serial_no": serial_no, "batch_no": i.get("batch_no")}, i)

            elif batch_nos and isinstance(batch_nos, str):
                for batch_no in batch_nos.split('\n'):
                    if batch_no:
                        create_or_skip_storage_log({"serial_no": i.get("serial_no"), "batch_no": batch_no}, i)
            

def create_or_skip_storage_log(entry, i):
    print("*****isndie bundle*******")
    print("***entry**",entry)
    serial_no = entry.get('serial_no') or ""
    batch_no = entry.get('batch_no') or ""

    # Check if the storage log already exists
    slog = frappe.db.exists("Storage Log", {
        "serial_no": serial_no,
        "date": i.get("posting_date"),
        "batch_no": batch_no,
        "item": i.get("item_code"),
        "customer": i.get("custom_customer"),
        "company": i.get("company"),
        "warehouse": i.get("warehouse"),
        "qty": i.get('actual_qty')
    })

    if slog:
        print(f"Storage Log already exists for Serial No: {serial_no} and Batch No: {batch_no}")
        return  # Skip to next iteration if log exists

    # Create new storage log
    print(f"Creating new Storage Log for Serial No: {serial_no} and Batch No: {batch_no}")
    nslog = frappe.new_doc("Storage Log")
    nslog.item = i.get("item_code")
    nslog.company = i.get("company")
    nslog.warehouse = i.get("warehouse")
    nslog.qty = i.get("actual_qty")
    nslog.date = i.get("posting_date")
    
    nslog.has_serial_no = 1 if serial_no else 0
    nslog.serial_no = serial_no
    nslog.has_batch_no = 1 if batch_no else 0
    nslog.batch_no = batch_no

    nslog.uom = i.get("stock_uom")
    nslog.customer = i.get("custom_customer")
    nslog.total_volume = i.get("total_volume")
    nslog.unit_volume = i.get("unit_volume")

    try:
        nslog.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Storage Log created successfully for Serial No: {serial_no} and Batch No: {batch_no}")
    except Exception as e:
        frappe.db.rollback()
        print(f"Error creating Storage Log: {str(e)}")
        print(traceback.format_exc())

















    # snos = frappe.db.sql("""<
    #     SELECT   
    #         sle.serial_no,
    #         sle.batch_no,
    #         sle.stock_uom,
    #         sle.company,
    #         sle.actual_qty,
    #         sle.posting_date,
    #         sle.warehouse,
    #         sle.item_code,                  
    #         sle.is_cancelled,
    #         sle.voucher_no,
    #         se_detail.item_code AS se_item_code,
    #         se_detail.uom AS se_uom,
    #         se_detail.custom_customer_purchase_order AS custom_customer_purchase_order,
    #         se_detail.serial_and_batch_bundle AS serial_batch_bundle,
    #         cpo.customer AS customer,
    #         cpo.total_net_volume AS total_volume,
    #         ci.volume_per_u': None, 'batch_no': None,nit AS unit_volume
    #     FROM
    #         `tabStock Ledger Entry` AS sle
    #     JOIN
    #         `tabStock Entry` AS se ON sle.voucher_no = se.name
    #     LEFT JOIN
    #         `tabStock Entry Detail` AS se_detail ON se.name = se_detail.parent
    #     LEFT JOIN
    #         `tabCustomer Purchase Order` AS cpo ON se_detail.custom_customer_purchase_order = cpo.name
    #     LEFT JOIN
    #         `tabCustomer Purchase Order Item` AS ci ON cpo.name = ci.parent
    #     WHERE
    #         sle.is_cancelled = 0
    #     AND sle.posting_date = %s
    # """, (tdate), as_dict=True)
 
# @frappe.whitelist()
# def create_slogs(tdate=None):
#     print('calling API--------------------------')
#     if not tdate:
#         tdate = get_datetime()
#         print('******tdate****',tdate)
#     sno = fetch_serial_no(tdate)
#     print('sno----------',sno)
#     if sno:
#         for i in sno:
#             serial_nos = i.get("serial_no")
#             bundle_id = i.get("serial_batch_bundle")

#             if bundle_id:
#                 print("Serial Batch Bundle ID:", bundle_id)
#                 bundle_doc = frappe.get_doc("Serial and Batch Bundle",bundle_id)
#                 print('******bundle_doc*****',bundle_doc)
#                 serial_batch_data = frappe.db.sql("""
#                         SELECT
#                             entry.serial_no,
#                             entry.batch_no
#                         FROM
#                             `tabSerial and Batch Bundle` AS bundle
#                         JOIN
#                             `tabSerial and Batch Entry` AS entry
#                         ON
#                             bundle.name = entry.parent
#                         WHERE
#                             bundle.name = %s
#                     """, (bundle_id), as_dict=True)
#                 print('******serial_batch*****',serial_batch_data)
#                 for entry in serial_batch_data:
#                     serial_no = entry.get('serial_no')
#                     batch_no = entry.get('batch_no')

#                     if serial_no or batch_no:
#                         print("********inside id of create slogs***********",serial_no, getdate(tdate), i.get("batch_no"),i.get("item_code"),i.get("custom_customer"),i.get("company"),i.get("warehouse"),
#                                i.get('qty'))
#                         print("**Iiiiiii***",i)
#                         # print(f"""
#                         #     SELECT name FROM `tabStorage Log` WHERE
#                         #     serial_no = "{serial_no}"
#                         #     AND date = "{i.get("posting_date")}"
#                         #     AND batch_no = "{i.get("batch_no")}"
#                         #     AND item = "{i.get("item_code")}"
#                         #     AND customer = "{i.get("custom_customer")}"
#                         #     AND company = "{i.get("company")}"
#                         #     AND warehouse = "{i.get("warehouse")}"
#                         #     AND qty = "{i.get('actual_qty')}"
#                         # """)
#                         # slog = db.sql("""
#                         #     SELECT name FROM `tabStorage Log` WHERE
#                         #     serial_no = %s
#                         #     AND date = %s
#                         #     AND batch_no = %s
#                         #     AND item = %s
#                         #     AND customer = %s
#                         #     AND company = %s
#                         #     AND warehouse = %s
#                         #     AND qty = %s
#                         # """, (serial_no, i.get("posting_date"), i.get("batch_no"),i.get("item_code"),i.get("custom_customer"),i.get("company"),i.get("warehouse"),
#                         #        i.get('actual_qty')), as_dict=True)
#                         slog = frappe.db.exists("Storage Log",{"serial_no": serial_no,"date" : i.get("posting_date"),"batch_no" : i.get("batch_no"),"item" : i.get("item_code"),"customer": i.get("custom_customer"),"company" : i.get("company"),"warehouse" : i.get("warehouse"),"qty": i.get('actual_qty')})

#                         print("slog",slog)
#                         if slog:
#                             print(f"********Storage Log already present for Serial No: {serial_no} and Batch No: {batch_no}***********")
#                             return
#                         else:
#                             print(f"********Creating new Storage Log for Serial No: {serial_no} and Batch No: {batch_no}***********")
                            
#                             # po = i.get('customer_purchase_order')
#                             # print("****####$$$$$po$$$$",po)
#                             # customer = frappe.get_value("Customer Purchase Order", po, "customer")
#                             # print('******customer###########',customer)

#                             nslog = frappe.new_doc("Storage Log")
#                             nslog.item = i.get("item_code")
#                             nslog.company = i.get("company")
#                             nslog.warehouse = i.get("warehouse")
#                             nslog.qty = i.get("actual_qty")
#                             nslog.date = i.get("posting_date")

#                             if serial_no:
#                                 nslog.has_serial_no = 1
#                                 nslog.serial_no = serial_no
#                             if batch_no:
#                                 nslog.has_batch_no = 1
#                                 nslog.batch_no = batch_no

#                             nslog.uom = i.get("stock_uom")
#                             print("******customer 1111111",i.get("custom_customer"))
#                             nslog.customer = i.get("custom_customer")
#                             nslog.total_volume = i.get("total_volume")
#                             nslog.unit_volume = i.get("unit_volume")
                            
#                             try:
#                                 nslog.insert(ignore_permissions=True)
#                                 frappe.db.commit()
#                                 print(f"********Storage Log Created Successfully for Serial No: {serial_no} and Batch No: {batch_no}***********")
#                             except Exception as e:
#                                 frappe.db.rollback()
#                                 print(f"Error creating Storage Log: {str(e)}")
#                                 print(traceback.format_exc()) 
                        
#             else:
#                 print("###############inside 2nd else")
#                 if serial_nos and isinstance(serial_nos, str):
#                     for serial_no in serial_nos.split('\n'):
#                         if serial_no:
#                             print("********inside id of create slogs***********")
#                             # slog = db.sql("""
#                             #     SELECT name FROM `tabStorage Log` WHERE
#                             #     serial_no = %s
#                             #     AND DATE(date) = %s
#                             #     AND batch_no = %s
#                             #     AND item = %s
#                             #     AND customer = %s
#                             #     AND company = %s
#                             #     AND warehouse = %s
#                             #     AND qty = %s
#                             # """, (serial_no, getdate(tdate), i.get("batch_no"),i.get("item_code"),i.get("customer"),i.get("company"),i.get("warehouse"),
#                             #       i.get('qty')), as_dict=True)
#                             slog = frappe.db.exists("Storage Log",{"serial_no": serial_no,"date" : i.get("posting_date"),"batch_no" : i.get("batch_no"),"item" : i.get("item_code"),"customer": i.get("custom_customer"),"company" : i.get("company"),"warehouse" : i.get("warehouse"),"qty": i.get('actual_qty')})
#                             if slog:
#                                 print("********slogs present already***********")
#                                 return

#                             if not slog:
#                                 print("********slogs not present, inside not slog if statement***********")
#                                 nslog = frappe.new_doc("Storage Log")
#                                 nslog.item = i.get("item_code")
#                                 nslog.company = i.get("company")
#                                 nslog.warehouse = i.get("warehouse")
#                                 nslog.qty = i.get("actual_qty")
#                                 nslog.date = i.get("posting_date")
#                                 if i.get("serial_no"):
#                                     nslog.has_serial_no = 1
#                                     nslog.serial_no = serial_no
#                                 if i.get("batch_no"):
#                                     nslog.has_batch_no = 1
#                                     nslog.batch_no = i.get("batch_no")
#                                 nslog.uom = i.get("stock_uom")  
#                                 nslog.customer = i.get("custom_customer")
#                                 nslog.total_volume = i.get("total_volume")
#                                 nslog.unit_volume = i.get("unit_volume")
#                                 nslog.insert(ignore_permissions=True)
