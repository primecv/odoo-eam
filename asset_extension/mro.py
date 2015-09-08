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
		'technician_id': fields.many2one('hr.employee', 'Expert (technician)', domain="[('is_technician','=',True)]"),
		'type': fields.selection([('Corrective','Corrective')],'Type of Maintenance'),
		
	}

	_defaults = {
		'type': 'Corrective',
	}

	def action_confirm(self, cr, uid, ids, context=None):
		""" Confirms maintenance request.
		@return: Newly generated Maintenance Order Id.
		"""
		order = self.pool.get('mro.order')
		order_id = False
		for request in self.browse(cr, uid, ids, context=context):
			order_id = order.create(cr, uid, {
				'date_planned':request.requested_date,
				'date_scheduled':request.requested_date,
				'date_execution':request.requested_date,
				'origin': request.name,
				'state': 'draft',
				'maintenance_type': 'bm',
				'asset_id': request.asset_id.id,
				'asset_location_id': request.asset_id.property_stock_asset and request.asset_id.property_stock_asset.id or False,
				'description': request.cause,
				'problem_description': request.description,
				'type': request.type,
				'cause': request.cause,
			})
		self.write(cr, uid, ids, {'state': 'run'})
		return order_id


class mro_order(osv.Model):
	_inherit = "mro.order"

	_columns = {
		'type': fields.selection([('Preventive', 'Preventive'), ('Corrective', 'Corrective')],'Type of Maintenance'),
		'technician_id': fields.many2one("hr.employee", 'Assigned To', domain="[('is_technician','=',True)]", track_visibility='onchange'),
		'asset_location_id': fields.many2one('stock.location', 'Asset Location', track_visibility='onchange'),
		'cause': fields.char('Cause', track_visibility='onchange'), 
		'intervention_type': fields.selection([('Internal', 'Internal'),('External', 'External')], 'Type of Intervention', track_visibility='onchange'),
		'diagnostic': fields.text('Diagnostic', track_visibility='onchange'),
		'resolution_part_id': fields.many2one('product.product', 'Part', track_visibility='onchange'),
		'resolution_note': fields.text('Description'),
		'resolution_date': fields.date('Resolution Date', track_visibility='onchange'),
		'delivery_date': fields.date('Date of Delivery', track_visibility='onchange'),
		'delivery_note': fields.text('Note'),
		'delivery_document_ids': fields.one2many('mro.order.delivery.attachments', 'order_id', 'Attachment(s)'),
		'documentation_attachments': fields.one2many('mro.order.documentation.attachments', 'order_id', 'Attachment(s)'),
	}

	_defaults = {
		#'type': 'Preventive'
	}


	def onchange_asset(self, cr, uid, ids, asset):
		value = {}
		if asset:
			value['asset_location_id'] = self.pool.get('asset.asset').browse(cr, uid, asset).property_stock_asset
		return {'value': value}

class mro_order_delivery_attachments(osv.Model):
	_name = "mro.order.delivery.attachments"

	_columns = {
		'order_id': fields.many2one('mro.order', 'Maintenance Order'),
		'name': fields.char('Filename'),
		'file': fields.binary('File'),
	}

class mro_order_documentation_attachments(osv.Model):
	_name = "mro.order.documentation.attachments"

	_columns = {
		'order_id': fields.many2one('mro.order', 'Maintenance Order'),
		'name': fields.char('Filename'),
		'file': fields.binary('File'),
	}
