# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, msgprint, scrub
from frappe.model.document import Document
from frappe.utils import flt

class PickupPriceList(Document):
	def validate(self):
			self.validate_dates()
			self.validate_distances()
			self.validate_weight()

	def validate_distances(self):
		"""Validate To Distance should not be less than From Distance."""
		for i in self.price_matrix:
			print("***i.from_distance and i.to_distance and i.from_distance > i.to_distance****",i.from_distance , i.to_distance , i.from_distance , i.to_distance)
			if i.from_distance > i.to_distance:
				msgprint(_("To Distance cannot be less than From Distance."))
				raise frappe.ValidationError("To Distance cannot be less than From Distance.")
		
	def validate_dates(self):
			"""Validate To Date should not be less than From Date."""
			if self.from_date and self.to_date and self.from_date > self.to_date:
				msgprint(_("To Date cannot be less than From Date."))
				raise frappe.ValidationError("To Date cannot be less than From Date.")
			
	def validate_weight(self):
		for i in self.price_matrix:
			if i.from_weight > i.to_weight:
				frappe.msgprint(_("To Weight cannot be less than From Weight."))
				raise frappe.ValidationError("To Weight cannot be less than From Weight.")
