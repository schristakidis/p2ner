
def is_vw(location_id):
	location_id = str(location_id).lower()
	return "be-ibbt" in location_id or "be-iminds" in location_id

def is_cells(location_id):
	return "uk-hplabs" in str(location_id).lower()

def is_aws(location_id):
	return str(location_id).lower().endswith("aws")

def is_federica(location_id):
	return "federica" in str(location_id).lower()

def is_autobahn(location_id):
	return "autobahn" in str(location_id).lower()

def is_one(location_id):
	return not (is_vw(location_id) or is_cells(location_id) or is_aws(location_id) or is_federica(location_id) or is_autobahn(location_id))