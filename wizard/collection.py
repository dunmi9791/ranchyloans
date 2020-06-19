from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class CollectAmount(models.TransientModel):
    _name = 'collect.amount'
    _description = 'Collect Amount Wizard'

    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False, )
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True, )
    co_id = fields.Many2one(related="member_id.group_id.co_id", string="Credit Officer", readonly=True, )
    scheduled_amount = fields.Float(string="Scheduled Loan Amount", related="loan_id.installment_amount",  required=False, )
    collected_amount = fields.Float(string="Collected Amount Loan", required=False, )
    collected_savings = fields.Float(string="Collected Amount Saving", required=False, )
    collected_by = fields.Many2one(string="Collected By", required=False, )
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Active Loan", required=False)
    linked_schedule_ids = fields.Many2many(comodel_name="schedule.installments", relation="", column1="", column2="",
                                           string="Linked Scheduled Installments", )
    current_user = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)
    no_installments = fields.Integer(string="Number of Installments Paid", required=False, default=1,)
    collected_total = fields.Integer(string="Total Collected", compute="_total_collected", )
    date = fields.Date(string="Date", required=False, default=date.today())

    @api.one
    @api.depends('collected_amount', 'collected_savings')
    def _total_collected(self):
        self.collected_total = self.collected_amount + self.collected_savings

    @api.onchange('member_id')
    def _onchange_member_id(self):
        if self.member_id:
            loan_ids = self.member_id.loan_ids.ids
            return {'domain': {'loan_id': [('id', 'in', loan_ids), ('state', '=', 'disbursed')]}}

    @api.onchange('loan_id')
    def _onchange_loan_id(self):
        if self.loan_id:
            schedule_ids = self.loan_id.schedule_installments_ids.ids
            return {'domain': {'linked_schedule_ids': [('id', 'in', schedule_ids), ('state', '=', 'unpaid')]}}

    @api.one
    @api.depends('')
    def collect_amount(self):
        collection = self.env['collection.ranchy']
        vals = {
            'member': self.member_id.id,
            'loan_id': self.loan_id.id,
            'collect_loan': self.collected_amount,
            'collect_savings': self.collected_savings,
            'no_installments': self.no_installments,
            'linked_installments_ids': [(6,  0, self.linked_schedule_ids.ids)],
            'state': 'collected',
            'date': self.date,
        }
        collection.create(vals)


class WithdrawAmount(models.TransientModel):
    _name = 'withdraw.amount'
    _description = 'Withdraw Amount Wizard'

    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False, )
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True, )
    co_id = fields.Many2one(related="member_id.group_id.co_id", string="Credit Officer", readonly=True, )
    amount = fields.Float(string="Amount",  required=False, )
    balance = fields.Float(string="Balance", related="member_id.balance", )
    date = fields.Date(string="Date", required=False, default=date.today())

    @api.one
    @api.depends('')
    def withdraw_amount(self):
        withdrawal = self.env['withdrawals.ranchy']
        vals = {
            'member_id': self.member_id.id,
            'amount': self.amount,
            'date': self.date,
        }
        withdrawal.create(vals)


class LapseAdjustments(models.TransientModel):
    _name = 'lapse.adjustment'
    _description = 'Lapse Adjustment Wizard'

    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False, )
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True, )
    co_id = fields.Many2one(related="member_id.group_id.co_id", string="Credit Officer", readonly=True, )
    amount = fields.Float(string="Adjustment Amount",  required=False, )
    balance = fields.Float(string=" Savings Balance", related="member_id.balance", )
    loan_balance = fields.Float(string="Loan Balance")

    @api.one
    @api.depends('')
    def lapse_adjustment(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        pass


