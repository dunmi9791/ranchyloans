# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from dateutil import relativedelta
from datetime import datetime
from datetime import date


class LoansRanchy(models.Model):
    _name = 'loans.ranchy'
    _rec_name = 'loan_no'
    _description = 'Tables for loans'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    type = fields.Many2one(comodel_name="loantype.ranchy", string="Loan Type", required=False, )
    app_date = fields.Date(string="Date of Application", required=False, )
    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False,
                                track_visibility=True, trace_visibility='onchange',)
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True,)
    avg_monthly = fields.Float(string="Average Monthly Income",  required=False, )
    last_loan = fields.Float(string="Last Loan Received", required=False, )
    date_fullypaid = fields.Date(string="Date Last Loan was Fully Paid", required=False)
    amount_apply = fields.Float(string="Amount Applied For(principal)", required=False,
                                track_visibility=True, trace_visibility='onchange',)
    amount_approved = fields.Float(string="Amount Approved", required=False,
                                   track_visibility=True, trace_visibility='onchange',)
    no_install = fields.Integer (string="Number of Installments", required=False)
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
                             required=False, default='draft', track_visibility=True, trace_visibility='onchange',)
    schedule_installments_ids = fields.One2many(comodel_name="schedule.installments", inverse_name="loan_id",
                                                string="Schedule Installments", required=False, )
    payment_ids = fields.One2many(comodel_name="payments.ranchy", inverse_name="loan_id", string="Payments",
                                  required=False, )
    guarantor_name = fields.Char(string="Guarantor Name", required=False,
                                 track_visibility=True, trace_visibility='onchange',)
    relationship = fields.Char(string="Relationship with Borrower", required=False, )
    guarantor_home = fields.Text(string="Guarantor Home Address", required=False,
                                 track_visibility=True, trace_visibility='onchange',)
    guarantor_office = fields.Text(string="Guarantor Office Address", required=False)
    guarantor_phone = fields.Char(string="Guarantors Phone", required=False,
                                  track_visibility=True, trace_visibility='onchange',)
    loan_no = fields.Char(string="Loan Number", default=lambda self: _('New'),
                          requires=False, readonly=True, trace_visibility='onchange', )
    interest = fields.Float(string="Service Charge", compute='_interest')
    payment_amount = fields.Float(string="Repayment Amount", compute='_repay_amount')
    installment_amount = fields.Float(string="Installment Amount", compute='_installment_amount')
    total_realisable = fields.Integer(string="Expected Realisation", compute='_total_realisable')
    total_realised = fields.Integer(string="Realised Total", compute='_total_realised')
    balance_loan = fields.Integer(string="Loan Balance", compute='_loan_balance', )

    @api.one
    @api.depends('schedule_installments_ids.installment', )
    def _total_realisable(self):

        self.total_realisable = sum(schedule.installment for schedule in self.schedule_installments_ids)

    @api.one
    @api.depends('schedule_installments_ids.installment', )
    def _total_realised(self):

        self.total_realised = sum(paid.installment
                                  for paid in self.schedule_installments_ids.filtered(lambda o: o.state == 'paid'))

    @api.one
    @api.depends('amount_approved')
    def _interest(self):
        self.interest = self.amount_approved * 0.15

    @api.one
    @api.depends('interest')
    def _repay_amount(self):
        self.payment_amount = self.amount_approved + self.interest

    @api.one
    @api.depends('payment_amount')
    def _installment_amount(self):
        self.installment_amount = self.payment_amount / self.no_install

    @api.one
    @api.depends('payment_amount')
    def _loan_balance(self):
        self.balance_loan = self.payment_amount - self.total_realised

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

    @api.model
    def _compute_flat(self, loan_amount, period, first_payment_date):
        result = []

        installment_amount = loan_amount / period
        first_date = first_payment_date.strftime("%m-%d-%Y")
        next_payment_date = datetime.strptime(first_date,
                                              "%m-%d-%Y")
        for loan_period in range(1, period + 1):
            res = {
                "date": next_payment_date.strftime("%m-%d-%Y"),
                "installment": installment_amount,

            }
            result.append(res)
            next_payment_date = next_payment_date + \
                                relativedelta.relativedelta(
                                    weeks=+1)
        return result

    @api.multi
    def _compute_payment(self):
        self.ensure_one()

        obj_loan_type = self.env["loans.ranchy"]
        obj_payment = self.env["schedule.installments"]

        payment_datas = obj_loan_type._compute_flat(
            self.payment_amount,
            self.no_install,
            self.date_first,)

        for payment_data in payment_datas:
            payment_data.update({"loan_id": self.id})
            obj_payment.create(payment_data)

    @api.multi
    def compute_schedule(self):
        for loan in self:
            loan._compute_payment()


class UnionRanchy(models.Model):
    _name = 'union.ranchy'
    _rec_name = 'name'
    _description = 'Table of Unions'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    members_ids = fields.One2many(comodel_name="members.ranchy", inverse_name="group_id", string="Union Members", required=False, )
    co_id = fields.Many2one(comodel_name="hr.employee", string="Credit Officer", required=False,
                            track_visibility=True, trace_visibility='onchange', )
    description = fields.Text(string="Union Description", required=False, )
    union_day = fields.Selection(string="Union Day", selection=[('monday', 'Monday'), ('tuesday', 'Tuesday'),
                                                                ('wednesday', 'Wednesday'), ('thursday', 'Thursday'),
                                                                ('friday', 'Friday'), ], required=False, )


class DisbursmentRanchy(models.Model):
    _name = 'disbursment.ranchy'
    _rec_name = 'name'
    _description = 'Disbursments'

    name = fields.Char()


