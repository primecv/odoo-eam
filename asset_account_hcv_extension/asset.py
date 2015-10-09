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
