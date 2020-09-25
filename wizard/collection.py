from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class CollectAmount(models.TransientModel):
    _name = 'collect.amount'
    _description = 'Collect Amount Wizard'

    member_id = fields.Many2one(comodel_name="members.ranchy", string="", related="loan_id.member_id", required=False, )
    member_name = fields.Char(string="Member", related="member_id.name")
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True, )
    co_id = fields.Many2one(related="member_id.group_id.co_id", string="Credit Officer", readonly=True, )
    scheduled_amount = fields.Float(string="Scheduled Loan Amount", related="loan_id.installment_amount",  required=False, )
    collected_amount = fields.Float(string="Collected Amount Loan", required=False, )
    collected_savings = fields.Float(string="Collected Amount Saving", required=False, )
    collected_by = fields.Many2one(string="Collected By", required=False, )
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Active Loan", required=False)
    linked_schedule_ids = fields.Many2many(comodel_name="schedule.installments", relation="", column1="", column2="",
                                           string="Linked Scheduled Installments", required=True, )
    current_user = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)
    no_installments = fields.Integer(string="Number of Installments Paid", required=False, default=1,)
    collected_total = fields.Integer(string="Total Collected", compute="_total_collected", )
    date = fields.Date(string="Date", required=False, default=date.today())
    collection_id = fields.Many2one('collection.ranchy', invisible=1)
    installment_limit = fields.Integer(string="", compute="_limit")

    def _limit(self):
        self.installment_limit = self.collected_amount / self.scheduled_amount

    def _check_limit(self):
        new_list = []
        for obj in self:
            if obj.installment_limit <= 0:
                return False
            for field in obj.linked_schedule_ids:
                new_list.append(field.id)
            if obj.installment_limit != len(new_list):
                return False
        return True

    def _multiple(self):
        # m = self.collected_amount
        # n = self.scheduled_amount
        return True if self.collected_amount % self.scheduled_amount == 0 else False

    _constraints = [
        (_check_limit, 'Please check that you have linked the correct amount of scheduled installments',
         ['installment_limit', 'linked_schedule_ids']),
        (_multiple, 'Loan Amount Collected must be in Multiples of Scheduled Installment',
         ['installment_limit', 'linked_schedule_ids']),
    ]





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
        collection = self.env['collection.ranchy'].create({
            'member': self.member_id.id,
            'loan_id': self.loan_id.id,
            'collect_loan': self.collected_amount,
            'collect_savings': self.collected_savings,
            'no_installments': self.no_installments,
            'linked_installments_ids': [(6,  0, self.linked_schedule_ids.ids)],
            'state': 'collected',
            'date': self.date,
        })

        self.collection_id = collection
        payment = self.env['payments.ranchy']
        payment_detail = {
            'loan_id': self.loan_id.id,
            'amount': self.collected_amount,
            'date': date.today(),
            'collection_id': self.collection_id.id,
        }
        payment.create(payment_detail)
        for installment in self.linked_schedule_ids:
            installment.state = 'paid'


class WithdrawAmount(models.TransientModel):
    _name = 'withdraw.amount'
    _description = 'Withdraw Amount Wizard'

    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False, )
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True, )
    co_id = fields.Many2one(related="member_id.group_id.co_id", string="Credit Officer", readonly=True, )
    amount = fields.Float(string="Amount",  required=False, )
    balance = fields.Float(string="Balance", related="member_id.balance", )
    date = fields.Date(string="Date", required=False, default=date.today())
    request_id = fields.Many2one(comodel_name="withdraw.request", string="Ref Request", required=False,)

    @api.one
    @api.depends('')
    def withdraw_amount(self):
        withdrawal = self.env['withdrawals.ranchy']
        requestid = self.env['withdraw.request'].browse(self.request_id.id)
        vals = {
            'member_id': self.member_id.id,
            'amount': self.amount,
            'date': self.date,
        }
        withdrawal.create(vals)
        requestid.disburse_withdrawal()


