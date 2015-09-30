from openerp.osv import osv, fields
import time

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

	def get_available_parts(self, cr, uid, ids, name, arg, context=None):
		res = {}
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {}
			done_line_ids = []
			if order.move_lines:
				done_line_ids += [move.id for move in order.move_lines if move.state == 'done']
			res[order.id]['parts_moved_lines'] = done_line_ids
		return res

	STATE_SELECTION = [
        ('draft', 'DRAFT'),
        ('released', 'WAITING PARTS'),
        ('ready', 'READY TO MAINTENANCE'),
		('validate', 'VALIDATED'),
        ('done', 'DONE'),
        ('cancel', 'CANCELED')
    ]

	_columns = {
		'state': fields.selection(STATE_SELECTION, 'Status', readonly=True, track_visibility='onchange'),
		'type': fields.selection([('Preventive', 'Preventive'), ('Corrective', 'Corrective')],'Type of Maintenance'),
		'technician_id': fields.many2one("hr.employee", 'Assigned To', domain="[('is_technician','=',True)]", track_visibility='onchange'),#used for corrective type of maintenance
		'technician_p_id': fields.many2one("hr.employee", 'Assigned To', domain="[('is_technician','=',True)]", track_visibility='onchange'),#used for preventive type of maintenance
		'technician_ref': fields.function(get_technician, type='many2one', relation='hr.employee', string='Technician', store=True),
		'asset_location_rel_id': fields.related('asset_id', 'property_stock_asset', type='many2one', relation='stock.location', string='Asset Location', store=True, track_visibility='onchange', readonly=True),
		'barcode_no': fields.related('asset_id', 'barcode_no', type='char', string='Barcode No', store=True, readonly=True),
		'cause': fields.char('Cause', track_visibility='onchange'), 
		'intervention_type': fields.selection([('Internal', 'Internal'),('External', 'External')], 'Type of Intervention', track_visibility='onchange'),
		'diagnostic': fields.text('Diagnostic', track_visibility='onchange'),
		'date': fields.date('Date'),
		#'resolution_part_id': fields.many2one('product.product', 'Part', track_visibility='onchange'),
		'resolution_parts_line': fields.one2many('mro.order.resolution.line', 'order_id', 'Resolution Parts'),
		'resolution_note': fields.text('Description'),
		'resolution_date': fields.date('Resolution Date', track_visibility='onchange'),
		'delivery_date': fields.date('Date of Delivery', track_visibility='onchange'),
		'delivery_note': fields.text('Note'),
		'delivery_document_ids': fields.one2many('mro.order.delivery.attachments', 'order_id', 'Attachment(s)'),
		'documentation_attachments': fields.one2many('mro.order.documentation.attachments', 'order_id', 'Attachment(s)'),

		'move_lines': fields.one2many('stock.move', 'mro_order_id', 'Moves'),

		'parts_moved_lines': fields.function(get_available_parts, relation="stock.move", method=True, type="one2many", multi='parts'),
		'maintenance_cost': fields.float('Cost of Maintenance'),
		'work_hours': fields.float('Work Hours'),
		'maintenance_c_cost': fields.float('Cost of Maintenance'),
		'work_c_hours': fields.float('Work Hours'),
		
		'tools_description_confirm': fields.text('Tools Description',translate=True, track_visibility='onchange'),
        'operations_description_confirm': fields.text('Operations Description',translate=True, track_visibility='onchange'),
		'documentation_attachments_confirm': fields.one2many('mro.order.documentation.attachments', 'order_confirm_id', 'Attachment(s)'),
		'task_id': fields.many2one('mro.task', 'Task'),
		'validation_date': fields.date('Validation Date'),
		'validation_note': fields.text('Note'),
	}

	_defaults = {
		#'type': 'Preventive'
	}

	_order = "id desc"

	def write(self, cr, uid, ids, vals, context=None):
		for rec in self.browse(cr, uid, ids):
			mro_type = rec.type
			if 'type' in vals:
				mro_type = vals['type']
			if not rec.task_id:
				if mro_type == 'Preventive':
					technician_id = rec.technician_p_id and rec.technician_p_id.id or False
					if 'technician_p_id' in vals:
						technician_id = vals['technician_p_id']
					if technician_id:
						task_id = self.pool.get('mro.task').create(cr, uid, {'name': rec.name, 
																		'technician_id': technician_id,
																		'maintenance_type': 'pm',
																		'mro_id': rec.id,
																		'request_date': rec.date_execution,
																		'description': rec.description,
																		})
						vals['task_id'] = task_id
				elif mro_type == 'Corrective':
					technician_id = rec.technician_id and rec.technician_id.id or False
					if 'technician_id' in vals:
						technician_id = vals['technician_id']
					if technician_id:
						task_id = self.pool.get('mro.task').create(cr, uid, {'name': rec.name, 
																		'technician_id': technician_id,
																		'maintenance_type': 'cm',
																		'mro_id': rec.id,
																		'request_date': rec.date_scheduled,
																		'cause': rec.cause
																		})
						vals['task_id'] = task_id
			else:
				if mro_type == 'Preventive':
					if 'technician_p_id' in vals:
						technician_id = vals['technician_p_id']
						self.pool.get('mro.task').write(cr, uid, [rec.task_id.id], {'technician_id': technician_id,
																					'mro_id': rec.id, 
																					'request_date': rec.date_execution,
																					'description': rec.description})
				elif mro_type == 'Corrective':
					if 'technician_id' in vals:
						technician_id = vals['technician_id']
						self.pool.get('mro.task').write(cr, uid, [rec.task_id.id], {'technician_id': technician_id, 
																					'mro_id': rec.id,
																					'request_date': rec.date_scheduled,
																					'cause': rec.cause})
		return super(mro_order, self).write(cr, uid, ids, vals, context=None)

	def button_done(self, cr, uid, ids, context=None):
		for order in self.browse(cr, uid, ids, context=context):
			if order.type == 'Preventive':
				self.pool.get('stock.move').action_done(cr, uid, [x.id for x in order.move_lines])
			elif order.type == 'Corrective':
				picking_type_id, source_location_id, location_dest_id = 0, 0, 0
				picking_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'picking_type_internal')
				if picking_type_id:
					picking_type_id = picking_type_id[1]

				source_location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
				if source_location_id:
					source_location_id = source_location_id[1]

				location_dest_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'location_maintenance')
				if location_dest_id:
					location_dest_id = location_dest_id[1]

				for rec in self.browse(cr, uid, ids):
					group_id = self.pool.get("procurement.group").create(cr, uid, {'name': rec.name}, context=context)
					for line in rec.resolution_parts_line:
						if line.qty <= 0:
							raise osv.except_osv(('Error!'), ('Invalid Parts Quantity.'))
						else:
							move_id = self.pool.get('stock.move').create(cr, uid, {
										'product_id': line.parts_id.id,
										'product_uom_qty': line.qty,
										'product_uom': line.parts_id.product_tmpl_id.uom_id.id,
										'name': 'Maintenance Order ' + rec.name,
										'picking_type_id': picking_type_id,
										'location_id': source_location_id,
										'location_dest_id': location_dest_id,
										'group_id': group_id or None,
										'mro_order_id': rec.id
									})
							self.pool.get('stock.move').action_done(cr, uid, [move_id])
		self.write(cr, uid, ids, {'state': 'done', 'date_execution': time.strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def button_cancel(self, cr, uid, ids, context=None):
		for order in self.browse(cr, uid, ids, context=context):
			self.pool.get('stock.move').action_cancel(cr, uid, [x.id for x in order.move_lines])
		self.write(cr, uid, ids, {'state': 'cancel'})
		return True

	def button_validate(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'validate'})
	
	def action_confirm(self, cr, uid, ids, context=None):        
		""" override default behaviour
		returns ready state
		"""
		'''picking_type_id, source_location_id, location_dest_id = 0, 0, 0
		picking_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'picking_type_internal')
		if picking_type_id:
			picking_type_id = picking_type_id[1]

		source_location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
		if source_location_id:
			source_location_id = source_location_id[1]

		location_dest_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'location_maintenance')
		if location_dest_id:
			location_dest_id = location_dest_id[1]

		for rec in self.browse(cr, uid, ids):
			group_id = self.pool.get("procurement.group").create(cr, uid, {'name': rec.name}, context=context)
			for line in rec.parts_lines:
				if line.parts_qty <= 0:
					raise osv.except_osv(('Error!'), ('Invalid Parts Quantity.'))
				else:
					move_id = self.pool.get('stock.move').create(cr, uid, {
								'product_id': line.parts_id.id,
								'product_uom_qty': line.parts_qty,
								'product_uom': line.parts_id.product_tmpl_id.uom_id.id,
								'name': 'Maintenance Order ' + rec.name,
								'picking_type_id': picking_type_id,
								'location_id': source_location_id,
								'location_dest_id': location_dest_id,
								'group_id': group_id or None,
								'mro_order_id': rec.id
							})
					self.pool.get('stock.move').action_done(cr, uid, [move_id])'''
		return self.write(cr, uid, ids, {'state': 'ready'})

	def onchange_asset(self, cr, uid, ids, asset):
		value = {}
		if asset:
			value['asset_location_rel_id'] = self.pool.get('asset.asset').browse(cr, uid, asset).property_stock_asset
			value['barcode_no'] = self.pool.get('asset.asset').browse(cr, uid, asset).barcode_no or False
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
		'order_confirm_id': fields.many2one('mro.order', 'Maintenance Order'),
		'name': fields.char('Filename'),
		'file': fields.binary('File'),
	}

