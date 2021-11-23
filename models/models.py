# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
from dateutil import relativedelta
from datetime import datetime
from datetime import date
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp


class LoansRanchy(models.Model):
    _name = 'loans.ranchy'
    _rec_name = 'loan_no'
    _description = 'Tables for loans'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    type = fields.Many2one(comodel_name="loantype.ranchy", string="Loan Type", required=True,
                           track_visibility=True, trace_visibility='onchange' )
    app_date = fields.Date(string="Date of Application", required=False, )
    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=True,
                                track_visibility=True, trace_visibility='onchange',)
    group = fields.Many2one(string="Group/Union", comodel_name="union.ranchy",)
    avg_monthly = fields.Float(string="Average Monthly Income",  required=False, )
    last_loan = fields.Float(string="Last Loan Received", required=False, )
    date_fullypaid = fields.Date(string="Date Last Loan was Fully Paid", required=False)
    amount_apply = fields.Float(string="Amount Applied For(principal)", required=False,
                                track_visibility=True, trace_visibility='onchange',)
    amount_approved = fields.Float(string="Amount Approved", required=False,
                                   track_visibility=True, trace_visibility='onchange',)
    credit = fields.Monetary(default=0.0, currency_field='currency_id')
    no_install = fields.Integer (string="Number of Installments", related="type.no_installments", readonly=True,)
    duration = fields.Char(string="Loan Duration", required=False)
    date_first = fields.Date(string="Date First Installment is Due", required=False)
    date_last = fields.Date(string="Date Last Installment is Due", required=False)
    is_family = fields.Boolean(string="Any family member registered in the group",  )
    name_family = fields.Char(string="Name of Family Member")
    savings_balance = fields.Float(string="Savings Balance", related="member_id.balance", readonly=True,)
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
    total_realised = fields.Integer(string="Realised Total", compute='_total_realised', store=True)
    balance_loan = fields.Integer(string="Loan Balance", compute='_loan_balance', store=True )
    is_computed = fields.Boolean(string="Computed",  )
    interest_rate = fields.Float(string="Interest Rate", related="type.service_rate", readonly=True,)
    stage_id = fields.Many2one(comodel_name="loan.stages", string="Loan Stage", required=False, )
    riskpremium_rate = fields.Float(string="Premium Rate", related="type.risk_premium", readonly=True, )
    admin_charge = fields.Float(string="Administrative Charge", related="type.admin_charge", readonly=True,)
    risk_premium_amount = fields.Float(string="Risk Premium", compute='_risk_premium',)
    fee_paid = fields.Boolean(string="Fees Paid")
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True, default=lambda self: self.env.user.company_id)
    fees_collected = fields.Boolean(string="",  )
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', store=True, string="Currency")

    @api.one
    @api.depends('company_id')
    def _compute_currency(self):
        self.currency_id = self.company_id.currency_id or self.env.user.company_id.currency_id

    @api.onchange('group')
    def _onchange_group_id(self):
        if self.group:
            members_ids = self.group.members_ids.ids
            return {'domain': {'member_id': [('id', 'in', members_ids),]}}

    @api.one
    @api.depends('amount_approved')
    def _risk_premium(self):
        self.risk_premium_amount = self.amount_approved * (self.riskpremium_rate / 100)

    @api.one
    @api.depends('schedule_installments_ids.installment', )
    def _total_realisable(self):

        self.total_realisable = sum(schedule.installment for schedule in self.schedule_installments_ids)

    @api.one
    @api.depends('schedule_installments_ids.state', )
    def _total_realised(self):

        self.total_realised = sum(paid.installment
                                  for paid in self.schedule_installments_ids.filtered(lambda o: o.state == 'paid'))

    @api.one
    @api.depends('amount_approved')
    def _interest(self):
        self.interest = self.amount_approved * (self.interest_rate / 100)

    @api.one
    @api.depends('interest', 'amount_approved')
    def _repay_amount(self):
        self.payment_amount = self.amount_approved + self.interest

    @api.one
    @api.depends('payment_amount')
    def _installment_amount(self):
        self.installment_amount = self.payment_amount / self.no_install

    @api.one
    @api.depends('total_realised', 'payment_amount')
    def _loan_balance(self):
        self.balance_loan = self.payment_amount - self.total_realised

    @api.onchange('balance_loan')
    def _onchange_balance_loan(self):
        if self.balance_loan == 0.00:
            self.change_state('paid')

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
        for loan in self:
            loan.compute_schedule()
            self.change_state('approved')

    @api.multi
    def disburse_loan(self):
        if self.fees_collected:
            self.change_state('disbursed')
        else:
            raise ValidationError(
                _('Collect and Enter Risk Premium and admin Charges first'))

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

    @api.model
    def _compute_monthly(self, loan_amount, period, first_payment_date):
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
                                    months=+1)
        return result

    @api.multi
    def _compute_payment(self):
        self.ensure_one()

        obj_loan_type = self.env["loans.ranchy"]
        obj_payment = self.env["schedule.installments"]
        if self.type.installment_period == 'weekly':
            payment_datas = obj_loan_type._compute_flat(
                self.payment_amount,
                self.no_install,
                self.date_first,)
            for payment_data in payment_datas:
                payment_data.update({"loan_id": self.id})
                obj_payment.create(payment_data)

        elif self.type.installment_period == 'monthly':
            payment_datas = obj_loan_type._compute_monthly(
                self.payment_amount,
                self.no_install,
                self.date_first, )

            for payment_data in payment_datas:
                payment_data.update({"loan_id": self.id})
                obj_payment.create(payment_data)

    @api.multi
    def compute_schedule(self):
        if self.is_computed:
            msg = _('Schedule has already been computed')
            raise UserError(msg)
        else:
            for loan in self:
                loan._compute_payment()
                self.is_computed = True

    @api.multi
    def write(self, values):
        if self.balance_loan in values and self.balance_loan == 0:
            self.change_state('paid')
        return super(LoansRanchy, self).write(values)


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
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    union_purse_ids = fields.One2many(comodel_name="union.purse", inverse_name="union_id", string='Purse')
    union_purse_balance = fields.Float(string="Purse Balance", compute='_compute_purse' )

    @api.multi
    @api.depends('union_purse_ids')
    def _compute_purse(self):
        for record in self:
            purse_list = []
            for line in record.union_purse_ids:
                purse_list.append(line.balance)
            self.union_purse_balance = purse_list[-1]
        # last_transaction = self.env['union.purse'].search(['union_id', "=", self.id])[:-1].id
        # purse_balance = last_transaction.balance
        # return purse_balance



