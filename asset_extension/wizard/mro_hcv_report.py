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
		'asset_id': fields.many2one('asset.asset', 'Equipment (Optional)', help="If selected, Report will list Maintenance Orders for selected Equipment only."),
		'technician_id': fields.many2one('hr.employee', 'Technician (Optional)', help="If selected, Report will list Maintenance Orders for selected Technician only.")
	}

	_defaults = {
		'partner_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, [uid])[0].partner_id.id
	}

	def print_report(self, cr, uid, ids, context=None):
		for rec in self.browse(cr, uid, ids):
			if (rec.start_period and rec.end_period) and (rec.end_period < rec.start_period):
				raise osv.except_osv(('Alert!'),('End Date Must be greater than Start Date.'))
			if rec.type == 'scheduled':
				return self.pool['report'].get_action(cr, uid, ids, 'asset_extension.report_mroscheduled', context=context)
			if rec.type == 'period':
				return self.pool['report'].get_action(cr, uid, ids, 'asset_extension.report_mroperiod', context=context)
			if rec.type == 'technician':
				return self.pool['report'].get_action(cr, uid, ids, 'asset_extension.report_mrotechnician', context=context)
			if rec.type == 'equipment':
				return self.pool['report'].get_action(cr, uid, ids, 'asset_extension.report_mroequipment', context=context)
