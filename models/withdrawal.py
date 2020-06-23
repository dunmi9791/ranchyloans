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

