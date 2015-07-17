from openerp.osv import osv, fields

class res_partner(osv.Model):
	_inherit = "res.partner"

	_columns = {
		'is_technician': fields.boolean('Is Technician?'),
	}

