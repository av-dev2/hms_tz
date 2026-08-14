# Copyright (c) 2025, Aakvatech and Contributors
# See license.txt
from unittest.mock import patch

import frappe
from frappe.core.doctype.user.user import reset_password
from frappe.tests.utils import FrappeTestCase

KNOWN_USER = "Administrator"
UNKNOWN_USER = "definitely-not-a-user@example.invalid"


class TestPasswordResetEnumeration(FrappeTestCase):
    """The reset endpoint must not reveal whether an account exists (CWE-204).

    Frappe fixes this upstream; this test fails if the site is ever rolled back
    to a release that answers differently for known and unknown users.
    """

    def reset_for(self, user):
        frappe.local.response = frappe._dict()
        frappe.clear_messages()
        with patch("frappe.sendmail"):
            reset_password(user=user)
        return {
            "status": frappe.local.response.get("http_status_code"),
            "messages": [m.get("message") for m in frappe.get_message_log()],
        }

    def test_known_and_unknown_users_get_the_same_answer(self):
        known = self.reset_for(KNOWN_USER)
        unknown = self.reset_for(UNKNOWN_USER)

        self.assertEqual(known["messages"], unknown["messages"])
        self.assertEqual(known["status"], unknown["status"])

    def test_unknown_user_does_not_return_404(self):
        """Cybergen enumerated accounts from a 404 'not found' on this endpoint."""
        self.assertNotEqual(self.reset_for(UNKNOWN_USER)["status"], 404)

    def test_response_does_not_name_the_account(self):
        messages = " ".join(self.reset_for(UNKNOWN_USER)["messages"]).lower()

        self.assertNotIn("not found", messages)
        self.assertNotIn("does not exist", messages)
        self.assertNotIn(UNKNOWN_USER.lower(), messages)
