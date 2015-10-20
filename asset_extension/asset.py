# -*- coding: utf-8 -*-
from openerp.osv import osv, fields

class asset_asset(osv.osv):
	_inherit = "asset.asset"

	_columns = {
		'asset_id': fields.char('ID'),
		'hospital_id': fields.many2one('res.partner', 'Hospital'),
		'department_ids': fields.many2many('hospital.department', 'asset_hospital_departments', 'asset_id', 'department_id', 'Departments'),
		'category_id': fields.many2one('asset.asset.category', 'Category'),
		'mark': fields.char('Mark'),
		'manuf_year': fields.date('Manufacturing Year'),
		'state_operation': fields.selection([('1', 'Active'),('0','Inactive')], 'State Operation'),
		'notes': fields.text('Notes'),
		'code': fields.char('Code'),
		'asset_value': fields.float('Value'),
		'asset_value_estimate': fields.float('Estimated Value'),
		'equipment_type': fields.selection([('equip1','Equipamento Biomédico'), ('equip2','Equipamento Refrigeração'), ('equip3','Equipamento Lavandaria'),('equip4','Equipamento Cozinha'),('equip5', 'Equipamento Informáticos'), ('equip6', 'Equipamentos de Escritório')], 'Equipment Family'),#not to be used
		'equipment_type_id': fields.many2one('asset.equipment.family', 'Equipment Family', track_visibility='onchange'),
		'barcode_label': fields.binary('Barcode'),
		'barcode_no': fields.char('Barcode No', track_visibility='onchange'),
		'location_island': fields.related('property_stock_asset', 'island', type='char', string='Island', store=True),
		'location_county': fields.related('property_stock_asset', 'county', type='char', string='County', store=True),
        'property_stock_asset': fields.property(
          type='many2one',
          relation='stock.location',
          string="Asset Location",
          store=True,
		  required=True,
          help="This location will be used as the destination location for installed parts during asset life."),
		'asset_location_child_ids': fields.one2many('asset.location.child.rel', 'child_id', 'Asset Location Hierarchy'),
		'asset_location_parent_ids': fields.one2many('asset.location.parent.rel', 'parent_id', 'Asset Location Hierarchy'),
		'asset_location_parent_search': fields.related('asset_location_parent_ids', 'location_id', 'name', type='char', string='Asset Location with Parent Locations'),
		'asset_location_child_search': fields.related('asset_location_child_ids', 'location_id', 'name', type='char', relation='stock.location', string='Asset Location with Child Locations'),
		'asset_location_rel_check': fields.boolean('Location Rel Check'),
		'equipment_origin_id': fields.many2one('asset.equipment.origin', 'Origin of the Equipment'),
		#accessory fields:
		'is_accessory': fields.boolean('Is Accessory'),
		'purchase_date': fields.date('Purchase Date'),
		'manuf_year': fields.date('Manufacturing Year'),
		'supplier_id': fields.many2one('res.partner', 'Supplier', domain="[('supplier','=',1)]"),

	}

	def create(self, cr, uid, vals, context=None):
		seq = self.pool.get('ir.sequence').get(cr, uid, 'asset.asset') 
		asset_id = ''
		hospital_seq = ''
		if 'hospital_id' in vals and vals['hospital_id']:
			hospital_seq = self.pool.get('res.partner').browse(cr, uid, [vals['hospital_id']])[0].name[0:3]
		if len(vals['name']) <= 3:
			name = vals['name']
		else:
			name = vals['name'][0:3]
		asset_id = hospital_seq + name + str(seq)
		vals['asset_id'] = asset_id
		codeseq = self.pool.get('ir.sequence').get(cr, uid, 'asset.code') 
		vals['code'] = codeseq
		res = super(asset_asset, self).create(cr, uid, vals, context)
		if 'property_stock_asset' in vals:
			location_id = vals['property_stock_asset']
			self.update_location_hierarchy(cr, uid, res, location_id)
		return res 

	def update_location_hierarchy(self, cr, uid, res, location_id):
		#get child locations:
		asset_location_parent_rel_obj = self.pool.get('asset.location.parent.rel')
		search_ids = asset_location_parent_rel_obj.search(cr, uid, [('parent_id','=',res)])
		asset_location_parent_rel_obj.unlink(cr,uid,search_ids)
		child_ids = []
		for loc in self.pool.get('stock.location').browse(cr, uid, [location_id]):
			for l in loc.child_ids:
				child_ids.append(l.id)
		child_ids.append(location_id)
		for loc in child_ids:
			asset_location_parent_rel_obj.create(cr, uid, {'location_id': loc, 'parent_id': res})
		#get parent locations:
		asset_location_child_rel_obj = self.pool.get('asset.location.child.rel')
		search_ids = asset_location_child_rel_obj.search(cr, uid, [('child_id','=',res)])
		asset_location_child_rel_obj.unlink(cr,uid,search_ids)
		parent_ids = []
		parent_ids.append(location_id)
		def parent_loc(location_id):
			parent_loc_id = None
			for locs in self.pool.get('stock.location').browse(cr, uid, [location_id]):
				parent_loc_id = locs.location_id.id
				parent_ids.append(parent_loc_id)
			if parent_loc_id:
				parent_loc(parent_loc_id)
		parent_loc(location_id)
		for loc in parent_ids:
			asset_location_child_rel_obj.create(cr, uid, {'location_id': loc, 'child_id': res})
		return True

	def write(self, cr, uid, ids, vals, context=None):
		if 'property_stock_asset' in vals:
			self.update_location_hierarchy(cr, uid, ids[0], vals['property_stock_asset'])
			vals['asset_location_rel_check'] = True
		#else:#used to update asset parent and child location hierarchy for old Records.
		#	for rec in self.browse(cr, uid, ids):
		#		if rec.property_stock_asset and rec.asset_location_rel_check is False:
		#			self.update_location_hierarchy(cr, uid, ids[0], rec.property_stock_asset.id)
		#			vals['asset_location_rel_check'] = True
		return super(asset_asset, self).write(cr, uid, ids, vals, context)

	def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
		res = super(asset_asset, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)
		if context and 'default_active' in context:
			cr.execute('select id from asset_asset')
			records = cr.fetchall()
			if not args:
				args = [['id', 'in', list(records)]]
			else:
				args.append(['id', 'in', list(records)])
			res = super(asset_asset, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)
		return res

	def onchange_hospital(self, cr, uid, ids, hospital_id, context=None):
		if not hospital_id:
			return {'value': {'department_ids': []}}
		departments = []
		for partner in self.pool.get('res.partner').browse(cr, uid, [hospital_id]):
			for dept in partner.department_ids:
				departments.append(dept.id)
		return {'value': {'department_ids': [6,0,departments]}}

	def onchange_equipment_type(self, cr, uid, ids, equip_id, context=None):
		if not equip_id:
			return {'value': {}}
		return {'value': {'category_id': False}}

class asset_asset_category(osv.Model):
	_name = "asset.asset.category"

	_columns = {
		'name': fields.char('Category Name', required=True, select=True),
		'code': fields.char('Code'),
		'equipment_family_id': fields.many2one('asset.equipment.family', 'Related Equipment Family'),
	}

class asset_equipment_familyt(osv.Model):
	_name = "asset.equipment.family"

	_columns = {
		'name': fields.char('Equipment Family'),
	}

class asset_equipment_origin(osv.Model):
	_name = "asset.equipment.origin"
	_description = "Equipment Origin"

	_columns = {
		'name': fields.char('Equipment Origin'),
	}
	
#dummy table to manage Asset Location parent-child hierarchy to be used in Asset Search:
class asset_location_parent_rel(osv.Model):
	_name = "asset.location.parent.rel"

	_columns = {
		'location_id': fields.many2one('stock.location', 'Location'),
		'parent_id': fields.many2one('asset.asset', 'Parent Asset'),
	}

class asset_location_child_rel(osv.Model):
	_name = "asset.location.child.rel"

	_columns = {
		'location_id': fields.many2one('stock.location', 'Location'),
		'child_id': fields.many2one('asset.asset', 'Child Asset'),
	}

