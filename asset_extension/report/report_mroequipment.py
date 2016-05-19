import time

from openerp.report import report_sxw
from openerp.osv import osv
from datetime import date,datetime

class mro_hcv_equipment(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(mro_hcv_equipment, self).__init__(cr, uid, name, context=context)
 
        self.localcontext.update({
            'time': time,
            'getLines': self._lines_get,
            'getLineDetails': self._lines_getDetails,
            'getLineCount': self._lines_getCount,
        })
        self.context = context
    
    def _lines_get(self, date_from, date_to, equipment=False):
        cr=self.cr
        sql_where = ''
        if date_from:
           if sql_where:
               sql_where = sql_where + " and mro_order.date_execution >= date '%s'" %(date_from)
           else:
               sql_where = sql_where + " mro_order.date_execution >= date '%s'" %(date_from)
        if date_to:
           if sql_where:
               sql_where = sql_where + " and mro_order.date_execution <= date '%s'" % (date_to)
           else:
               sql_where = sql_where + " mro_order.date_execution <= date '%s'" % (date_to)
        if equipment:
           if sql_where:
               sql_where = sql_where + " and asset_id=%s" %(equipment.id)
           else:
               sql_where = sql_where + " asset_id=%s" %(equipment.id)
        else:
           if sql_where:
               sql_where = sql_where + " and asset_id is not null"
           else:
               sql_where = sql_where + " asset_id is not null"

        if sql_where:
            query = ''' select id from mro_order where %s '''%(sql_where)
        else:
            query = ''' select id from mro_order'''

        self.cr.execute(query)
        lines_ids=[]
        for data in self.cr.dictfetchall():
                lines_ids.append(data['id'])
        lines = {}
        mro_ids = self.pool.get('mro.order').search(self.cr, self.uid, [('id','in',lines_ids)], order='asset_id')
        for l in self.pool.get('mro.order').browse(self.cr, self.uid, mro_ids):
            if l.asset_id not in lines.keys():
                lines[l.asset_id] = []
        for l in self.pool.get('mro.order').browse(self.cr, self.uid, mro_ids):
            lines[l.asset_id].append(l)
        return lines

    def _lines_getDetails(self, date_from, date_to, equipment=False):
        lines = self._lines_get(date_from, date_to, equipment)
        result = []
        if equipment: 
            result = lines[equipment]
        return result

    def _lines_getCount(self, date_from, date_to, equipment=False):
        lines = self._lines_get(date_from, date_to, equipment)
        result = 0
        if equipment: 
            result = len(lines[equipment])
        return result

     
class report_mroequipment(osv.AbstractModel):
    _name = 'report.asset_extension.report_mroequipment'
    _inherit = 'report.abstract_report'
    _template = 'asset_extension.report_mroequipment'
    _wrapped_report_class = mro_hcv_equipment

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
