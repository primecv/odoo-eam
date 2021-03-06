import time

from openerp.report import report_sxw
from openerp.osv import osv
from datetime import date,datetime

class mro_hcv_technician(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(mro_hcv_technician, self).__init__(cr, uid, name, context=context)
 
        self.localcontext.update({
            'time': time,
            'getLines': self._lines_get,
            'getLineDetails': self._lines_getDetails,
            'getLineCount': self._lines_getCount,
            'getTotal': self.gettotal,
        })
        self.context = context
    
    def _lines_get(self, date_from, date_to, technician=False):
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
        if technician:
           if sql_where:
               sql_where = sql_where + " and technician_ref=%s" %(technician.id)
           else:
               sql_where = sql_where + " technician_ref=%s" %(technician.id)
        else:
           if sql_where:
               sql_where = sql_where + " and technician_ref is not null"
           else:
               sql_where = sql_where + " technician_ref is not null"

        if sql_where:
            query = ''' select id from mro_order where %s '''%(sql_where)
        else:
            query = ''' select id from mro_order'''

        '''if date_from and date_to:
            query=""" select id from mro_order
                        where mro_order.date_execution between date '%s' and date '%s'""" % (date_from, date_to)
        if date_from and not date_to:
            query=""" select id from mro_order
                        where mro_order.date_execution >= date '%s'""" % (date_from)
        if not date_from and date_to:
            query=""" select id from mro_order
                        where mro_order.date_execution <= date '%s'""" % (date_to)
        if not date_from and not date_to:
            query=""" select id from mro_order"""'''

        self.cr.execute(query)
        lines_ids=[]
        for data in self.cr.dictfetchall():
                lines_ids.append(data['id'])
        lines = {}
        ltech_ids = self.pool.get('mro.order').search(self.cr, self.uid, [('id','in',lines_ids)], order='technician_ref')
        for l in self.pool.get('mro.order').browse(self.cr, self.uid, ltech_ids):
            if l.technician_ref not in lines.keys():
                lines[l.technician_ref] = []
        for l in self.pool.get('mro.order').browse(self.cr, self.uid, ltech_ids):
            lines[l.technician_ref].append(l)
        return lines

    def _lines_getDetails(self, date_from, date_to, tech=False):
        lines = self._lines_get(date_from, date_to, tech)
        result = []
        if tech: 
            result = lines[tech]
        return result

    def _lines_getCount(self, date_from, date_to, tech=False):
        lines = self._lines_get(date_from, date_to, tech)
        result = 0
        if tech: 
            result = len(lines[tech])
        return result

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

     
class report_mrotechnician(osv.AbstractModel):
    _name = 'report.asset_extension.report_mrotechnician'
    _inherit = 'report.abstract_report'
    _template = 'asset_extension.report_mrotechnician'
    _wrapped_report_class = mro_hcv_technician

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
