from openerp.osv import osv, fields

class res_partner(osv.Model):
	_inherit = "res.partner"

	_columns = {
		'is_hospital': fields.boolean('Is Hospital?'),
		'hospital_category_id': fields.many2one('hospital.category', 'Department')
	}


class hospital_category(osv.Model):
	_name = "hospital.category"
	
	_description = "Hospital Category - Department"

	_columns = {
		'name': fields.char('Department Name'),
		'code': fields.char('Code'),
	}

