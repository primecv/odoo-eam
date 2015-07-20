from openerp.osv import osv, fields

class mro_request(osv.Model):
	_inherit = "mro.request"

	_columns = {
		'hospital_id': fields.many2one('res.partner', 'Hospital', domain="[('is_hospital','=',True)]"),
		'department_ids': fields.many2many('hospital.department', 'mro_request_hospital_departments', 'request_id', 'department_id', 'Departments'),
		'diagnostic': fields.text('Diagnostic'),
		'resolution': fields.text('Resolution'),
		'resolution_date': fields.date('Resolution Date'),
		'delivery_date': fields.date('Date of Delivery'),
		'technician_id': fields.many2one('res.partner', 'Expert (technician)', domain="[('is_technician','=',True)]"),
		'type': fields.selection([('Corrective','Corrective')],'Type of Maintenance'),
		
	}

	_defaults = {
		'type': 'Corrective',
	}

class mro_order(osv.Model):
	_inherit = "mro.order"

	_columns = {
		'type': fields.selection([('Preventive', 'Preventive')],'Type of Maintenance'),
		'technician_id': fields.many2one("res.partner", 'Technician', domain="[('is_technician','=',True)]"),
	}

	_defaults = {
		'type': 'Preventive'
	}
