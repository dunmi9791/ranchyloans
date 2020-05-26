# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LoansRanchy(models.Model):
    _name = 'loans.ranchy'
    _rec_name = 'name'
    _description = 'Tables for loans'

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
                                                         ('paid', 'Fully Paid'), ], required=False, )
    schedule_installments_ids = fields.One2many(comodel_name="schedule.installments", inverse_name="loan_id",
                                                string="Schedule Installments", required=False, )
    payment_ids = fields.One2many(comodel_name="payments.ranchy", inverse_name="loan_id", string="Payments",
                                  required=False, )


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


class LoanType(models.Model):
    _name = 'loantype.ranchy'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()

class Savings(models.Model):
    _name = 'savings.ranchy'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
    member_id = fields.Many2one(comodel_name="members.ranchy", string="Member", required=False, )


class Withdrawals(models.Model):
    _name = 'withdrawals.ranchy'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
    member_id = fields.Many2one(comodel_name="members.ranchy", string="Member", required=False, )


class ScheduleInstallments(models.Model):
    _name = 'schedule.installments'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan", required=False, )


class LoanPayments(models.Model):
    _name = 'payments.ranchy'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan", required=False, )




