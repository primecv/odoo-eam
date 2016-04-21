# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Prime Consulting (<http://prime.cv>).
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
from datetime import datetime
from datetime import date as dt
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class asset_asset(osv.osv):
	_inherit = "asset.asset"

	_columns = {
		'hours_of_operation': fields.float('Hours of Operation', readonly=True),
		'planned_amount': fields.float('Amounts of Planned Tests', readonly=True),
	}

	def create(self, cr, uid, vals, context=None):
		res = super(asset_asset, self).create(cr, uid, vals, context)
		if context and 'po_asset' in context and 'rfq_id' in context:
			#update Asset Value :
			self.write(cr, uid, [res], {'asset_value': context['price_unit']})
			#add item in Supplier's Product Supplied Tab :
			purchase_date = 'purchase_date' in vals and vals['purchase_date'] or False
			self.pool.get('product.supplierinfo.hcv').create(cr, uid, {
																		'name': vals['name'],
																		'price': context['price_unit'],
																		'delivery_date': purchase_date,
																		'partner_id': context['default_vendor_id'],
																	})
			if context['default_is_accessory'] is True:
				self.pool.get('rfq.hcv').write(cr, uid, [context['rfq_id']], {'create_accessory': False, 
																			'new_accessory_id': res,
																			'state': 'done'
																		})
			elif context['default_is_accessory'] is False:
				self.pool.get('rfq.hcv').write(cr, uid, [context['rfq_id']], {'create_asset': False, 
																			'new_asset_id': res,
																			'state': 'done'
																		})
		return res

