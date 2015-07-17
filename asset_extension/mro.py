from openerp.osv import osv, fields

class mro_request(osv.Model):
	_inherit = "mro.request"

	_columns = {
		'hospital_id': fields.many2one('res.partner', 'Hospital', domain="[('is_hospital','=',True)]"),
		'hospital_department_id': fields.many2one('hospital.category', 'Department'),
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
