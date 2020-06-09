# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class LoansRanchy(models.Model):
    _name = 'loans.ranchy'
    _rec_name = 'loan_no'
    _description = 'Tables for loans'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    type = fields.Many2one(comodel_name="loantype.ranchy", string="Loan Type", required=False, )
    app_date = fields.Date(string="Date of Application", required=False, )
    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False, )
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True,)
    avg_monthly = fields.Float(string="Average Monthly Income",  required=False, )
    last_loan = fields.Float(string="Last Loan Received", required=False, )
    date_fullypaid = fields.Date(string="Date Last Loan was Fully Paid", required=False)
    amount_apply = fields.Float(string="Amount Applied For(principal)", required=False)
    amount_approved = fields.Float(string="Amount Approved", required=False)
    no_install = fields.Float(string="Number of Installments", required=False)
    duration = fields.Char(string="Loan Duration", required=False)
    date_first = fields.Date(string="Date First Installment is Due", required=False)
    date_last = fields.Date(string="Date Last Installment is Due", required=False)
    is_family = fields.Boolean(string="Any family member registered in the group",  )
    name_family = fields.Char(string="Name of Family Member")
    savings_balance = fields.Float(string="Savings Balance")
    is_indebted = fields.Boolean(string="Are You Indebted to any MFB/MFI",  )
    indebted_amount = fields.Float(string="Indebted Amount")
    indebted_mfb = fields.Char(string="MFB/MFI Name")
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('applied', 'Applied'),
                                                         ('approved', 'Approved'),
                                                         ('disbursed', 'Disbursed / Payment ongoing'),
                                                         ('paid', 'Fully Paid'), ('cancel', 'Canceled')],
                             required=False, default='draft')
    schedule_installments_ids = fields.One2many(comodel_name="schedule.installments", inverse_name="loan_id",
                                                string="Schedule Installments", required=False, )
    payment_ids = fields.One2many(comodel_name="payments.ranchy", inverse_name="loan_id", string="Payments",
                                  required=False, )
    guarantor_name = fields.Char(string="Guarantor Name", required=False)
    relationship = fields.Char(string="Relationship with Borrower", required=False, )
    guarantor_home = fields.Text(string="Guarantor Home Address", required=False)
    guarantor_office = fields.Text(string="Guarantor Office Address", required=False)
    guarantor_phone = fields.Char(string="Guarantors Phone", required=False)
    loan_no = fields.Char(string="Loan Number", default=lambda self: _('New'),
                          requires=False, readonly=True, trace_visibility='onchange', )

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'applied'),
                   ('applied', 'approved'),
                   ('applied', 'cancel'),
                   ('approved', 'disbursed'),
                   ('disbursed', 'paid'),

                   ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for loan in self:
            if loan.is_allowed_transition(loan.state, new_state):
                loan.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (loan.state, new_state)
                raise UserError(msg)

    @api.multi
    def apply_loan(self):
        self.change_state('applied')

    @api.multi
    def approve_loan(self):
        self.change_state('approved')

    @api.multi
    def disburse_loan(self):
        self.change_state('disbursed')

    @api.multi
    def reject(self):
        self.change_state('cancel')

    @api.model
    def create(self, vals):
        if vals.get('loan_no', _('New')) == _('New'):
            vals['loan_no'] = self.env['ir.sequence'].next_by_code('increment_loan') or _('New')
        result = super(LoansRanchy, self).create(vals)
        return result


class UnionRanchy(models.Model):
    _name = 'union.ranchy'
    _rec_name = 'name'
    _description = 'Table of Unions'

    name = fields.Char()
    members_ids = fields.One2many(comodel_name="members.ranchy", inverse_name="group_id", string="Union Members", required=False, )
    co_id = fields.Many2one(comodel_name="hr.employee", string="Credit Officer", required=False, )
    description = fields.Text(string="Union Description", required=False, )


class DisbursmentRanchy(models.Model):
    _name = 'disbursment.ranchy'
    _rec_name = 'name'
    _description = 'Disbursments'

    name = fields.Char()


