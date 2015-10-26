# -*- coding: utf-8 -*-
from openerp.osv import osv, fields

class asset_list_report(osv.osv):
	_name = "asset.list.report"

	_columns = {
		'name': fields.char('Name'),
		'partner_id': fields.many2one('res.partner', 'Partner'),
		'asset_list': fields.one2many('asset.asset', 'asset_report_id', 'Assets'),
		'total_assets': fields.integer('Total'),
	}

	_defaults = {
		'partner_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, [uid])[0].partner_id.id
	}

	def print_report(self, cr, uid, ids, context=None):
		cr.execute("update asset_asset set asset_report_id=NULL")
		partner = self.pool.get('res.users').browse(cr, uid, [uid])[0].partner_id.id
		self.write(cr, uid, ids, {'partner_id': partner})
		if context and 'active_model' in context and context['active_model'] == 'asset.asset':
			assets = context.get('active_ids', False)
			if len(assets) and len(assets) == 1:
				cr.execute("update asset_asset set asset_report_id=%s where id=%s"%(ids[0], assets[0]))
			elif len(assets) and len(assets) > 1:
				cr.execute("update asset_asset set asset_report_id=%s where id in %s"%(ids[0], tuple(assets)))
			self.write(cr, uid, ids, {'total_assets': len(assets)})
		return self.pool['report'].get_action(cr, uid, ids, 'asset_extension.report_assetlist', context=context)

class asset_asset(osv.osv):
	_inherit = "asset.asset"

	_columns = {
		'asset_report_id': fields.many2one('asset.list.report', 'Report Id'),
	}
