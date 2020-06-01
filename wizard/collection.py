from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CollectAmount(models.TransientModel):
    _name = 'collect.amount'
    _description = 'Collect Amount Wizard'

    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False, )
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True, )
    co_id = fields.Many2one(related="member_id.group_id.co_id", string="Credit Officer", readonly=True, )
    scheduled_amount = fields.Float(string="Scheduled Amount",  required=False, )
    collected_amount = fields.Float(string="Collected Amount", required=False, )
    balance = fields.Float(string="Balance", compute="_balance", )
    loan_id = fields.Many2one(comodel_name="loans.ranchy", string="Loan ID")

    @api.one
    @api.depends('scheduled_amount')
    def _balance(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        self.balance = self.scheduled_amount - self.collected_amount


    @api.one
    @api.depends('')
    def collect_amount(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        pass


class WithdrawAmount(models.TransientModel):
    _name = 'withdraw.amount'
    _description = 'Withdraw Amount Wizard'

    member_id = fields.Many2one(comodel_name="members.ranchy", string="", required=False, )
    group = fields.Many2one(string="Group/Union", related="member_id.group_id", readonly=True, )
    co_id = fields.Many2one(related="member_id.group_id.co_id", string="Credit Officer", readonly=True, )
    amount = fields.Float(string="Amount",  required=False, )
    balance = fields.Float(string="Balance", related="member_id.balance", )

    @api.one
    @api.depends('')
    def withdraw_amount(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        pass


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


