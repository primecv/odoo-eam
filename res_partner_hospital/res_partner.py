from openerp.osv import osv, fields

class res_partner(osv.Model):
	_inherit = "res.partner"

	_columns = {
		'is_hospital': fields.boolean('Is Hospital?'),
		'department_ids': fields.many2many('hospital.department', 'res_partner_hospital_departments', 'hospital_id', 'department_id', 'Departments'),
	}


class hospital_department(osv.Model):
	_name = "hospital.department"
	
	_description = "Hospital Department - Service Areas"

	_columns = {
		'name': fields.char('Department Name'),
		'code': fields.char('Code'),
	}