class MembersRanchy(models.Model):
    _name = 'members.ranchy'
    _rec_name = 'name'
    _description = 'members'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    first_name = fields.Char(string="First Name", required=False, )
    surname = fields.Char(string="Surname", required=False, )
    r_address = fields.Char(string="Residential Address", required=False, )
    b_address = fields.Char(string="Business Address", required=False,)
    p_address = fields.Char(string="Permanent Address", required=False,)
    phone = fields.Char(string="Phone Number", required=False,)
    dob = fields.Date(string="Date of Birth", required=False, )
    marital_status = fields.Selection(string="Marital Status", selection=[('single', 'Single'), ('married', 'Married'),
                                                                          ('divorced', 'Divorced'), ('widow', 'Widow'),
                                                                          ], required=False, )
    formal_edu = fields.Selection(string="Formal Education", selection=[('none', 'None'), ('primary', 'Primary'),
                                                                        ('secondary', 'Secondary'),
                                                                        ('tertiary', 'Tertiary'), ], required=False)
    nok = fields.Char(string="next of Kin", required=False)
    nok_phone = fields.Char(string="NOK Phone", required=False)
    group_id = fields.Many2one(comodel_name="union.ranchy", string="Union/Group", required=False, )
    m_photo = fields.Binary(string="",  )
    saving_ids = fields.One2many(comodel_name="savings.ranchy", inverse_name="member_id", string="Savings", required=False, )
    withdrawal_ids = fields.One2many(comodel_name="withdrawals.ranchy", inverse_name="member_id", string="Withdrawals",
                                 required=False, )
    loan_ids = fields.One2many(comodel_name="loans.ranchy", inverse_name="member_id", string="Loans",
                                 required=False, )
    active = fields.Boolean(string="Active", default=True)
    loan_count = fields.Integer(string="Loans", compute= 'get_loan_count', )
    saving_total = fields.Float(string="saving total", compute='_saving_total')
    withdrawal_total = fields.Float(string="withdrawal total", compute='_withdrawal_total')
    balance = fields.Float(string="Savings Balance", compute='_balance')

    def get_loan_count(self):
        count = self.env['loans.ranchy'].search_count([('member_id', '=', self.id)])
        self.loan_count = count

    @api.one
    @api.depends('saving_ids.amount', )
    def _saving_total(self):
        self.saving_total = sum(saving_id.amount for saving_id in self.saving_ids)

    @api.one
    @api.depends('withdrawal_ids.amount', )
    def _withdrawal_total(self):
        self.withdrawal_total = sum(withdrawal_id.amount for withdrawal_id in self.withdrawal_ids)

    def _balance(self):
        self.balance = self.saving_total - self.withdrawal_total


class LoanType(models.Model):
    _name = 'loantype.ranchy'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
    principal_amount = fields.Float(string="Principal Amount",  required=True, )
    service_rate = fields.Float(string="Service Rate", required=True, )
    admin_charge = fields.Float(string="Administrative Charge", required=True)
    risk_premium = fields.Float(string="Risk Premium", required=True)
    no_installments = fields.Float(string="Number of Installments", required=True)


class Savings(models.Model):
    _name = 'savings.ranchy'
    _rec_name = 'name'
    _description = 'Savings Deposit'

    name = fields.Char()
    member_id = fields.Many2one(comodel_name="members.ranchy", string="Member", required=False, )
    date = fields.Date(string="Date", required=False, )
    amount = fields.Float(string="Amount", required=False, )


class Withdrawals(models.Model):
    _name = 'withdrawals.ranchy'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
    member_id = fields.Many2one(comodel_name="members.ranchy", string="Member", required=False, )
    date = fields.Date(string="Date", required=False, )
    amount = fields.Float(string="Amount", required=False, )


class ScheduleInstallments(models.Model):
    _name = 'schedule.installments'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan", required=False, )
    date = fields.Date(string="Schedule Date")
    installment = fields.Float(string="Installment Amount",  required=False, )
    state = fields.Selection(string="State", selection=[('paid', 'Paid'), ('unpaid', 'Unpaid'), ],
                             required=False, default='unpaid')


class LoanPayments(models.Model):
    _name = 'payments.ranchy'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan", required=False, )









