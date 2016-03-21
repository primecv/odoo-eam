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

class stock_move(osv.osv):
	_inherit = "stock.move"

	_columns = {
        'product_uom_qty': fields.integer('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
            required=True, states={'done': [('readonly', True)]},
            help="This is the quantity of products from an inventory "
                "point of view. For moves in the state 'done', this is the "
                "quantity of products that were actually moved. For other "
                "moves, this is the quantity of product that is planned to "
                "be moved. Lowering this quantity does not generate a "
                "backorder. Changing this quantity on assigned moves affects "
                "the product reservation, and should be done with care."
        ),
	}
	def create(self, cr, uid, vals, context=None):
		res = super(stock_move, self).create(cr, uid, vals, context)
		if context and 'hcv' in context and context['hcv'] is True:
			self.pool.get('registration.request.hcv').write(cr, uid,[context['register_id']],{'move_id': res, 'state':'transfer'})
		return res

	def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False, loc_dest_id=False, partner_id=False):
		if not prod_id:
			return {}
		user = self.pool.get('res.users').browse(cr, uid, uid)
		lang = user and user.lang or False
		if partner_id:
			addr_rec = self.pool.get('res.partner').browse(cr, uid, partner_id)
			if addr_rec:
				lang = addr_rec and addr_rec.lang or False
		ctx = {'lang': lang}

		product = self.pool.get('product.product').browse(cr, uid, [prod_id], context=ctx)[0]
		uos_id = product.uos_id and product.uos_id.id or False
		result = {
            'name': product.partner_ref,
            'product_uom': product.uom_id.id,
            'product_uos': uos_id,
        }
		if loc_id:
			result['location_id'] = loc_id
		return {'value': result}

	def get_rr_ref(self, cr, uid, ids):
		rr_id = False
		for rec in self.browse(cr, uid, ids):
			origin = rec.origin
			if origin:
				rr_id = self.pool.get('registration.request.hcv').search(cr, uid, [('name','=',origin)])
		return rr_id

	def action_done(self, cr, uid, ids, context=None):
		res = super(stock_move, self).action_done(cr, uid, ids, context)
		rr_id = self.get_rr_ref(cr, uid, ids)
		if rr_id:
			self.pool.get('registration.request.hcv').write(cr, uid, rr_id, {'state': 'transfer_done'})
		return res

	def action_cancel(self, cr, uid, ids, context=None):
		res = super(stock_move, self).action_cancel(cr, uid, ids, context)
		rr_id = self.get_rr_ref(cr, uid, ids)
		if rr_id:
			self.pool.get('registration.request.hcv').write(cr, uid, rr_id, {'state': 'transfer_cancel'})
		return res

