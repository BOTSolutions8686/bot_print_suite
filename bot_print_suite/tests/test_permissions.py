"""Regression tests for authorization gates around whitelisted APIs."""

import unittest
from unittest.mock import patch

import frappe

from bot_print_suite.bot_print_suite.doctype.print_enquiry.print_enquiry import (
	_require_permission as require_enquiry_permission,
)
from bot_print_suite.estimation.quotation_mapper import (
	_require_permission as require_quotation_permission,
)
from bot_print_suite.production.job_tracker import _require_sales_order_read
from bot_print_suite.production.start_production import (
	_require_permission as require_production_permission,
)


class TestWhitelistedAPIPermissions(unittest.TestCase):
	@patch("frappe.has_permission", return_value=False)
	def test_enquiry_conversion_rejects_missing_destination_permission(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			require_enquiry_permission("Print Estimate", "create")

	@patch("frappe.has_permission", return_value=False)
	def test_quotation_creation_rejects_missing_destination_permission(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			require_quotation_permission("Quotation", "create")

	@patch("frappe.has_permission", return_value=False)
	def test_production_start_rejects_missing_destination_permission(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			require_production_permission("Work Order", "submit")

	@patch("frappe.has_permission", return_value=False)
	def test_job_metrics_require_sales_order_read_permission(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			_require_sales_order_read()

