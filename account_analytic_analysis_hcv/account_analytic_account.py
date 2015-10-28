# -*- coding: utf-8 -*-
from openerp.osv import osv, fields

class account_analytic_account(osv.osv):
	_inherit = 'account.analytic.account'

	_columns = {
		'purchase': fields.boolean('Is Purchase?'),
	}
