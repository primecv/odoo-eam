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

	def create(self, cr, uid, vals, context=None):
		res = super(stock_move, self).create(cr, uid, vals, context)
		if context and 'hcv' in context and context['hcv'] is True:
			self.pool.get('registration.request.hcv').write(cr, uid,[context['register_id']],{'move_id': res, 'state':'transfer'})
		return res

