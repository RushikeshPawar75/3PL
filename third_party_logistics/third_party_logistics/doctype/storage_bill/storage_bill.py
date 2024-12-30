# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import get_datetime
from frappe.utils import today, date_diff

class StorageBill(Document):
	@frappe.whitelist()
	def fetch_logs(self):
		customer = self.customer
		company = self.company
		from_date = self.from_date
		to_date = self.to_date

		if not customer:
			frappe.throw("Please select a Customer before fetching logs.")

		if customer:
			entry = frappe.get_all("Storage Log",
		  				filters = {"customer": customer,"company":company,
				   					"date": ["between", [from_date, to_date]],
				   				},
						  fields = ["*"]
		 					)
			result = []
			for i in entry:
				item = frappe.get_doc("Item",i.item)

				if item:
					description = item.description
					batch = i.batch_no
					serial = i.serial_no
					print("UUUUUUUUUUUUUUUUUUUUUUUU",batch)
					print("UUUUUUUUUUUUUUUUUUUUUUUU",serial)
					
				else:
					description = ""
				
				if i.batch_no:
					stk_entry= frappe.get_value("Batch",i.batch_no,"reference_name")
					print("**stk entry****",stk_entry)
				if i.serial_no:
					stk_entry= frappe.get_value("Serial No",i.serial_no,"purchase_document_no")
					print("**stk entry****",stk_entry)
				else:
					print("***i.customer_purchase_order***", i.customer_purchase_order)
					stock_entry = frappe.db.sql(
						"""SELECT name FROM `tabStock Entry` WHERE custom_customer_purchase_order = %s""",
						(i.customer_purchase_order,), 
						as_dict=True 
					)
					stk_entry = stock_entry[0].get("name")
					print("**stk entry****", stk_entry)


				cust_po = frappe.get_value("Stock Entry",stk_entry,"custom_customer_purchase_order")
				print("***sdfgsdfgsdf****",cust_po)


				stock_entry_details = frappe.get_all("Stock Entry Detail",
                                          filters={"parent": stk_entry},
                                          fields=["uom","qty",'item_code']
                                          )
				print("#########",stock_entry_details)


				stock_uom = ""
				qty_in_stock_uom= ""
				item_code = "" 

				for detail in stock_entry_details:
					if detail:
						stock_uom = detail.get("uom")
						qty_in_stock_uom = detail.get("qty")
						item_code = detail.get("item_code")
						

						# amount = detail.get("amount")
					else:
						print("NO DATA FOUND FROM STOCK ENTRY DETAILS")

				storage_price_list= frappe.get_all('Storage Price List', 
													filters={
															'customer': i.customer,
															'disable': 0,
															'from_date': ['<=', self.from_date],
															'to_date': ['>=', self.to_date]
															}, 
													fields=['*'])
				if not storage_price_list :
					print("storage-------->",storage_price_list)
					frappe.throw("No active Storage Price List found, no Storage Price List, or might be disabled for this Customer.")
				# from_date = ""
				# to_date = ""
				# price_per_unit_volume = ""
				# volume_uom = ""
				print("*********storage price list ******",storage_price_list)
				price_per_day = 0.0

				for spl in storage_price_list:
					if spl:
						# from_date = spl.get("from_date")
						# to_date = spl.get("to_date")
						tab_data = frappe.db.get_all("Storage Prices Table",{"parent":spl.name},['from_area','to_area','price_per_day'])
						print("********tab data*******",tab_data)
						price_per_day = 0.0

						cpor_cur = frappe.get_doc("Customer Purchase Order",cust_po)
						print("*************in cpour_cur***********",cpor_cur)
						if cpor_cur:
							print("*************in cpour_cur***********")
							ttl_area = cpor_cur.total_net_area
							print("*****total area*****",ttl_area)
							no_area=True
							for x in tab_data:
								if x['from_area'] <= ttl_area <= x['to_area']:
									no_area=False
									print("x.from_area"+"<="+" ttl_area"+">= "+"x.to_area",x.from_area,ttl_area,x.to_area)
									print("*************in i.from_area <= ttl_area >= i.to_area***********")
									price_per_day += x['price_per_day']
									print("***********price per day*************",price_per_day)
									print("x---->",x)
									break
							if no_area:
								frappe.throw(f"The toatal area was not matching with price per sqft area in the storage price list {ttl_area}")
									
						volume_uom = spl.get("volume_uom")
						cpo = frappe.get_doc("Customer Purchase Order",cust_po)
						cust=cpo.get("customer")
						comp=cpo.get("company")
						if cpo:
							total_weight = cpo.total_net_weight   
							total_volume = cpo.total_net_volume
							total_area = cpo.total_net_area
							total_amount = cpo.total
							total_quantt = cpo.total_qty


						date = i.date
						# print("**************date************",date)
						current_date = today()
						days_stored = date_diff(current_date, date)
						# print("Item has been stored for {} days.".format(days_stored))

						similar_record_exists = False
						for existing_record in result:
							if (
								existing_record["item"] == i.item
								and existing_record["qty"] == i.qty
								and existing_record["date_stored"] == date.strftime('%Y-%m-%d')
								and existing_record["storage_price_list"] == spl.get("name")
								and existing_record["total_volume"] == total_volume
								and existing_record["total_weight"] == total_weight
								and existing_record["total_area"] == total_area
							):
								similar_record_exists = True
								break


						ppuv = spl.get("price_per_unit_volume")
						ppuw=spl.get("price_per_unit_weight_")
						ppdw=spl.get("price_per_day_weight")
						ppdv = spl.get("price_per_day_volume")

						print("(days_stored,total_amount,total_quantt,total_area,price_per_day",days_stored,total_amount,total_quantt,total_area,price_per_day)
						storage_charges = self.calculate_storage_charges(
							days_stored,total_amount,total_quantt,total_area,price_per_day,ppuv,ppuw,ppdw,ppdv
						)

						print("Storage Chrages Value : ",storage_charges)

						if not similar_record_exists:  
							result.append({
								"item": i.get("item"),
								"customer":cust,
								"company":comp,
								"description": description,
								"date_stored": date.strftime('%Y-%m-%d'),
								"days_stored": days_stored,
								"volume_uom": volume_uom,
								"storage_price_list": spl.get("name"),
								"qty": i.get("qty"),
								"uom": i.get("uom"),
								"stock_uom": stock_uom,
								"qty_in_stock_uom": qty_in_stock_uom,
								"total_weight": total_weight,
								"amount": total_amount,
								"total_volume": total_volume,
								"total_area":total_area,
								"price_per_unit_volume": spl.get("price_per_unit_volume") if spl.get("price_per_unit_volume") else 0,
								"price_per_unit_weight": spl.get("price_per_unit_weight_") if spl.get("price_per_unit_weight_") else 0,
								"price_per_day_weight":spl.get("price_per_day_weight") if spl.get("price_per_day_weight") else 0,
								"price_per_day_volume": spl.get("price_per_day_volume") if spl.get("price_per_day_volume") else 0,
								"storage_charges": storage_charges,
								"price_per_day":price_per_day,
							})
					else:
						print("No Data From SPL")
					# print("Result:----------->", result)
			print("Result:----------->", result)
			return result
				
	@frappe.whitelist()
	def update_items(self):
		print("update items"*70)
		self.set("items", [])
		logs = self.fetch_logs()
		total_storage_charges = 0
		customer = self.customer
		company = self.company
		total_area = 0
		if not logs:
			print("No logs fetched.")
			return 0, 0

		for d in logs:
			print("Appending item:", d)
			# if customer == d.get("customer") and company == d.get("company"):
			self.append('items', {
				"item": d.get("item"),
				"qty": d.get("qty"),
				"uom": d.get("uom"),
				"date_stored": d.get('date_stored'),
				"days_stored": d.get('days_stored'),
				"storage_price_list": d.get("storage_price_list"),
				"item_discription": d.get("description"),
				"stock_uom": d.get("stock_uom"),
				"qty_in_stock_uom": d.get("qty_in_stock_uom"),
				"total_weight": d.get("total_weight"),
				"amount": d.get("amount"),
				"total_volume": d.get("total_volume"),
				"total_area": d.get("total_area"),
				"price_per_unit_weight": d.get("price_per_unit_weight"),
				"price_per_day_weight": d.get("price_per_day_weight"),
				"price_per_unit_volume": d.get("price_per_unit_volume"),
				"price_per_day_volume": d.get("price_per_day_volume"),
			})
			total_storage_charges += d.get("storage_charges", 0)
			total_area += d.get("total_area", 0)

			# else:
			# 	print("inside else")

		print("customer , company",customer,company)
		print("Total charges:", total_storage_charges, "Total area:", total_area)
		return total_storage_charges, total_area

	def calculate_storage_charges(self,days_stored,total_amount,total_quantt,total_area,price_per_day,ppuv,ppuw,ppdw,ppdv):
		print ("######4555555"*5)
		total_quantity = total_quantt
		print("Total Quantity:", total_quantity)
		# print("Total Amount before charges:", total_amount)
		# storage_charges_till_date = total_amount
		print("Total Amount before charges:", )   
		storage_charges_till_date = 0
		print("storage_charges_till_date",storage_charges_till_date)

		total_daily_charge = 0
		# for day in range(1, days_stored + 1):

		print("days_stored########",days_stored)

		total_charges = 0

		if ppuw != 0 and ppdw != 0:
			total_charges_for_one_qty = ppuw * ppdw * days_stored
			print("*total_charges_for_one_qty for weight **",total_charges_for_one_qty, ppuw * ppdw * days_stored)
			total_charges += total_quantity * total_charges_for_one_qty


		elif ppuv != 0 and ppdv != 0:
			total_charges_for_one_qty = ppuv * ppdv * days_stored
			print("ppuv * ppdv * days_stored",ppuv,ppdv,days_stored)
			print("*total_charges_for_one_qty for volumne**",total_charges_for_one_qty)
			total_charges += total_quantity * total_charges_for_one_qty
		
		
		total_charges += storage_charges_till_date
		# total_charges == total_area * price_per_day
		print('***total_charges***',total_charges)

		daily_charge_area = total_area * price_per_day
		print("daily_charge_area",daily_charge_area)
		total_daily_charge_for_quantity = daily_charge_area * total_quantity
		print("total_daily_charge_for_quantity",total_daily_charge_for_quantity)
		total_charges += total_daily_charge_for_quantity * days_stored
		print("total_charges",total_charges)

		return total_charges
		




		# daily_charge_area = total_area * price_per_day
		# 	print("$$$$$$$$$$$$",daily_charge_area)
		# 	# print(f"Day {day}: Daily charge per day on total area : {daily_charge_area}")
		# 	total_daily_charge_for_quantity = daily_charge_area * total_quantity
		# 	print("daily_charge_area * total_quantity", total_quantity)
		# 	print("total_daily_charge_for_quantity",total_daily_charge_for_quantity)
		# 	total_daily_charge += total_daily_charge_for_quantity
		# 	print("total_daily_charge",total_daily_charge)
		# 	# print("Total charges for day {day} including area : ", total_daily_charge)

		# print("Total Charge for quantity until day", days_stored, ":", total_daily_charge)
		
		# storage_charges_till_date += total_daily_charge
		# print("Storage bill chraged till date:", storage_charges_till_date)
		# return storage_charges_till_date


	def on_submit(self):

		total_amount = self.str_charges
		print("total_amount",total_amount)
		total_items = len(self.items)
		print('Total Items using len :',total_items)
		total_rate = total_amount / total_items
		cost_center = ""
		customer = frappe.get_doc("Customer",self.customer)
		print("customer----->",customer)
		sett = frappe.get_doc("Third Party Logistics Setting")
		print("sett------->",sett)
		if not sett.storage_defaults:
			frappe.throw("Please Select Storage Cost Center in Third Party Logistics Setting")
		for i in sett.storage_defaults:
			if self.company == i.get("company"):
				if not i.get("cost_center"):
					frappe.throw("Please Select Storage Cost Center in Third Party Logistics Setting")
				cost_center = i.get("cost_center")
				
		si = frappe.new_doc('Sales Invoice')
		print("#######------>",si)
		si.customer = self.customer
		si.company = self.company
		print("si.customer------->",si.customer)
		print("si.company------->",si.company)
		si.append("items",{
			"item_code":sett.storage_item,
			"qty" : total_items,
			'rate':total_rate,
			"amount":total_amount,
			"cost_center":cost_center
		})
		print("si$$$$$$$$$$$$$$$",si)
		si.storage_bill = self.name
		print("si.storage_bill-------->",si.storage_bill)
		si.save(ignore_permissions=True)
		frappe.msgprint(" Sales Invoice Created Successfully......! ")