class mro_order_resolution_line(osv.osv):
	_name = 'mro.order.resolution.line'

	_columns = {
		'parts_id': fields.many2one('product.product', 'Parts', required=True),
		'qty': fields.integer('Quantity'),
		'order_id': fields.many2one('mro.order', 'MRO Order'),
	}

	_defaults = {
		'qty': 1,
	}

class mro_order_parts_line(osv.osv):
	_inherit = 'mro.order.parts.line'

	#_columns = {
	#	'order_id': fields.many2one('mro.order', 'MRO Order'),
	#}

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

class mro_task(osv.osv):
	_inherit = "mro.task"

	_columns = {
		'mro_id': fields.many2one('mro.order', 'Maintenance Order', track_visibility='onchange'),
		'technician_id': fields.many2one('hr.employee', 'Technician', domain="[('is_technician','=',True)]", track_visibility='onchange'),
		'category_id': fields.many2one('asset.category', 'Asset Category', ondelete='restrict', required=False),
		'request_date': fields.date('Request Date', track_visibility='onchange'),
		'description': fields.char('Description', track_visibility='onchange'),
		'cause': fields.char('Cause', track_visibility='onchange')
	}

class stock_move(osv.osv):
	_inherit = "stock.move"

	_columns = {
		'mro_order_id': fields.many2one('mro.order', 'Maitenance Order'),
	}

	def onchange_parts_id(self, cr, uid, ids, product_id, model=None, context=None):
		vals = {}
		if model == 'mro.order' and product_id:
			picking_type_id, source_location_id, location_dest_id = 0, 0, 0
			picking_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'picking_type_internal')
			if picking_type_id:
				picking_type_id = picking_type_id[1]

			source_location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
			if source_location_id:
				source_location_id = source_location_id[1]

			location_dest_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'location_maintenance')
			if location_dest_id:
				location_dest_id = location_dest_id[1]

			vals['name'] = 'Maintenance Order '
			uom_id = self.pool.get('product.product').browse(cr, uid, [product_id])[0].product_tmpl_id.uom_id.id
			vals['product_uom'] = uom_id 
			vals['picking_type_id'] = picking_type_id
			vals['location_id'] = source_location_id
			vals['location_dest_id'] = location_dest_id
		return {'value': vals}

	def create(self, cr, uid, vals, context=None):
		if 'mro_order_id' in vals and vals['mro_order_id']:
			ids = [vals['mro_order_id']]
			for rec in self.pool.get('mro.order').browse(cr, uid, ids):
				group_id = self.pool.get("procurement.group").create(cr, uid, {'name': rec.name}, context=context)
				if vals['product_uom_qty'] <= 0:
					raise osv.except_osv(('Error!'), ('Invalid Parts Quantity to be Consumed.'))
				else:
					vals['name'] = 'Maintenance Order ' + rec.name
					vals['group_id'] = group_id
		return super(stock_move, self).create(cr, uid, vals, context)

