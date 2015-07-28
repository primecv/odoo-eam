from openerp.osv import osv, fields

class res_country_city(osv.Model):
	_name = "res.country.city"

	_columns = {
		'name': fields.char('City Name'),
		'county_id': fields.many2one('res.country.county', 'County'),
	}

class res_country_county(osv.Model):
	_name = "res.country.county"

	_columns = {
		'name': fields.char('County Name'),
		'island_id': fields.many2one('res.country.island', 'Island'),
	}

class res_country_island(osv.Model):
	_name = "res.country.island"

	_columns = {
		'name': fields.char('Island Name'),
		'country_id': fields.many2one('res.country', 'Country'),
	}
