#-*- coding:utf-8 -*-

import time
from openerp.osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class stock_history(osv.osv):
	_inherit = "stock.history"

	def _get_inventory_value(self, cr, uid, ids, name, attr, context=None):
		if context is None:
			context = {}
		date = context.get('history_date')
		product_tmpl_obj = self.pool.get("product.template")
		res = {}
		for line in self.browse(cr, uid, ids, context=context):
			if line.product_id.cost_method == 'real':
				res[line.id] = line.quantity * line.price_unit_on_quant
			else:
				res[line.id] = line.quantity * product_tmpl_obj.get_history_price(cr, uid, line.product_id.product_tmpl_id.id, line.company_id.id, date, context, line.source, line.product_id.id)
		return res

	_columns = {
		'inventory_value': fields.function(_get_inventory_value, string="Inventory Value", type='float', readonly=True),
	}


class product_template(osv.osv):
	_inherit = "product.template"

	def get_history_price(self, cr, uid, product_tmpl, company_id, date=None, context=None, source=None, product_id=None):
		if context is None:
			context = {}
		if date is None:
			date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		price_history_obj = self.pool.get('product.price.history')
		history_ids = price_history_obj.search(cr, uid, [('company_id', '=', company_id), ('product_template_id', '=', product_tmpl), ('datetime', '<=', date)], limit=1)
		cost = 0.0
		if source:
			po_ref = self.pool.get('purchase.order').search(cr, uid, [('name','=',source)])
			if po_ref:
				for po in self.pool.get('purchase.order').browse(cr, uid, po_ref):
					for line in po.order_line:
						if product_id == line.product_id.id:
							cost = line.price_unit
				return cost
		if history_ids:
			return price_history_obj.read(cr, uid, history_ids[0], ['cost'], context=context)['cost']
		return 0.0

