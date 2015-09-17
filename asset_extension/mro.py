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

	def get_technician(self,cr,uid,ids,field_name,arg,context=None):
		result = {}
		for rec in self.browse(cr, uid, ids):
			result[rec.id] = False
			if not rec.type:
				result[rec.id] = False
			elif rec.type == 'Preventive':
				result[rec.id] = rec.technician_p_id and rec.technician_p_id.id or False
			elif rec.type == 'Corrective':
				result[rec.id] = rec.technician_id and rec.technician_id.id or False

		return result

	_columns = {
		'type': fields.selection([('Preventive', 'Preventive'), ('Corrective', 'Corrective')],'Type of Maintenance'),
		'technician_id': fields.many2one("hr.employee", 'Assigned To', domain="[('is_technician','=',True)]", track_visibility='onchange'),#used for corrective type of maintenance
		'technician_p_id': fields.many2one("hr.employee", 'Assigned To', domain="[('is_technician','=',True)]", track_visibility='onchange'),#used for preventive type of maintenance
		'technician_ref': fields.function(get_technician, type='many2one', relation='hr.employee', string='Technician', store=True),
		'asset_location_rel_id': fields.related('asset_id', 'property_stock_asset', type='many2one', relation='stock.location', string='Asset Location', store=True, track_visibility='onchange', readonly=True),
		'cause': fields.char('Cause', track_visibility='onchange'), 
		'intervention_type': fields.selection([('Internal', 'Internal'),('External', 'External')], 'Type of Intervention', track_visibility='onchange'),
		'diagnostic': fields.text('Diagnostic', track_visibility='onchange'),
		'date': fields.date('Date'),
		#'resolution_part_id': fields.many2one('product.product', 'Part', track_visibility='onchange'),
		'resolution_parts_line': fields.one2many('mro.order.parts.line', 'order_id', 'Resolution Parts'),
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

	def action_confirm(self, cr, uid, ids, context=None):        
		""" override default behaviour
		returns ready state
		"""
		return self.write(cr, uid, ids, {'state': 'ready'})

	def onchange_asset(self, cr, uid, ids, asset):
		value = {}
		if asset:
			value['asset_location_rel_id'] = self.pool.get('asset.asset').browse(cr, uid, asset).property_stock_asset
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

class mro_order_parts_line(osv.osv):
	_inherit = 'mro.order.parts.line'

	_columns = {
		'order_id': fields.many2one('mro.order', 'MRO Order'),
	}

	def create(self, cr, uid, values, context=None):
		search = []
		if 'maintenance_id' in values:
			search.append(('maintenance_id','=',values['maintenance_id']))
		if 'parts_id' in values:
			search.append(('parts_id','=',values['parts_id']))
		ids = self.search(cr, uid, search)
		if len(ids)>0:
			if values and 'parts_qty' not in values:
				values.update({'parts_qty': 0})
			elif not values:
				values = {}
				values.update({'parts_qty': 0})
			values['parts_qty'] = self.browse(cr, uid, ids[0]).parts_qty + values['parts_qty']
			self.write(cr, uid, ids[0], values, context=context)
			return ids[0]
		ids = self.search(cr, uid, [('maintenance_id','=',False)])
		if len(ids)>0:
			self.write(cr, uid, ids[0], values, context=context)
			return ids[0]
		return super(mro_order_parts_line, self).create(cr, uid, values, context=context)

