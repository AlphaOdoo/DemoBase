from odoo import models, fields, api
from odoo.exceptions import UserError, Warning, ValidationError

class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"
    _description = "Account move reversal inherit"

    cancellation_reason_id = fields.Many2one('cancellation_reasons', string='Cancellation Reason')
    
    def get_invoice_type(self):
        self.inv_type = self._context.get('inv_type')
    inv_type = fields.Boolean(compute="get_invoice_type")

    def reverse_moves(self):
        ##TODO mandar datos y recibir opcionales en "invoice cancellation":
        print(str(self._context))
        if self._context.get('inv_type'):
            if not self.cancellation_reason_id:
                raise Warning("You must select a cancellation reason, in order to send it to SIN")
        super(AccountMoveReversal, self).reverse_moves()
        # self.env['account.move'].send_email(self.cancellation_reason_id.code, self._context.get('cuf'),
        #                                     self._context.get('inv_number'), self._context.get('email_to'))
        self.env['account.move'].invoice_cancellation(self._context.get('inv_type'),
                                                    self._context.get('cufd'),
                                                    self._context.get('cuf'), 
                                                    self._context.get('inv_number'), 
                                                    self._context.get('account_move_id'), 
                                                    self._context.get('invoice_dosage_id'),
                                                    self.cancellation_reason_id.code,
                                                    self._context.get('email_to'))

