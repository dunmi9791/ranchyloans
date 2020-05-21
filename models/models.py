# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LoansRanchy(models.Model):
    _name = 'loans.ranchy'
    _rec_name = 'name'
    _description = 'Tables for loans'

    name = fields.Char()


class UnionRanchy(models.Model):
    _name = 'union.ranchy'
    _rec_name = 'name'
    _description = 'Table of Unions'

    name = fields.Char()


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

