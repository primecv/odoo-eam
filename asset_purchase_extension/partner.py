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

class res_partner(osv.osv):
	_inherit = "res.partner"

	def _purchase_invoice_count(self, cr, uid, ids, field_name, arg, context=None):
		PurchaseOrder = self.pool['rfq.hcv']
		Invoice = self.pool['account.invoice']
		return {
			partner_id: {
                'rfq_order_count': PurchaseOrder.search_count(cr,uid, [('partner_id', 'child_of', partner_id)], context=context),
                'supplier_invoice_count': Invoice.search_count(cr,uid, [('partner_id', 'child_of', partner_id), ('type','=','in_invoice')], context=context)
            }
            for partner_id in ids
        }

	_columns = {
		'purchase_line_ids': fields.one2many('product.supplierinfo.hcv', 'partner_id', 'Products Supplied'),
        'rfq_order_count': fields.function(_purchase_invoice_count, string='# of Purchase Order', type='integer', multi="count"),
	}


class product_supplierinfo_hcv(osv.osv):
	_name = "product.supplierinfo.hcv"
	_description = "Products Supplied"
	_columns = {
		'partner_id': fields.many2one('res.partner', 'Supplier'),
		'product_id': fields.many2one('product.product', 'Product'),
		'name': fields.char('Product'),
		'price': fields.float('Price'),
		'delivery_date': fields.date('Delivery Date'),
		'delivery_time': fields.char('Delivery Time(in Days)'),
	}