class UnionPurse(models.Model):
    _name = 'union.purse'
    _rec_name = ''
    _description = 'Table for union purse'

    union_id = fields.Many2one( comodel_name='union.ranchy', string='Union', required=False)
    date = fields.Date(string='Date', required=False)
    details = fields.Char(string='Details', required=False)
    debit = fields.Float(string='Debit', required=False)
    credit = fields.Float(string='Credit', required=False)
    balance = fields.Float(string='Balance', compute='_purse_balance', required=False, store=True)
    previous_balance = fields.Float(string='previous balance', compute='_previous_record', store=True)
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)

    @api.one
    @api.depends('union_id', )
    def _previous_record(self):
        for record in self:
            balance_ids = self.env['union.purse'].search([('union_id', '=', self.union_id.id), ('id', '<', record.id)], order='id desc', limit=1)
            previous_record = balance_ids[0]['balance'] if balance_ids else 0
            self.previous_balance = previous_record

    @api.depends('balance')
    def get_data(self):
        for rec in self:
            if not isinstance(rec.id, models.NewId):
                previous_balance = 0
                for previusin in self.search([('id', '<', rec.id)]):
                    previous_balance += previusin.balance
                previous_balance += rec.balance
                rec.previous_balance = previous_balance

    @api.one
    @api.depends('previous_balance')
    def _purse_balance(self):
        self.balance = self.previous_balance + self.debit - self.credit






class DisbursementRanchy(models.Model):
    _name = 'disbursement.ranchy'
    _rec_name = 'name'
    _description = 'Disbursements'

    name = fields.Char()