class MembersRanchy(models.Model):
    _name = 'members.ranchy'
    _rec_name = 'member_no'
    _description = 'members'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    first_name = fields.Char(string="First Name", required=False, track_visibility=True, trace_visibility='onchange', )
    surname = fields.Char(string="Surname", required=False, track_visibility=True, trace_visibility='onchange', )
    r_address = fields.Char(string="Residential Address", required=False, track_visibility=True, trace_visibility='onchange', )
    b_address = fields.Char(string="Business Address", required=False,)
    p_address = fields.Char(string="Permanent Address", required=False, track_visibility=True, trace_visibility='onchange',)
    phone = fields.Char(string="Phone Number", required=False, track_visibility=True, trace_visibility='onchange',)
    dob = fields.Date(string="Date of Birth", required=False, )
    marital_status = fields.Selection(string="Marital Status", selection=[('single', 'Single'), ('married', 'Married'),
                                                                          ('divorced', 'Divorced'), ('widow', 'Widow'),
                                                                          ], required=False, )
    formal_edu = fields.Selection(string="Formal Education", selection=[('none', 'None'), ('primary', 'Primary'),
                                                                        ('secondary', 'Secondary'),
                                                                        ('tertiary', 'Tertiary'), ], required=False)
    nok = fields.Char(string="next of Kin", required=False, track_visibility=True, trace_visibility='onchange',)
    nok_phone = fields.Char(string="NOK Phone", required=False, track_visibility=True, trace_visibility='onchange',)
    group_id = fields.Many2one(comodel_name="union.ranchy", string="Union/Group", required=False, track_visibility=True, trace_visibility='onchange', )
    m_photo = fields.Binary(string="", track_visibility=True, trace_visibility='onchange', )
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
    member_no = fields.Char(string="Member Number", default=lambda self: _('New'),
                            requires=False, readonly=True, trace_visibility='onchange', )
    active_loan = fields.Many2one(comodel_name="loans.ranchy", inverse_name="member_id", string="Loans",
                                 required=False,)

    @api.model
    def create(self, vals):
        if vals.get('member_no', _('New')) == _('New'):
            vals['member_no'] = self.env['ir.sequence'].next_by_code('increment_member') or _('New')
        result = super(MembersRanchy, self).create(vals)
        return result

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
    amount = fields.Integer(string="Amount", required=False, )


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
    _rec_name = 'installment'
    _description = 'New Description'

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan", required=False, )
    date = fields.Date(string="Schedule Date")
    installment = fields.Float(string="Installment Amount",  required=False, )
    state = fields.Selection(string="State", selection=[('paid', 'Paid'), ('unpaid', 'Unpaid'), ],
                             required=False, default='unpaid')

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('unpaid', 'paid'),

                   ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for installment in self:
            if installment.is_allowed_transition(installment.state, new_state):
                installment.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (installment.state, new_state)
                raise UserError(msg)

    @api.multi
    def apply_paid(self):
        self.change_state('paid')


class LoanPayments(models.Model):
    _name = 'payments.ranchy'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan", required=False, )
    amount = fields.Integer(string="Amount Paid")
    date = fields.Date(string="Date")


class CollectionRanchy(models.Model):
    _name = 'collection.ranchy'
    _rec_name = 'member'
    _description = 'table of collections'

    name = fields.Char()
    member = fields.Many2one(comodel_name="members.ranchy", string="Member", required=False, )
    group = fields.Many2one(string="Group/Union", related="member.group_id", readonly=True,)
    scheduled = fields.Float(string="Expected Installment", related="loan_id.installment_amount")
    loan_id = fields.Many2one(string="Active Loan", comodel_name="loans.ranchy")
    collect_loan = fields.Integer(string="Collected Loan amount", )
    collect_savings = fields.Integer(string="Collected Savings",)
    no_installments = fields.Integer(string="number of installments", compute="_no_installment")
    linked_installments_ids = fields.Many2many(comodel_name="schedule.installments", relation="collection_schedule_rel", column1="collection_id", column2="schedule_id", string="Linked Installments", )
    state = fields.Selection(string="", selection=[('draft', 'Draft'), ('collected', 'Collected'),
                                                   ('confirmed', 'Confirmed'), ], required=False, )
    collected_by = fields.Many2one('res.users', 'Collected By', default=lambda self: self.env.user)
    collected_total = fields.Integer(string="Total Collected", compute="_total_collected",)
    date = fields.Date(string="Date", required=False, default=date.today())




    @api.one
    @api.depends('collect_loan', 'collect_savings')
    def _total_collected(self):
        self.collected_total = self.collect_loan + self.collect_savings


    @api.one
    @api.depends('collect_loan')
    def _no_installment(self):
        self.no_installments = self.collect_loan / self.scheduled

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'collected'),
                   ('collected', 'confirmed'),

                   ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for collection in self:
            if collection.is_allowed_transition(collection.state, new_state):
                collection.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (collection.state, new_state)
                raise UserError(msg)

    def confirm_collection(self):
        savings = self.env['savings.ranchy']
        vals = {
            'member_id': self.member.id,
            'amount': self.collect_savings,
            'date': self.date,
        }
        savings.create(vals)
        loan_repayment = self.env['payments.ranchy']
        values = {
            'loan_id': self.loan_id.id,
            'amount': self.collect_loan,
            'date': self.date,

        }
        loan_repayment.create(values)
        schedule = self.env['schedule.installments']
        install_id = self.linked_installments_ids.id
        install = schedule.browse(install_id)

        install.apply_paid()
        self.change_state('confirmed')

    def schedule(self):
        sch = self.env['schedule.installments'].apply_paid
        return sch











