from openerp.osv import osv, fields

class res_country_city(osv.Model):
	_name = "res.country.city"

	_columns = {
		'name': fields.char('City Name'),
		'country_id': fields.many2one('res.country', 'Country'),
	}

class res_country_county(osv.Model):
	_name = "res.country.county"

	_columns = {
		'name': fields.char('County Name'),
		'country_id': fields.many2one('res.country', 'Country'),
	}