class MembersRanchy(models.Model):
    _name = 'members.ranchy'
    _rec_name = 'member_no'
    _description = 'members'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", compute="fullname", required=False)
    first_name = fields.Char(string="First Name", required=True, track_visibility=True, trace_visibility='onchange', )
    surname = fields.Char(string="Surname", required=True, track_visibility=True, trace_visibility='onchange', )
    r_address = fields.Char(string="Residential Address", required=False, track_visibility=True, trace_visibility='onchange', )
    b_address = fields.Char(string="Business Address", required=False,)
    p_address = fields.Char(string="Permanent Address", required=False, track_visibility=True, trace_visibility='onchange',)
    phone = fields.Char(string="Phone Number", required=True, track_visibility=True, trace_visibility='onchange',)
    dob = fields.Date(string="Date of Birth", required=False, )
    marital_status = fields.Selection(string="Marital Status", selection=[('single', 'Single'), ('married', 'Married'),
                                                                          ('divorced', 'Divorced'), ('widow', 'Widow'),
                                                                          ], required=False, )
    formal_edu = fields.Selection(string="Formal Education", selection=[('none', 'None'), ('primary', 'Primary'),
                                                                        ('secondary', 'Secondary'),
                                                                        ('tertiary', 'Tertiary'), ], required=False)
    nok = fields.Char(string="next of Kin", required=False, track_visibility=True, trace_visibility='onchange',)
    nok_phone = fields.Char(string="NOK Phone", required=False, track_visibility=True, trace_visibility='onchange',)
    group_id = fields.Many2one(comodel_name="union.ranchy", string="Union/Group", required=True, track_visibility=True,
                               trace_visibility='onchange', )
    union_card_no = fields.Selection(string="Union Card", selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
                                                           ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
                                                           ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'),
                                                           ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'),
                                                           ('20', '20'), ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24'),
                                                           ('25', '25'), ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'),
                                                           ('30', '30'), ('31', '31'), ], required=False, )
    m_photo = fields.Binary(string="", track_visibility=True, trace_visibility='onchange', attachment=True, readonly=False, )
    saving_ids = fields.One2many(comodel_name="savings.ranchy", inverse_name="member_id", string="Savings", required=False, )
    withdrawal_ids = fields.One2many(comodel_name="withdrawals.ranchy", inverse_name="member_id", string="Withdrawals",
                                 required=False, )
    loan_ids = fields.One2many(comodel_name="loans.ranchy", inverse_name="member_id", string="Loans",
                                 required=False, )
    active = fields.Boolean(string="Active", default=True)
    loan_count = fields.Integer(string="Loans", compute='get_loan_count', )
    collection_count = fields.Integer(string="Loans", compute='get_collection_count', )
    saving_total = fields.Float(string="saving total", compute='_saving_total')
    withdrawal_total = fields.Float(string="withdrawal total", compute='_withdrawal_total')
    balance = fields.Float(string="Savings Balance", compute='_balance')
    member_no = fields.Char(string="Member Number", default=lambda self: _('New'),
                            requires=False, readonly=True, trace_visibility='onchange', )
    active_loan = fields.Many2one(comodel_name="loans.ranchy", inverse_name="member_id", string="Loans",
                                 required=False,)
    collection_ids = fields.One2many(comodel_name="collection.ranchy", inverse_name="member", string="Collections")
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            record_name = record.name + ' - ' + record.member_no
            result.append((record.id, record_name))
        return result

    @api.one
    @api.depends('first_name', 'surname')
    def fullname(self):
        for record in self:
            record['name'] = (record.first_name or '') + ' ' + (record.surname or '')

    @api.model
    def create(self, vals):
        if vals.get('member_no', _('New')) == _('New'):
            vals['member_no'] = self.env['ir.sequence'].next_by_code('increment_member') or _('New')
        result = super(MembersRanchy, self).create(vals)
        return result

    def get_loan_count(self):
        count = self.env['loans.ranchy'].search_count([('member_id', '=', self.id)])
        self.loan_count = count

    def get_collection_count(self):
        count = self.env['collection.ranchy'].search_count([('member', '=', self.id)])
        self.collection_count = count

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
    installment_period = fields.Selection(string="Installment Period", selection=[('weekly', 'Weekly'),
                                                                                  ('monthly', 'Monthly'), ],
                                          required=False, default='weekly' )
    service_rate = fields.Float(string="Service Rate", required=True, )
    admin_charge = fields.Float(string="Administrative Charge", required=True)
    risk_premium = fields.Float(string="Risk Premium", required=True)
    no_installments = fields.Integer(string="Number of Installments", required=True)


