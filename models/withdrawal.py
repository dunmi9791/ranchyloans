# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from dateutil import relativedelta
from datetime import datetime
from datetime import date


class WithdrawRequest(models.Model):
    _name = 'withdraw.request'
    _rec_name = 'request_id'
    _description = 'Withdrawal Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    request_id = fields.Char(string="Request ID", default=lambda self: _('New'),
                             requires=False, readonly=True, trace_visibility='onchange', )
    member_id = fields.Many2one(comodel_name="members.ranchy", string="Member", required=False, )
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True, )
    request_date = fields.Date(string="Date", required=False, default=date.today())
    disburse_date = fields.Date(string="Scheduled Date", required=False,)
    amount = fields.Integer(string="Requested Amount", required=False, )
    disburse_amount = fields.Integer(string="Disbursed Amount", required=False,)
    note = fields.Text(string="Notes", required=False, )
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('requested', 'Requested'),
                                                        ('disbursed', 'Disbursed'), ('rejected', 'Rejected'), ],
                             default='draft', required=False, track_visibility=True, trace_visibility='onchange', )

    @api.model
    def create(self, vals):
        if vals.get('request_id', _('New')) == _('New'):
            vals['request_id'] = self.env['ir.sequence'].next_by_code('increment_request') or _('New')
        result = super(WithdrawRequest, self).create(vals)
        return result

    def _track_subtype(self, init_values):
        # init_values contains the modified fields' values before the changes
        #
        # the applied values can be accessed on the record as they are already
        # in cache
        self.ensure_one()
        if 'state' in init_values and self.state == 'requested':
            return 'ranchyloans.wtd_state_request'  # Full external id
        elif 'state' in init_values and self.state == 'disbursed':
            return 'ranchyloans.wtd_state_disburse'
        elif 'state' in init_values and self.state == 'rejected':
            return 'ranchyloans.wtd_state_reject'
        return super(WithdrawRequest, self)._track_subtype(init_values)

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'requested'),
                   ('requested', 'disbursed'),
                   ('requested', 'rejected'),
                   ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for request in self:
            if request.is_allowed_transition(request.state, new_state):
                request.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (request.state, new_state)
                raise UserError(msg)

    def request_withdrawal(self):
        self.change_state('requested')

    def reject_withdrawal(self):
        self.change_state('rejected')

    def disburse_withdrawal(self):
        self.change_state('disbursed')


class LoanStages(models.Model):
    _name = 'loan.stages'
    _rec_name = 'name'
    _description = 'Loan Stages'

    name = fields.Char()
    principal_amount = fields.Float(string="Principal Amount",  required=False, )


class LapseAdjustment(models.Model):
    _name = 'lapse.adjustment'
    _rec_name = 'name'
    _description = 'Lapse Table'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False, )
    loan_id = fields.Many2one(string="Loan", comodel_name="loans.ranchy")
    amount = fields.Float(string="Adjustment Amount", required=False, )
    date = fields.Date(string="Date", required=False, )
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)


class PostCollection(models.TransientModel):
    """
    This wizard will flag expense request to attend to later
    """

    _name = "post.collection"
    _description = "Post Collections "

    @api.multi
    def post_collection(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['schedule.installments'].browse(active_ids):
            if record.state == 'unpaid':
                collection = self.env['collection.ranchy']
                vals = {
                    'member': record.member.id,
                    'loan_id': record.loan_id.id,
                    'collect_loan': record.collection_loan,
                    'collect_savings': record.collection_savings,
                    'no_installments': record.no_installments,
                    # 'linked_installments_ids': [(6, 0, record.linked_schedule_ids.ids)],
                    'state': 'collected',
                    'date': date.today(),
                }
                collection.create(vals)
                record.change_state('paid')
            else:
                pass

        return {'type': 'ir.actions.act_window_close'}


class FeesCollection(models.Model):
    _name = 'fees.collection'
    _rec_name = 'name'
    _description = 'Fees collection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan Id", required=False, )
    member_id = fields.Many2one(comodel_name="members.ranchy", string="Member", related="loan_id.member_id")
    date = fields.Date(string="Date", required=False, default=date.today())
    risk_premium = fields.Float(string="Risk Premium", required=False, )
    amount = fields.Float(string="Total", required=False, )
    admin_charge = fields.Float(string="Administrative Charge")
    state = fields.Selection(string="Status", selection=[('collected', 'Collected'), ('posted', 'Posted'), ],
                             required=False, default='collected')
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('collected', 'posted'),

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

    @api.multi
    def post_collection(self):
        self.change_state('posted')


class Disbursements(models.Model):
    _name = 'disbursements.ranchi'
    _rec_name = 'name'
    _description = 'Disbursement Table'

    name = fields.Char()
    union_id = fields.Many2one(comodel_name="union.ranchy", string="", required=False, )
    member_id = fields.Many2one(comodel_name="members.ranchy", string="Member", )
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan")
    disbursed_amount = fields.Float(string="Disbursed Amount",  required=False, )
    mode = fields.Selection(string="Mode of Disburse", selection=[('cash', 'Cash'), ('cheque', 'Cheque'),
                                                                  ('transfer', 'Transfer')], required=False, )
    state = fields.Selection(string="Status", selection=[('disbursed', 'Disbursed'), ('posted', 'Posted'), ],
                             required=False, default='disbursed')
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    mode_ref = fields.Char(string="Cheque / Ref", required=False, )




