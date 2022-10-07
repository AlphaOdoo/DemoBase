
from email.policy import default
from numpy import where
#from statistics import correlation
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError



class Asiento(models.Model):
    _inherit="account.move"

    origin = fields.Char(compute='_compute_origin',string='Origen', default='')
    correlative = fields.Char(string='Correlativo')
    

    # @api.onchange('corre')
    # def _onchange_correlativo(self):
    #     self.correlative = "J222"
    # def _get_name_grouped(self):
    #     vals= []
    #     name_grouped = self.read_group(
    #         [('id', 'in', self._ids)],
    #         [('create_date','=','self.create_date')],
    #         [('create_date')])
    #     vals[0]
    #     return name_grouped

    @api.onchange('correlative')
    def _obtain_name(self):
        acCode = self.env['account.move'].search(
            [('create_date', '=', self.create_date)])
        for item in acCode:
            self.name = str(item.name)
        return self.name


    def _rule_get(self):
        record = self.env['account_move_line'].search(
            [('create_date', '=', self.create_date)])
        return record


    def run_sql(self, qry):
        createdate = self.create_date
        where = ' create_date = ' + "'" + str(createdate) + \
            "'" 
            # + 'and am.create_date = aml.create_date'
        self._cr.execute(qry + where)
        _res = self._cr.dictfetchall()
        return _res

    # def aux_run_sql1(self):
    #     self.run_sql1('Select account_id, round(sum(debit),2) as debito, ' +
    #                 'round(sum(credit),2) as credito, round(sum(debit / 6.96),2) AS debitoSus, '+ 
    #                 'round(sum(credit / 6.96),2) as creditoSus '
    #                 'FROM account_move_line where ')
    def run_sql1(self, qry):
        createdate = self.create_date
        where = ' aml.create_date = ' + "'" + str(createdate) + \
            "'" 
        aux_to_where = qry + where
        group_by = ' group by aa.name, aa.code'
            # + 'and am.create_date = aml.create_date'
        self._cr.execute(qry + where + group_by)
        _res = self._cr.dictfetchall()
        return _res

    def run_sql2(self):
        qry = "select create_date, string_agg(name, ', ' )as name FROM account_move where "
        createdate = self.create_date
        where = 'create_date = ' + "'" + str(createdate) + \
            "'" 
        # aux_to_where = qry + where
        group_by = 'group by create_date'
        self._cr.execute(qry + str(where) + group_by)
        _res = self._cr.dictfetchall()
        return _res

    # def get_sql(self, qry):
    #     createdate = self.create_date
    #     where = ' am.create_date = ' + "'" + createdate + \
    #         "'" + 'and am.create_date = aml.create_date'
    #     lines = []
    #     sql_select = sql.SQL(
    #     """
    #     select am.name as Asiento,aj.name as Diario, am.date as FechaContable,
    #         rp.name Cliente, aml.name as Descripcion,aml.ref as Glosa, aa.name as NomCuenta,
    #         aml.account_id,aa.code as CodCuenta
    #     from account_move as am
    #         left join account_move_line as aml on  aml.move_id = am.id
    #         left join account_journal as aj on am.journal_id = aj.id
    #         left join account_account as aa on aa.id=aml.account_id
    #         left join res_partner as rp on am.partner_id = rp.id
    #     WHERE 
    
    #     """
    #         + where
    #     )

    #     self._cr.execute(sql_select)
    #     final_result = [i[0] for i in self._cr.fetchall()]
    #     return final_result




    def _compute_origin(self):
        if(self.ref):        
            proc= ""
            for c in range(len(self.ref)):
                if (self.ref[c] != '-'):
                    proc=proc+self.ref[c]
                else:
                    break
            self.origin=proc

   
    # def print_report(self):
    #     record = self.env['account.move'].search(
    #         [('origin', '=', self.origin)])
    #     print("prueba preuba preuba")
    #     for item in record:
    #         print(str(record))
    #     # datas = {
    #     #     'inv': self,
    #     #     'items': self.invoice_line_ids
    #     # }
    #     # self.generate_qr_code()

    #     return self.env.ref('l10n_bo_reports.accountentry_report').report_action(self)
            


    # @api.depends('correlative')
    # def _onchange_correlativo(self):
    #     # Busqueda por fecha de creacion
       
    #     for r in self:
    #         record = self.env['account.move'].search(
    #         [('create_date', '=', self.create_date)])
    #         r.create_date = record.create_date

    #     # #Busqueda por la misma referencia
    #     # record = self.env['account.move'].search(
    #     # [('origin', '=', self.origin)])
    
    # # 2022-06-00001

    #     sequence=int(r.correlative[8:13])
    #     initvalue = sequence

    #     initvalue1 = 1 #cambiar por el initvalue de arriba
    #     # Genera el año y el mes
    #     from datetime import datetime
    #     now = datetime.now()
    #     year = now.year
    #     month = now.month
    #     day = now.day
        
    #     # Genera sufijo autoincremental
    #     if day == 1:
    #         initvalue = 1

    #     if month == 1 and day == 1:
    #         initvalue = 5

        
    #     incrementedSufix = initvalue + 1
    #     prefixinitnum = '0'
    #     if incrementedSufix < 10:
    #         prefixnumber = prefixinitnum +'0000' 
    #         incrementedSufix = prefixnumber+str(incrementedSufix)
    #     if incrementedSufix in range(10,99):
    #         prefixnumber = prefixinitnum + '000' 
    #         incrementedSufix = prefixnumber+str(incrementedSufix)
    #     if incrementedSufix in range(100,999):
    #         prefixnumber = prefixinitnum + '00' 
    #         incrementedSufix = prefixnumber+str(incrementedSufix)
    #     if incrementedSufix in range(1000,9999):
    #         prefixnumber = prefixinitnum + '0' 
    #         incrementedSufix = prefixnumber+str(incrementedSufix)
    #     if incrementedSufix in range(10000,99999):
    #         prefixnumber = prefixinitnum 
    #         incrementedSufix = prefixnumber+str(incrementedSufix)
        
    #     numerator = year + '-' + month + incrementedSufix
    #     # self.correlative = numerator

    #     if r:
    #         self.correlative = r[0].correlative
    #     else:
    #         self.correlative = numerator 

