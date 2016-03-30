from openerp.osv import osv, fields

class res_partner(osv.osv):
	_inherit = "res.partner"

	def _journal_item_count(self, cr, uid, ids, field_name, arg, context=None):
		""" Override function from account module's partner.py
		Show count of Contracts correctly ie. count of partner's analytic accounts of type 'contract'
		"""
		MoveLine = self.pool('account.move.line')
		AnalyticAccount = self.pool('account.analytic.account')
		return {
            partner_id: {
                'journal_item_count': MoveLine.search_count(cr, uid, [('partner_id', '=', partner_id)], context=context),
                'contracts_count': AnalyticAccount.search_count(cr,uid, [('partner_id', '=', partner_id),('type','=','contract')], context=context)
            }
            for partner_id in ids
        }

	_columns = {
        'contracts_count': fields.function(_journal_item_count, string="Contracts", type='integer', multi="invoice_journal"),
        'journal_item_count': fields.function(_journal_item_count, string="Journal Items", type="integer", multi="invoice_journal"),
	}