class Savings(models.Model):
    _name = 'savings.ranchy'
    _rec_name = 'name'
    _description = 'Savings Deposit'

    name = fields.Char()
    member_id = fields.Many2one(comodel_name="members.ranchy", string="Member", required=False, )
    date = fields.Date(string="Date", required=False, )
    amount = fields.Integer(string="Amount", required=False, )
    note = fields.Char(string="Note", required=False, )


class Withdrawals(models.Model):
    _name = 'withdrawals.ranchy'
    _rec_name = 'name'
    _description = 'withdrawals'

    name = fields.Char()
    member_id = fields.Many2one(comodel_name="members.ranchy", string="Member", required=False, )
    date = fields.Date(string="Date", required=False, )
    amount = fields.Float(string="Amount", required=False, )
    description = fields.Char(string="Description", required=False, )


class ScheduleInstallments(models.Model):
    _name = 'schedule.installments'
    _rec_name = 'date'
    _description = 'installments'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan", required=False, )
    date = fields.Date(string="Schedule Date")
    installment = fields.Float(string="Installment Amount",  required=False, )
    state = fields.Selection(string="State", selection=[('paid', 'Paid'), ('unpaid', 'Unpaid'), ],
                             required=False, default='unpaid')
    member = fields.Many2one(comodel_name="members.ranchy", string="Member", related="loan_id.member_id", store=True)
    union = fields.Many2one(comodel_name="union.ranchy", string="Union/Group", related="member.group_id", store=True)
    image = fields.Binary(string="Photo", related="member.m_photo")
    collected = fields.Boolean(string="",  )
    default = fields.Boolean(string="",)
    member_name = fields.Char(string="Name", related="member.name")
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    collection_id = fields.Many2one('collection.ranchy', invisible=1)
    collection_loan = fields.Integer(string="Collection (Loan)",)
    collection_savings = fields.Integer(string="Collection(Savings)",)
    no_installments = fields.Integer(string="Number of Installments Paid", required=False, default=1, )

    @api.onchange('loan_id')
    def _onchange_loan_id(self):
        if self.loan_id:
            schedule_ids = self.loan_id.schedule_installments_ids.ids
            return {'domain': {'linked_schedule_ids': [('id', 'in', schedule_ids), ('state', '=', 'unpaid')]}}

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('unpaid', 'paid'),
                   ('paid', 'paid'),

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

    def collect_repayment(self):
        self.ensure_one()
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'collect.amount',
            'view_id': self.env.ref('ranchyloans.collect_repayment_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_loan_id': self.loan_id.id,


            },
            'target': 'new'
        }

    @api.multi
    def mark_paid(self):
        collection = self.env['collection.ranchy'].create({
                'member': self.member.id,
                'loan_id': self.loan_id.id,
                'collect_loan': self.installment,
                'no_installments': 1,
                'linked_installments_ids': [(6, 0, self.ids)],
                'state': 'collected',
                'date': date.today(),
            })
        self.collection_id = collection
        payment = self.env['payments.ranchy']
        payment_detail ={
            'loan_id': self.loan_id.id,
            'amount': self.installment,
            'date': date.today(),
            'collection_id': self.collection_id.id,
        }
        payment.create(payment_detail)

        self.change_state('paid')

    @api.multi
    @api.depends('date')
    def _reschedule_date(self):
        loan_id = self.loan_id
        schedules = loan_id.schedule_installments_ids.date
        latestdate = max(schedules)
        new_date = latestdate + relativedelta.relativedelta(weeks=+1)
        self.date = new_date


