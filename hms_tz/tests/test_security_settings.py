# Copyright (c) 2025, Aakvatech and Contributors
# See license.txt
from unittest.mock import patch

import frappe
from frappe.core.doctype.system_settings.system_settings import SystemSettings
from frappe.tests.utils import FrappeTestCase

from hms_tz.security.settings import CONTACT_US_BASELINE, SECURITY_BASELINE, apply_security_settings


class TestSecuritySettings(FrappeTestCase):
    def setUp(self):
        self.original = {
            field: frappe.db.get_single_value("System Settings", field)
            for field in SECURITY_BASELINE
        }
        self.original_contact = {
            field: frappe.db.get_single_value("Contact Us Settings", field)
            for field in CONTACT_US_BASELINE
        }

    def tearDown(self):
        for doctype, values in (
            ("System Settings", self.original),
            ("Contact Us Settings", self.original_contact),
        ):
            settings = frappe.get_single(doctype)
            settings.update(values)
            settings.flags.ignore_permissions = True
            settings.save()

    def test_baseline_is_applied(self):
        settings = frappe.get_single("System Settings")
        settings.allow_consecutive_login_attempts = 0
        settings.allow_error_traceback = 1
        settings.flags.ignore_permissions = True
        settings.save()

        apply_security_settings()

        settings.reload()
        for field, value in SECURITY_BASELINE.items():
            self.assertEqual(settings.get(field), value, msg=field)

    def test_contact_form_is_disabled(self):
        """frappe.www.contact.send_message is guest-callable and does not validate
        `subject`, so the form is disabled on every site rather than per deploy."""
        settings = frappe.get_single("Contact Us Settings")
        settings.is_disabled = 0
        settings.flags.ignore_permissions = True
        settings.save()

        apply_security_settings()

        self.assertEqual(
            frappe.db.get_single_value("Contact Us Settings", "is_disabled"), 1
        )

    def test_traceback_setting_cannot_be_re_enabled(self):
        """Login is authenticated before before_request hooks run, so the
        disable_traceback flag never reaches a failed login. allow_error_traceback
        is the only control for that endpoint and must not drift between migrates."""
        settings = frappe.get_single("System Settings")
        settings.allow_error_traceback = 1
        settings.flags.ignore_permissions = True
        settings.save()

        self.assertEqual(
            frappe.db.get_single_value("System Settings", "allow_error_traceback"), 0
        )

    def test_login_lockout_is_enabled(self):
        """frappe's per-IP and per-user LoginAttemptTracker are inert at 0."""
        self.assertGreater(SECURITY_BASELINE["allow_consecutive_login_attempts"], 0)

    def test_running_twice_does_not_save_again(self):
        """after_migrate runs this on every deploy; an unchanged baseline must not
        churn System Settings."""
        apply_security_settings()

        with patch.object(SystemSettings, "save") as save:
            apply_security_settings()

        save.assert_not_called()
