
def calculate_volume(self,method):
		if self.custom_item_length:
			if self.custom_item_breadth:
				if self.custom_item_height:
					self.custom_volume_per_unit = self.custom_item_length * self.custom_item_breadth * self.custom_item_height
					self.custom_area_per_unit = self.custom_item_length * self.custom_item_breadth
					pass