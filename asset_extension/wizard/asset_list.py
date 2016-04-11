# -*- coding: utf-8 -*-
from openerp.osv import osv, fields

class hcv_equipment_list(osv.osv_memory):
	_name = "hcv.equipment.list"
	_description = "List of Equipments into a Hospital"

	_columns = {
		'location_id': fields.many2one('stock.location', 'Location', domain="[('usage','=','asset')]"),
		'asset_ids': fields.one2many('asset.asset.hcv.list', 'hcv_id', 'Assets'),
		'total_assets': fields.integer('Total Assets'),
		'partner_id': fields.many2one('res.partner', 'Partner'),
	}

	_defaults = {
		'partner_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, [uid])[0].partner_id.id
	}

	def print_report(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			loc_id = rec.location_id.id
			assets = self.pool.get('asset.asset').search(cr, uid, [('property_stock_asset','=',loc_id)])
			for asset in assets:
				self.pool.get('asset.asset.hcv.list').create(cr, uid, {'hcv_id': rec.id, 'asset_id': asset})
			self.write(cr, uid, ids, {'total_assets': len(assets)})
		return self.pool['report'].get_action(cr, uid, ids, 'asset_extension.report_hcv_equipments', context=context)


class asset_asset_hcv_list(osv.osv_memory):
	_name = "asset.asset.hcv.list"
	_description = "Asset List"

	_columns = {
		'hcv_id': fields.many2one('hcv.equipment.list', 'HCV'),
		'asset_id': fields.many2one('asset.asset', 'Asset'),
	}

