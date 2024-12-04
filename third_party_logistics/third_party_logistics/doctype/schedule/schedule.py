# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta

class Schedule(Document):
	def validate(self):
		if self.duration:
			if self.time_slots:
				for i in self.time_slots:
					updated_time = datetime.strptime(i.get("from_time"), '%H:%M:%S') + timedelta(minutes=self.duration)
					i.to_time = updated_time.time()
