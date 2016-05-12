#-*- coding:utf-8 -*-
######################################
#    By Prime Consulting, Cape Verde
######################################

from openerp.osv import osv, fields

class mro_hcv_report(osv.osv_memory):
	_name = "mro.hcv.report"

	_description = "Maintenance Reports"

	_columns = {
		'name': fields.char('Report Name'),	
		'type': fields.selection([('scheduled','Scheduled'),
									('period','By Period'),
									('technician', 'By Technician'),
									('equipment', 'By Equipment')], 'Report Type', required=True),

		'start_period': fields.date('Start Date'),
		'end_period': fields.date('End Date'),

		'partner_id': fields.many2one('res.partner', 'Partner'),

	}

	_defaults = {
		'partner_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, [uid])[0].partner_id.id
	}

	def print_report(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			if rec.type == 'period':
				return self.pool['report'].get_action(cr, uid, ids, 'asset_extension.report_mroperiod', context=context)
			if rec.type == 'scheduled':
				return self.pool['report'].get_action(cr, uid, ids, 'sale.report_saleorder', context=context)
			if rec.type == 'technician':
				return self.pool['report'].get_action(cr, uid, ids, 'sale.report_saleorder', context=context)
			if rec.type == 'equipment':
				return self.pool['report'].get_action(cr, uid, ids, 'sale.report_saleorder', context=context)
