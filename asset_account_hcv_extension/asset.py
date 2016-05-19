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
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

	def get_dates(self, cr, uid, lines):
		deprs = []
		for depr in lines:
			deprs.append(depr.id)
		smallest = self.pool.get('account.asset.depreciation.line').search(cr, uid, [('id','in',deprs), ('depreciation_date is not null')], order='depreciation_date asc')
		greatest = self.pool.get('account.asset.depreciation.line').search(cr, uid, [('id', 'in', deprs), ('depreciation_date is not null')], order='depreciation_date desc')
		sdate, gdate = False, False
		if smallest:
			for rec in self.pool.get('account.asset.depreciation.line').browse(cr, uid, [smallest[0]]):
				sdate = rec.depreciation_date
		if greatest:
			for rec in self.pool.get('account.asset.depreciation.line').browse(cr, uid, [greatest[0]]):
				gdate = rec.depreciation_date
		return (sdate, gdate)

	def check_depreciation_period(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			assets = self.search(cr, uid, [('asset_id','=',rec.asset_id.id), ('id','!=',rec.id)])
			flag = True
			for asset in self.browse(cr, uid, assets):
				for curr_depr in rec.depreciation_line_ids:
					for depr in asset.depreciation_line_ids:
						if depr.depreciation_date and depr.depreciation_date_to:
							if curr_depr.depreciation_date and curr_depr.depreciation_date_to:
								if (curr_depr.depreciation_date >= depr.depreciation_date and \
									curr_depr.depreciation_date <= depr.depreciation_date_to) or \
									(curr_depr.depreciation_date_to >= depr.depreciation_date and \
									curr_depr.depreciation_date_to <= depr.depreciation_date_to):
									flag = False
									break
							elif curr_depr.depreciation_date and not curr_depr.depreciation_date_to:
								if (curr_depr.depreciation_date >= depr.depreciation_date and \
									curr_depr.depreciation_date <= depr.depreciation_date_to):
									flag = False
									break
							elif not curr_depr.depreciation_date and curr_depr.depreciation_date_to:
								if (curr_depr.depreciation_date_to >= depr.depreciation_date and \
									curr_depr.depreciation_date_to <= depr.depreciation_date_to):
									flag = False
									break
						elif depr.depreciation_date and not depr.depreciation_date_to:
							smallest, largest = self.get_dates(cr, uid, asset.depreciation_line_ids)
							if smallest and largest:
								if curr_depr.depreciation_date and curr_depr.depreciation_date >= smallest \
									and curr_depr.depreciation_date <= largest:
									flag = False
									break
								if curr_depr.depreciation_date_to and curr_depr.depreciation_date_to >= smallest \
									and curr_depr.depreciation_date_to <= largest:
									flag = False
									break
			if flag is False:
				return False
			return True

	_columns = {
		'asset_location_id': fields.related('asset_id', 'property_stock_asset', relation='stock.location', type='many2one', string='Asset Location', store=True, readonly=True),
		'barcode_no': fields.related('asset_id', 'barcode_no', type='char', string='Barcode No', store=True, readonly=True),
		'capacity_type': fields.selection([('hours','No of Hours'), ('units', 'No of Units')], 'Installed Capacity'),
		'total_hours': fields.float('No of Hours'),
		'total_units': fields.integer('No of Units'),
		'method_number_copy':fields.integer('Number of Depreciations'),
	}

	_constraints = [(check_depreciation_period, 'An Asset Cannot be downgraded more than once in the same period.', ['depreciation_line_ids'])]

	def onchange_asset(self, cr, uid, ids, asset, context=None):
		asset = self.pool.get('asset.asset').browse(cr, uid, asset, context=context)
		return {'value': {	'name': asset.name, 
							'barcode_no': asset.barcode_no, 
							'category_id': asset.account_asset_category_id and asset.account_asset_category_id.id or False,
							'asset_location_id': asset.property_stock_asset and asset.property_stock_asset.id or False
						}
				}

	def onchange_category_id(self, cr, uid, ids, category_id, context=None):
		res = {'value':{}}
		asset_categ_obj = self.pool.get('account.asset.category')
		if category_id:
			category_obj = asset_categ_obj.browse(cr, uid, category_id, context=context)
			res['value'] = {
                            'method': category_obj.method,
                            'method_number': category_obj.method_number,
                            'method_number_copy': category_obj.method_number_copy,
                            'method_time': category_obj.method_time,
                            'method_period': category_obj.method_period,
                            'method_progress_factor': category_obj.method_progress_factor,
                            'method_end': category_obj.method_end,
                            'prorata': category_obj.prorata,
            }
		return res


	def validate(self, cr, uid, ids, context=None):
		for asset in self.browse(cr, uid, ids):
			for l in asset.depreciation_line_ids:
				if l.depreciation_date and l.depreciation_date < asset.purchase_date:
					raise osv.except_osv(('Validation Error!'), ("Depreciation Start Date must be greater than Asset's Purchase Date"))
				if l.depreciation_date and l.depreciation_date_to and l.depreciation_date > l.depreciation_date_to:
					raise osv.except_osv(('Validation Error!'), ("Invalid Depreciation Date Range."))
		return super(account_asset, self).validate(cr, uid, ids, context)

	def _compute_board_undone_dotation_nb(self, cr, uid, asset, depreciation_date, total_days, context=None):
		undone_dotation_number = asset.method_number
		if asset.method_time == 'end':
			end_date = datetime.strptime(asset.method_end, '%Y-%m-%d')
			undone_dotation_number = 0
			while depreciation_date <= end_date:
				depreciation_date = (datetime(depreciation_date.year, depreciation_date.month, depreciation_date.day) + relativedelta(months=+asset.method_period))
				undone_dotation_number += 1
		if asset.prorata:
			undone_dotation_number += 1
		return undone_dotation_number

	def _compute_board_amount(self, cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=None):
		#by default amount = 0
		amount = 0
		if i == undone_dotation_number:
			amount = residual_amount
		else:
			if asset.method == 'linear':
				amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
				if asset.prorata:
					amount = amount_to_depr / asset.method_number
					days = total_days - float(depreciation_date.strftime('%j'))
					if i == 1:
						amount = (amount_to_depr / asset.method_number) / total_days * days
					elif i == undone_dotation_number:
						amount = (amount_to_depr / asset.method_number) / total_days * (total_days - days)
			elif asset.method == 'degressive':
				amount = residual_amount * asset.method_progress_factor
				if asset.prorata:
					days = total_days - float(depreciation_date.strftime('%j'))
					if i == 1:
						amount = (residual_amount * asset.method_progress_factor) / total_days * days
					elif i == undone_dotation_number:
						amount = (residual_amount * asset.method_progress_factor) / total_days * (total_days - days)
		return amount

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
				depreciation_lin_obj = self.pool.get('account.asset.depreciation.line')
				currency_obj = self.pool.get('res.currency')
				for asset in self.browse(cr, uid, ids, context=context):
					if asset.value_residual == 0.0:
						continue
					posted_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_check', '=', True)],order='depreciation_date desc')
					old_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_id', '=', False)])
					if old_depreciation_line_ids:
						depreciation_lin_obj.unlink(cr, uid, old_depreciation_line_ids, context=context)

					amount_to_depr = residual_amount = asset.value_residual
					if asset.prorata:
						depreciation_date = datetime.strptime(self._get_last_depreciation_date(cr, uid, [asset.id], context)[asset.id], '%Y-%m-%d')
					else:
						# depreciation_date = 1st January of purchase year
						purchase_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d')
						#if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
						if (len(posted_depreciation_line_ids)>0):
							last_depreciation_date = datetime.strptime(depreciation_lin_obj.browse(cr,uid,posted_depreciation_line_ids[0],context=context).depreciation_date, '%Y-%m-%d')
							depreciation_date = (last_depreciation_date+relativedelta(months=+asset.method_period))
						else:
							depreciation_date = datetime(purchase_date.year, purchase_date.month, purchase_date.day)
					day = depreciation_date.day
					month = depreciation_date.month
					year = depreciation_date.year
					total_days = (year % 4) and 365 or 366

					undone_dotation_number = self._compute_board_undone_dotation_nb(cr, uid, asset, depreciation_date, total_days, context=context)
					for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
						i = x + 1
						amount = self._compute_board_amount(cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=context)
						company_currency = asset.company_id.currency_id.id
						current_currency = asset.currency_id.id
						# compute amount into company currency
						amount = currency_obj.compute(cr, uid, current_currency, company_currency, amount, context=context)
						residual_amount -= amount
						vals = {
							 'amount': amount,
							 'asset_id': asset.id,
							 'sequence': i,
							 'name': str(asset.id) +'/' + str(i),
							 'remaining_value': residual_amount,
							 'depreciated_value': (asset.purchase_value - asset.salvage_value) - (residual_amount + amount),
							 'depreciation_date': depreciation_date.strftime('%Y-%m-%d'),
						}
						depreciation_lin_obj.create(cr, uid, vals, context=context)
						# Considering Depr. Period as months
						depreciation_date = (datetime(year, month, day) + relativedelta(months=+asset.method_period))
						day = depreciation_date.day
						month = depreciation_date.month
						year = depreciation_date.year
				return True

	def print_entries(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			asset_id = rec.asset_id.id
			location_id = rec.asset_id.property_stock_asset.id
			ttype = 'hospital'
			if rec.asset_id.property_stock_asset.location_id:
				ttype = 'service'
			entry_id = self.pool.get('asset.depreciation.map.report').create(cr, uid, {
										'asset_ref': asset_id,
										'type': ttype,
										str(ttype)+'_location_id': location_id,
			})
			return self.pool.get('asset.depreciation.map.report').print_report(cr, uid, [entry_id], context={'asset': True, 'asset_id': rec.id})

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

class account_asset_history(osv.osv):
	_inherit = 'account.asset.history'
	_order = "id asc"

	_columns = {
		'total_hours': fields.float('No of Hours'),
		'total_units': fields.integer('No of Units'),
	}
