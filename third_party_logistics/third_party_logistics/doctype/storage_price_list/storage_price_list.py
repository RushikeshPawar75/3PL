# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, msgprint, scrub
from frappe.model.document import Document
from frappe.utils import flt


class StoragePriceList(Document):
		def validate(self):
				self.validate_dates()
				for i in self.prices_per_sqft:
					if i.price_per_day == 0:
						frappe.throw(f"Price per day should be greater than zero row : {i.idx}")
				
		def validate_dates(self):
			"""Validate To Date should not be less than From Date."""
			if self.from_date and self.to_date and self.from_date > self.to_date:
				msgprint(_("To Date cannot be less than From Date."))
				raise frappe.ValidationError("To Date cannot be less than From Date.")	
