from openerp.osv import osv, fields

class depreciation_map_report(osv.osv):
	_name = "asset.depreciation.map.report"

	_description = "Asset Depreciation Map By Location"

	_columns = {
		'type': fields.selection([('service','Service'),('hospital','Hospital')], 'Type'),
		'service_location_id': fields.many2one('stock.location', 'Service', domain="[('usage','=','asset'),('location_id','!=',False)]"),
		'hospital_location_id': fields.many2one('stock.location', 'Hospital', domain="[('usage','=','asset'),('location_id','=',False)]"),
		'asset_ids': fields.one2many('account.asset.asset', 'depreciation_map_id', 'Assets', invisible=True),
		'user_id': fields.many2one('res.users', 'User'),
		'asset_ref': fields.many2one('asset.asset', 'Asset(optional)'),
	}

	_defaults = {
		'user_id': lambda obj, cr, uid, context: uid,
	}

	def onchange_type(self, cr, uid, ids, ttype, context=None):
		vals = {}
		vals['asset_ref'] = False
		if ttype == 'service':
			vals['hospital_location_id'] = False
		elif ttype == 'hospital':
			vals['service_location_id'] = False
		return {'value': vals}

	def print_report(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			#delete existing report ids:
			reports = self.search(cr, uid, [('id','!=',rec.id)])
			self.unlink(cr, uid, reports)

			#delete existing Assets list:
			cr.execute("""update account_asset_asset set depreciation_map_id=NULL""")

			#compute Depreication Map Data:
			if rec.type == 'service':
				location_id = rec.service_location_id.id
			else:
				location_id = rec.hospital_location_id.id

			if rec.asset_ref: #print report for selected asset
				account_assets = self.pool.get('account.asset.asset').search(cr, uid, [('asset_id','=',rec.asset_ref.id)])
				if account_assets:
					for acc_asset in self.pool.get('account.asset.asset').browse(cr, uid, account_assets):
						self.pool.get('account.asset.asset').write(cr, uid, [acc_asset.id], {'depreciation_map_id':rec.id})
			elif not rec.asset_ref: #print report for all assets in a location
				assets = self.pool.get('asset.asset').search(cr, uid, [('property_stock_asset','=',location_id)])
				if assets:
					account_assets = self.pool.get('account.asset.asset').search(cr, uid, [('asset_id','in',assets)])
					if account_assets:
						for acc_asset in self.pool.get('account.asset.asset').browse(cr, uid, account_assets):
							self.pool.get('account.asset.asset').write(cr, uid, [acc_asset.id], {'depreciation_map_id':rec.id})
			return self.pool['report'].get_action(cr, uid, ids, 'asset_account_hcv_extension.report_depreciation_map', context=context)

class account_asset_asset(osv.osv):
	_inherit = "account.asset.asset"

	_columns = {
		'depreciation_map_id': fields.many2one('asset.depreciation.map.report', 'Depreciation Map'),	
	}


