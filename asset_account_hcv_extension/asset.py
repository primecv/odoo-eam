# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Prime Consulting, Cape Verde (<http://prime.cv>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv

class asset_asset(osv.osv):
	_inherit = "asset.asset"

	_columns = {
		'account_asset_category_id': fields.many2one('account.asset.category', 'Asset Category'),
	}

class account_asset(osv.osv):
	_inherit = 'account.asset.asset'

	_columns = {
		'asset_location_id': fields.related('asset_id', 'property_stock_asset', relation='stock.location', type='many2one', string='Asset Location', store=True, readonly=True),
		'barcode_no': fields.related('asset_id', 'barcode_no', type='char', string='Barcode No', store=True, readonly=True),
	}

	def onchange_asset(self, cr, uid, ids, asset, context=None):
		asset = self.pool.get('asset.asset').browse(cr, uid, asset, context=context)
		return {'value': {	'name': asset.name, 
							'barcode_no': asset.barcode_no, 
							'asset_location_id': asset.property_stock_asset and asset.property_stock_asset.id or False
						}
				}

class account_asset_category(osv.osv):
	_inherit = "account.asset.category"

	_columns = {
		'method_linear_factor': fields.float('Linear Factor', digits=(10,4)),
		'method_number_readonly': fields.related('method_number', type='integer', string='Number of Depriciations', store=True, readonly=True),
		'method_number': fields.integer('Number of Depreciations', help="The number of depreciations needed to depreciate your asset"),
	}

	def onchange_method(self, cr, uid, ids, method, factor, context=None):
		if not method:
			return False
		if method == 'linear':
			return {'value': {'method_progress_factor':0, 'method_linear_factor':0, 'method_time':'number'}}
		return {'value': {'method_progress_factor': 0}}

	def onchange_method_factor(self, cr, uid, ids, factor, context=None):
		#if factor and factor != 0:
			##return {'value': {'method_number': 1/factor, 'method_number_readonly': 1/factor}}
			#return {'value': {'method_linear_factor': factor}}
		return {}

	def onchange_method_number(self, cr, uid, ids, number, context=None):
		vals= {}
		if number:
			vals['method_linear_factor'] = 1.0/number
			print "######",vals
			return {'value': vals}
		return vals
