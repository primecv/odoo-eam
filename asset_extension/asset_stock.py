#-*- coding:utf-8 -*-

from openerp.osv import osv, fields
from datetime import datetime

class asset_stock_move(osv.osv):
	_name = "asset.stock.move"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "Asset Moves"
	_order = "id desc"

	def get_asset_desc(self, cr, uid, ids, field_name, arg, context=None):
		desc = ''
		result={}
		for rec in self.browse(cr,uid,ids):
			result[rec.id] = ''
			if rec.type == 'asset':
				result[rec.id] = rec.asset_id.name
			elif rec.type == 'accessory':
				result[rec.id] = rec.accessory_id.name
		return result

	_columns = {
		'name': fields.char('Description', track_visibility='onchange'),
		'state': fields.selection([('draft','Draft'), ('done','Transferred'), ('cancel','Cancelled')], 'Status', track_visibility='onchange'),
		'type': fields.selection([('asset','Asset'), ('accessory','Accessory')], 'Type', track_visibility='onchange'),
		'accessory_id': fields.many2one('asset.asset', 'Accessory', domain="[('is_accessory','=',True)]", track_visibility='onchange'),
		'asset_id': fields.many2one('asset.asset', 'Asset', domain="[('is_accessory','=',False)]", track_visibility='onchange'),
		'equipment_ref': fields.function(get_asset_desc, type="char", string="Equipment", store=True),
		'date': fields.datetime('Date', track_visibility='onchange'),
		'create_date': fields.datetime('Creation Date', track_visibility='onchange'),
		'location_id': fields.many2one('stock.location', 'Source Location'),
		'location_dest_id': fields.many2one('stock.location', 'Destination Location', track_visibility='onchange'),
		'note': fields.text('Note'),
	}

	_defaults = {
		'create_date': datetime.now()
	}

	def create(self, cr, uid, vals, context=None):
		vals['state'] = 'draft'
		return super(asset_stock_move, self).create(cr, uid, vals, context)

	def do_transfer(self, cr, uid, ids, context=None):
		for move in self.browse(cr, uid, ids):
			if move.type == 'asset':
				asset_id = move.asset_id.id
				asset_label = 'Asset'
			else:
				asset_id = move.accessory_id.id
				asset_label = 'Accessory'
			if move.location_id.id == move.location_dest_id.id:
				raise osv.except_osv(('Validation Error!'), ('You cannot move %s to the same location.')%(asset_label))
			self.pool.get('asset.asset').write(cr, uid, [asset_id], {'property_stock_asset': move.location_dest_id.id})
		return self.write(cr, uid, ids, {'state': 'done'})

	def action_cancel(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'cancel'})

	def onchange_asset(self, cr, uid, ids, ttype, asset_id, accessory_id, location_id, context=None):
		vals = {}
		loc_id = False
		if ttype == 'asset':
			loc_id = self.pool.get('asset.asset').browse(cr, uid, [asset_id])[0].property_stock_asset
			loc_id = loc_id and loc_id.id or False
		elif ttype == 'accessory':
			loc_id = self.pool.get('asset.asset').browse(cr, uid, [accessory_id])[0].property_stock_asset
			loc_id = loc_id and loc_id.id or False
		vals['location_id'] = loc_id
		return {'value': vals}

	def onchange_type(self, cr, uid, ids, ttype, context=None):
		vals = {'asset_id': False, 'accessory_id': False}
		return {'value': vals}