class LoanPayments(models.Model):
    _name = 'payments.ranchy'
    _rec_name = 'name'
    _description = 'Payments'

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan", required=False, )
    amount = fields.Integer(string="Amount Paid")
    date = fields.Date(string="Date")
    collection_id = fields.Many2one('collection.ranchy', invisible=1)


class CollectionRanchy(models.Model):
    _name = 'collection.ranchy'
    _rec_name = 'member'
    _description = 'table of collections'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    member = fields.Many2one(comodel_name="members.ranchy", string="Member", required=False, track_visibility=True, trace_visibility='onchange')
    group = fields.Many2one(string="Group/Union", related="member.group_id", readonly=True, store=True)
    scheduled = fields.Float(string="Expected Installment", related="loan_id.installment_amount")
    loan_id = fields.Many2one(string="Active Loan", comodel_name="loans.ranchy", track_visibility=True,)
    collect_loan = fields.Integer(string="Collected Loan amount", track_visibility=True, trace_visibility='onchange')
    collect_savings = fields.Integer(string="Collected Savings", trace_visibility='onchange')
    no_installments = fields.Integer(string="number of installments", compute="_no_installment",
                                     track_visibility=True, trace_visibility='onchange')
    linked_installments_ids = fields.Many2many(comodel_name="schedule.installments", relation="collection_schedule_rel", column1="collection_id", column2="schedule_id", string="Linked Installments", )
    state = fields.Selection(string="", selection=[('draft', 'Draft'), ('collected', 'Collected'),
                                                   ('confirmed', 'Confirmed'), ], required=False, track_visibility=True, trace_visibility='onchange' )
    collected_by = fields.Many2one('res.users', 'Collected By', default=lambda self: self.env.user,
                                   track_visibility=True,trace_visibility='onchange')
    collected_total = fields.Integer(string="Total Collected", compute="_total_collected", store=True, track_visibility=True,)
    date = fields.Date(string="Date", required=False, default=date.today(),
                       track_visibility=True, trace_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    description = fields.Char(string="Description", required=False, trace_visibility='onchange')
    note = fields.Char(string="Note", required=False, )
    # savings_balance = fields.Float(string="Saving Balance", related="member.balance", store=True)
    # loan_balance = fields.Integer(string="Loan Balance", related="loan_id.balance_loan", store=True)
    # journal_id = fields.Many2one('account.journal', string='Journal', required=True,
    #                              states={'confirm': [('readonly', True)]}, default=_default_journal)

    @api.onchange('member')
    def _onchange_member_id(self):
        if self.member:
            loan_ids = self.member.loan_ids.ids
            return {'domain': {'loan_id': [('id', 'in', loan_ids), ('state', '=', 'disbursed')]}}

    @api.onchange('loan_id')
    def _onchange_loan_id(self):
        if self.loan_id:
            schedule_ids = self.loan_id.schedule_installments_ids.ids
            return {'domain': {'linked_installments_ids': [('id', 'in', schedule_ids), ('state', '=', 'unpaid')]}}

    @api.one
    @api.depends('collect_loan', 'collect_savings')
    def _total_collected(self):
        self.collected_total = self.collect_loan + self.collect_savings


    @api.one
    @api.depends('collect_loan')
    def _no_installment(self):
        if self.collect_loan:
            self.no_installments = self.collect_loan / self.scheduled
        else:
            pass

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
            'note': self.note
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
        install_id = self.linked_installments_ids.ids
        install = schedule.browse(install_id)

        install.sudo().apply_paid()
        self.change_state('confirmed')

    def schedule(self):
        sch = self.env['schedule.installments'].apply_paid
        return sch

    def _daily(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        today = 300000
        yesterday = 25000
        result = {"value": today, "previous": yesterday}
        return result

    @api.one
    @api.depends('')
    def _daily_collection(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        number = 60
        return number


class Kpi(models.Model):
    _inherit = 'kpi.kpi'

    @api.multi
    def _daily_collection(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        number = 60
        return number

    @api.multi
    def _daily(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        number = 300000
        return number












