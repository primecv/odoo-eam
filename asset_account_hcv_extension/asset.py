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

	def get_depreciation_lines(self, cr, uid, ids, field_name, arg, context=None):
		account_asset_obj = self.pool.get('account.asset.asset')
		lines = account_asset_obj.search(cr, uid, [('asset_id', '=', ids[0])])
		dp_lines = []
		for asset in account_asset_obj.browse(cr, uid, lines):
			for dp_line in asset.depreciation_line_ids:
				dp_lines.append(dp_line.id)
		return dict([(id, dp_lines) for id in ids])

	def _depr_count(self, cr, uid, ids, field_name, arg, context=None):
		res = dict.fromkeys(ids, 0)
		depr = self.pool['account.asset.depreciation.line']
		for asset in self.browse(cr, uid, ids, context=context):
			res[asset.id] = depr.search_count(cr,uid, [('asset_asset_id', '=', asset.id)], context=context)
		return res

	_columns = {
		'account_asset_category_id': fields.many2one('account.asset.category', 'Asset Category'),
		'depreciation_line': fields.function(get_depreciation_lines, type='one2many', relation='account.asset.depreciation.line', string='Depreciation Lines'),
        'depr_count': fields.function(_depr_count, string='# Depreciations', type='integer'),
	}


	_defaults = {
		 'depreciation_line': lambda self, cr, uid, context : self.get_depreciation_lines(cr, uid, [0], '', '', context)[0],
	}

	def action_view_depreciation_lines(self, cr, uid, ids, context=None):
		return {
            'domain': "[('asset_asset_id','in',[" + ','.join(map(str, ids)) + "])]",
            'name': ('Depreciation Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.depreciation.line',
            'type': 'ir.actions.act_window',
            'target': 'current',
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
		'degressive_method_type': fields.selection([('hours','No of Hours'), ('units','No of Units')], 'Degressive Factor'),
		'operating_hours': fields.float('Hours of Operation'),
		'qty_produced': fields.integer('Qty of Units Produced'),
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

	def onchange_method_number(self, cr, uid, ids, method, number, period, context=None):
		vals= {}
		period = float(period)
		if method == 'degressive':
			if number:
				vals['method_progress_factor'] = period / number
		if number:
			vals['method_linear_factor'] = 1.0/number
			return {'value': vals}
		return vals

	def onchange_degressive_method_type(self, cr, uid, ids, degressive_method_type, context=None):
		vals = {}
		if degressive_method_type:
			vals['qty_produced'], vals['operating_hours'], vals['method_number'] = 0, 0, 0
		return {'value': vals}

	def onchange_units(self, cr, uid, ids, units, context=None):
		vals = {}
		if units:
			vals['method_number'] = units
		return {'value': vals}

	def onchange_hours(self, cr, uid, ids, hours, context=None):
		vals = {}
		if hours:
			vals['method_number'] = int(hours)
		return {'value': vals}

class account_asset_depreciation_line(osv.osv):
	_inherit = 'account.asset.depreciation.line'

	_columns = {
		'asset_asset_id': fields.related('asset_id', 'asset_id', type='many2one', relation='asset.asset'),
	}

	_defaults = {
		'remaining_value': 0.0,
		'depreciated_value': 0.0,
	}
