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
		'capacity_type': fields.selection([('hours','No of Hours'), ('units', 'No of Units')], 'Installed Capacity'),
		'total_hours': fields.float('No of Hours'),
		'total_units': fields.integer('No of Units'),
	}

	def onchange_asset(self, cr, uid, ids, asset, context=None):
		asset = self.pool.get('asset.asset').browse(cr, uid, asset, context=context)
		return {'value': {	'name': asset.name, 
							'barcode_no': asset.barcode_no, 
							'asset_location_id': asset.property_stock_asset and asset.property_stock_asset.id or False
						}
				}

	def validate(self, cr, uid, ids, context=None):
		for asset in self.browse(cr, uid, ids):
			for l in asset.depreciation_line_ids:
				if l.depreciation_date and l.depreciation_date < asset.purchase_date:
					raise osv.except_osv(('Validation Error!'), ("Depreciation Start Date must be greater than Asset's Purchase Date"))
				if l.depreciation_date and l.depreciation_date_to and l.depreciation_date > l.depreciation_date_to:
					raise osv.except_osv(('Validation Error!'), ("Invalid Depreciation Date Range."))
		return super(account_asset, self).validate(cr, uid, ids, context)

	def compute_depreciation_board(self, cr, uid, ids, context=None):
		depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
		currency_obj = self.pool.get('res.currency')
		for asset in self.browse(cr, uid, ids, context=context):
			if asset.method == 'degressive':
				capacity_type = asset.capacity_type
				total_capacity = 0.0
				if capacity_type == 'hours':
					total_capacity = asset.total_hours
				elif capacity_type == 'units':	
					total_capacity = asset.total_units

				#check start & end date :
				for l in asset.depreciation_line_ids:
					if l.depreciation_date and l.depreciation_date < asset.purchase_date:
						raise osv.except_osv(('Validation Error!'), ("Depreciation Start Date must be greater than Asset's Purchase Date"))
					if l.depreciation_date and l.depreciation_date_to and l.depreciation_date > l.depreciation_date_to:
						raise osv.except_osv(('Validation Error!'), ("Invalid Depreciation Date Range."))
				#check if depreciation line capacity exceeds total installed capacity :
				capacity = 0.0
				for line in asset.depreciation_line_ids:
					if capacity_type == 'hours':
						capacity = capacity + line.hours
					elif capacity_type == 'units':
						capacity = capacity + line.units
				if capacity > total_capacity:
					raise osv.except_osv(('Validation Error!'),('Depreciation Units cannot exceed Installed Capacity.'))

				#to compute depreciation amount per depreciation line :
				du = 0.0
				if total_capacity:
					du = asset.purchase_value / total_capacity
				capacity = 0.0
				total_depreciation = 0.0
				for line2 in asset.depreciation_line_ids:
					if capacity_type == 'hours':
						capacity = line2.hours
					elif capacity_type == 'units':
						capacity = line2.units
					current_depreciation = capacity * du
					depreciation_line_obj.write(cr, uid, [line2.id], {
																		'amount': current_depreciation, 
																		'depreciated_value': total_depreciation
																	})
					total_depreciation = total_depreciation + current_depreciation
			else:
				return super(account_asset, self).compute_depreciation_board(cr, uid, ids, context)

class account_asset_depreciation_line(osv.osv):
	_inherit = "account.asset.depreciation.line"

	_columns = {
		'units': fields.integer('No of Units'),
		'hours': fields.float('No of Hours'),
		'capacity_type': fields.selection([('hours','No of Hours'), ('units', 'No of Units')], 'Installed Capacity'),
		'amount_copy': fields.related('amount', type='float', store=True, string='Current Depreciation', readonly=True),
		'depreciation_date_to': fields.date('Date To'),
	}

	def onchange_capacity(self, cr, uid, ids, capacity_type, name, context=None):
		vals = {}
		if not capacity_type:
			raise osv.except_osv(('Alert!'), ('Please select Installed Capacity in Assets form.'))
		if capacity_type:
			vals['capacity_type'] = capacity_type
			vals['name'] = str(name)
		return {'value': vals}

class account_asset_category(osv.osv):
	_inherit = "account.asset.category"

	_columns = {
		'method_linear_factor': fields.float('Linear Factor', digits=(10,4)),
		'method_number_readonly': fields.related('method_number', type='integer', string='Number of Depriciations', store=True, readonly=True),
		'method_number': fields.integer('Number of Depreciations', help="The number of depreciations needed to depreciate your asset"),
		'degressive_method_type': fields.selection([('hours','No of Hours'), ('units','No of Units')], 'Degressive Factor'),
		'operating_hours': fields.float('Hours of Operation'),
		'qty_produced': fields.integer('Qty of Units Produced'),
		'method_number_copy': fields.integer('Number of Depreciations'),
	}

	def onchange_method(self, cr, uid, ids, method, factor, context=None):
		if not method:
			return False
		if method == 'linear':
			return {'value': {'method_progress_factor':0, 'method_linear_factor':0, 'method_time':'number', 'method_period': 1}}
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
		if method == 'linear':
			vals['method_period'] = 1
		if number:
			vals['method_linear_factor'] = 1.0/number
			return {'value': vals}
		return vals

	def onchange_compute_no_of_linear_depreciations(self, cr, uid, ids, method_no_year, context=None):
		vals = {}
		vals['method_number'] = method_no_year * 12
		return {'value': vals}

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
		'method': fields.related('asset_id', 'method', type='char', string='Method'),
	}

	_defaults = {
		'remaining_value': 0.0,
		'depreciated_value': 0.0,
	}
