import time

from openerp.report import report_sxw
from openerp.osv import osv
from datetime import date,datetime

class mro_hcv_scheduled(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(mro_hcv_scheduled, self).__init__(cr, uid, name, context=context)
 
        self.localcontext.update({
            'time': time,
            'getLines': self._lines_get,
            'getTotal': self.gettotal,
        })
        self.context = context
    
    def _lines_get(self, date_from, date_to):
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

        if sql_where:
            query = """ select id from mro_order where %s and type='Preventive' and state='draft'"""%(sql_where)
        else:
            query = """ select id from mro_order where type='Preventive' and state='draft' """

        self.cr.execute(query)
        lines_ids=[]
        for data in self.cr.dictfetchall():
                lines_ids.append(data['id'])
        lines = []
        for l in self.pool.get('mro.order').browse(self.cr, self.uid, lines_ids):
           lines.append(l)
        return lines

    def gettotal(self, date_from, date_to):
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

        if sql_where:
            query = """ select id from mro_order where %s and type='Preventive' and state='draft'"""%(sql_where)
        else:
            query = """ select id from mro_order where type='Preventive' and state='draft' """

        self.cr.execute(query)
        lines_ids=[]
        for data in self.cr.dictfetchall():
                lines_ids.append(data['id'])
        lines = []
        for l in self.pool.get('mro.order').browse(self.cr, self.uid, lines_ids):
           lines.append(l)
        return len(lines)

     
class report_mroperiod(osv.AbstractModel):
    _name = 'report.asset_extension.report_mroscheduled'
    _inherit = 'report.abstract_report'
    _template = 'asset_extension.report_mroscheduled'
    _wrapped_report_class = mro_hcv_scheduled

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