class LapseAdjustments(models.TransientModel):
    _name = 'lapse.adjustment'
    _description = 'Lapse Adjustment Wizard'

    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False, )
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True, )
    co_id = fields.Many2one(related="member_id.group_id.co_id", string="Credit Officer", readonly=True, )
    amount = fields.Float(string="Adjustment Amount",  required=False, )
    balance = fields.Float(string=" Savings Balance", related="member_id.balance", )
    loan_id = fields.Many2one(string="Loan", comodel_name="loans.ranchy")
    loan_balance = fields.Integer(string="Loan Balance", related="loan_id.balance_loan")
    withdraw_able = fields.Float(string="Loan Balance", compute="_withdraw_able")
    difference = fields.Float(string="Difference", compute="_difference")
    date = fields.Date(string="Date", required=False, default=date.today())
    linked_schedule_ids = fields.Many2many(comodel_name="schedule.installments", relation="", column1="", column2="",
                                           string="Linked Scheduled Installments", )

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
    @api.depends('balance', 'loan_balance')
    def _difference(self):
        self.difference = self.balance - self.loan_balance

    @api.one
    @api.depends('amount')
    def _withdraw_able(self):
        self.withdraw_able = self.loan_balance - self.amount

    @api.one
    @api.depends('')
    def lapse_adjustment(self):
        withdrawal = self.env['withdrawals.ranchy']
        vals = {
            'member_id': self.member_id.id,
            'amount': self.withdraw_able,
            'date': self.date,
            'description': 'Lapse Adjustment',
        }
        withdrawal.create(vals)
        collection = self.env['collection.ranchy']
        linked =[]
        linked_env = self.env['schedule.installments'].search([('loan_id', '=', self.loan_id.id), ('state', '=', 'unpaid')])
        for link in linked_env:
            linked.append(link.id)
        values = {
            'member': self.member_id.id,
            'loan_id': self.loan_id.id,
            'collect_loan': self.loan_balance,
            'description': 'Lapse Adjustment',
            'state': 'collected',
            'date': self.date,
            'linked_installments_ids': [(6, 0, linked)],

        }
        collection.create(values)
        lapse_record = self.env['lapse.adjustment']
        records = {
            'member_id': self.member_id.id,
            'loan_id': self.loan_id.id,
            'amount': self.amount,
            'date': self.date,
        }
        lapse_record.create(records)


class CollectFees(models.TransientModel):
    _name = 'collect.fees'
    _description = 'Collect Loan Fees Wizard'

    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="", required=False, )
    date = fields.Date(string="Date", required=False, default=date.today())
    risk_premium = fields.Float(string="Risk Premium",  required=False, )
    amount = fields.Float(string="Collected Amount",  required=False, )
    admin_charge = fields.Float(string="Administrative Charge")

    @api.constrains('amount')
    def check_amount(self):
        for rec in self:
            if rec.amount != rec.risk_premium + rec.admin_charge:
                raise UserError(_("Amount collected must be equal to Risk Premium plus Admin Charge."))

    def collect_fees(self):
        collection = self.env['fees.collection']
        vals = {
            'amount': self.amount,
            'loan_id': self.loan_id.id,
            'risk_premium': self.risk_premium,
            'admin_charge': self.admin_charge,

        }
        collection.create(vals)
        self.loan_id.fees_collected = True


class DisburseWiz(models.TransientModel):
    _name = 'disburse.wiz'
    _rec_name = 'name'
    _description = 'Disbursement Wizard'

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan")
    disbursed_amount = fields.Float(string="Disbursed Amount", required=False, related="loan_id.amount_approved")
    mode = fields.Selection(string="Mode of Disburse", selection=[('cash', 'Cash'), ('cheque', 'Cheque'),
                                                                  ('transfer', 'Transfer')], required=False, )
    mode_ref = fields.Char(string="Cheque / Ref", required=False, )
    date = fields.Date(string="Date", required=False, default=date.today())

    def disburse_loan(self):
        disbursement = self.env['disbursements.ranchi']
        vals = {
            'mode_ref': self.mode_ref,
            'loan_id': self.loan_id.id,
            'disbursed_amount': self.disbursed_amount,
            'mode': self.mode,

        }
        disbursement.create(vals)
        self.loan_id.change_state('disbursed')


