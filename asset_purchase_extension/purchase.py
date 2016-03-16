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
from openerp.osv import fields, osv

class purchase_order(osv.osv):
	_inherit = "purchase.order"

	def init(self, cr):
		try:
			cr.execute('alter table purchase_order drop constraint purchase_order_name_uniq;')
		except:
			pass

	STATE_SELECTION = [
        ('draft', 'Draft PO'),
        ('sent', 'RFQ'),
        ('bid', 'Bid Received'),
		('bid_done', 'Done'),
        ('confirmed', 'Waiting Approval'),
        ('approved', 'Purchase Confirmed'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
	]

	_columns = {
		'state': fields.selection(STATE_SELECTION, 'Status', readonly=True,
                                  help="The status of the purchase order or the quotation request. "
                                       "A request for quotation is a purchase order in a 'Draft' status. "
                                       "Then the order has to be confirmed by the user, the status switch "
                                       "to 'Confirmed'. Then the supplier must confirm the order to change "
                                       "the status to 'Approved'. When the purchase order is paid and "
                                       "received, the status becomes 'Done'. If a cancel action occurs in "
                                       "the invoice or in the receipt of goods, the status becomes "
                                       "in exception.",
                                  select=True, copy=False),
		'po_id': fields.many2one('purchase.order', 'Purchase Order'),
		'rfq_hcv_id': fields.many2one('rfq.hcv', 'RFQ'),
	}

	def wkf_confirm_order(self, cr, uid, ids, context=None):
		default = {}
		if context and 'rfq' in context and context['rfq'] is True:
			for rec in self.browse(cr, uid, ids):
				default['name'] = rec.name
				bid_id = super(purchase_order, self).copy(cr, uid, ids[0], default, context)
				self.write(cr, uid, [bid_id], {'state': 'bid_done', 'po_id': ids[0]})
		res = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context)
		return res

	def print_quotation(self, cr, uid, ids, context=None):
		'''
		This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow
		'''
		assert len(ids) == 1, 'This option should only be used for a single id at a time'
		self.signal_workflow(cr, uid, ids, 'send_rfq')
		for rec in self.browse(cr, uid, ids):
			if rec.state == 'draft': 
				self.write(cr, uid, ids, {'state': 'sent'})
		return self.pool['report'].get_action(cr, uid, ids, 'purchase.report_purchasequotation', context=context)

class purchase_order_line(osv.osv):
	_inherit = "purchase.order.line"

	_columns = {
		'rfq_line_id': fields.many2one('rfq.suppliers.hcv', 'RFQ Line Id'),
	}
