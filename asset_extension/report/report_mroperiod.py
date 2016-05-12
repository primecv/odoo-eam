import time

from openerp.report import report_sxw
from openerp.osv import osv
from datetime import date,datetime

class mro_hcv_period(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(mro_hcv_period, self).__init__(cr, uid, name, context=context)
 
        self.localcontext.update({
            'time': time,
            'getLines': self._lines_get,
            'getTotal': self.gettotal,
        })
        self.context = context
    
    def _lines_get(self, date_from, date_to):
        cr=self.cr
        query=""" select id from mro_order
                        where mro_order.date_execution between date '%s' and date '%s'""" % (date_from, date_to)

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
        query=""" select id from mro_order
                        where mro_order.date_execution between date '%s' and date '%s'""" % (date_from, date_to)

        self.cr.execute(query)
        lines_ids=[]
        for data in self.cr.dictfetchall():
                lines_ids.append(data['id'])
        lines = []
        for l in self.pool.get('mro.order').browse(self.cr, self.uid, lines_ids):
           lines.append(l)
        return len(lines)

     
class report_mroperiod(osv.AbstractModel):
    _name = 'report.asset_extension.report_mroperiod'
    _inherit = 'report.abstract_report'
    _template = 'asset_extension.report_mroperiod'
    _wrapped_report_class = mro_hcv_period

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
