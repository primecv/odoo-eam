# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
import time
from lxml import etree

from openerp.osv import fields, osv

class asset_modify(osv.osv_memory):
    _inherit = 'asset.modify'

    _columns = {
        'method': fields.selection([('linear','Linear'),
                                    ('degressive', 'Degressive')], 'Type'),
		'capacity_type': fields.selection([('hours','No of Hours'), ('units', 'No of Units')], 'Installed Capacity'),
		'total_hours': fields.float('No of Hours'),
		'total_units': fields.integer('No of Units'),
        'name2': fields.char('Name'),
    }

    def default_get(self, cr, uid, fields, context=None):
        """ To get default values for the object.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for which we want default values 
        @param context: A standard dictionary 
        @return: A dictionary which of fields with values. 
        """ 
        if not context:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        res = super(asset_modify, self).default_get(cr, uid, fields, context=context)
        asset_id = context.get('active_id', False)
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        if 'name' in fields:
            res.update({'name': asset.name})
        if 'method_number' in fields and asset.method_time == 'number':
            res.update({'method_number': asset.method_number})
        if 'method_period' in fields:
            res.update({'method_period': asset.method_period})
        if 'method_end' in fields and asset.method_time == 'end':
            res.update({'method_end': asset.method_end})
        if context.get('active_id'):
            res['asset_method_time'] = self._get_asset_method_time(cr, uid, [0], 'asset_method_time', [], context=context)[0]
            asset = self.pool['account.asset.asset'].browse(cr, uid, context.get('active_id'), context=context)
            res['method'] = asset.method
            res['capacity_type'] = asset.capacity_type
            res['total_hours'] = asset.total_hours
            res['total_units'] = asset.total_units
            if asset.method == 'linear':
                res['method_number'] = asset.category_id.method_number_copy
                res['method_period'] = asset.category_id.method_period
        return res
    
    def modify(self, cr, uid, ids, context=None):
        """ Modifies the duration of asset for calculating depreciation
        and maintains the history of old values.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of Ids 
        @param context: A standard dictionary 
        @return: Close the wizard. 
        """ 
        if not context:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        history_obj = self.pool.get('account.asset.history')
        asset_id = context.get('active_id', False)
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        data = self.browse(cr, uid, ids[0], context=context)
        if data.method == 'linear': name = data.name 
        else: name = data.name2
        history_vals = {
            'asset_id': asset_id,
            'name': name,
            'method_time': asset.method_time,
            'method_number': data.method_number,
            'method_period': data.method_period,
            'method_end': asset.method_end,
            'user_id': uid,
            'date': time.strftime('%Y-%m-%d'),
            'note': data.note,
            'total_hours': data.total_hours,
            'total_units': data.total_units,
        }
        if data.method == 'degressive':
            history_vals['method_number'] = 0
            history_vals['method_period'] = 0
        history_obj.create(cr, uid, history_vals, context=context)
        asset_vals = {
            'method_number_copy': data.method_number,
            'method_number': data.method_number * 12,
            'method_period': data.method_period,
            'method_end': data.method_end,
        }
        if data.method == 'degressive':
            asset_vals['total_hours'] = data.total_hours
            asset_vals['total_units'] = data.total_units
        asset_obj.write(cr, uid, [asset_id], asset_vals, context=context)
        asset_obj.compute_depreciation_board(cr, uid, [asset_id], context=context)
        return {'type': 'ir.actions.act_window_close'}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
