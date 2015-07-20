from openerp.osv import osv, fields

class hr_employee(osv.osv):
	_inherit = "hr.employee"

	_columns = {
		'is_technician': fields.boolean('Is Technician?'),
	}

