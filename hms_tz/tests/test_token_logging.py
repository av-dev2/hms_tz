# Copyright (c) 2025, Aakvatech and Contributors
# See license.txt
import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

MODULE = "hms_tz.hms_tz.doctype.hms_tz_setting.hms_tz_setting"


def response_for(payload):
    response = MagicMock()
    response.text = json.dumps(payload)
    response.status_code = 200
    return response


class TestTokenRequestLogging(FrappeTestCase):
    """Provider credentials do not expire, so they must never reach a response log."""

    def setting_doc(self, **values):
        doc = frappe.get_doc({"doctype": "HMS TZ Setting", **values})
        doc.get_password = MagicMock(return_value="super-secret")
        doc.db_update = MagicMock()
        doc.reload = MagicMock()
        doc.clear_cache = MagicMock()
        return doc

    def test_nhif_client_secret_is_masked(self):
        doc = self.setting_doc(
            enable_nhif_api=1,
            nhif_token_url="https://example.test/token",
            nhif_grant_type="password",
            nhif_scope="MedicalService",
            nhif_user="facility",
            facility_code="F1",
        )
        token_response = response_for({
            "token_type": "bearer",
            "access_token": "tok",
            "expires_in": 3600,
        })

        with patch(f"{MODULE}.requests.request", return_value=token_response), patch(
            f"{MODULE}.add_log"
        ) as add_log:
            doc.get_nhif_token()

        logged = add_log.call_args.kwargs["request_body"]
        self.assertEqual(logged["client_secret"], "***")
        self.assertNotIn("super-secret", str(logged))

    def test_nhif_request_still_sends_the_real_secret(self):
        """Masking is for the log only; the outbound request must be unchanged."""
        doc = self.setting_doc(
            enable_nhif_api=1,
            nhif_token_url="https://example.test/token",
            nhif_grant_type="password",
            nhif_scope="MedicalService",
            nhif_user="facility",
            facility_code="F1",
        )
        token_response = response_for({
            "token_type": "bearer",
            "access_token": "tok",
            "expires_in": 3600,
        })

        with patch(
            f"{MODULE}.requests.request", return_value=token_response
        ) as request, patch(f"{MODULE}.add_log"):
            doc.get_nhif_token()

        self.assertEqual(request.call_args.kwargs["data"]["client_secret"], "super-secret")

    def test_nhif_log_keeps_non_secret_fields(self):
        """The logs exist to debug claim rejections, so masking must stay narrow."""
        doc = self.setting_doc(
            enable_nhif_api=1,
            nhif_token_url="https://example.test/token",
            nhif_grant_type="password",
            nhif_scope="MedicalService",
            nhif_user="facility",
            facility_code="F1",
        )
        token_response = response_for({
            "token_type": "bearer",
            "access_token": "tok",
            "expires_in": 3600,
        })

        with patch(f"{MODULE}.requests.request", return_value=token_response), patch(
            f"{MODULE}.add_log"
        ) as add_log:
            doc.get_nhif_token()

        logged = add_log.call_args.kwargs["request_body"]
        self.assertEqual(logged["client_id"], "F1")
        self.assertEqual(logged["username"], "facility")
        self.assertEqual(logged["scope"], "MedicalService")

    def test_jubilee_password_is_masked(self):
        doc = self.setting_doc(
            enable_jubilee_api=1,
            jubilee_url="https://example.test",
            jubilee_user="provider",
            jubilee_provider_id="P1",
        )
        token_response = response_for({
            "Description": {"access_token": "tok", "issued_at": 0, "expires_in": 3600}
        })

        with patch(f"{MODULE}.requests.request", return_value=token_response), patch(
            f"{MODULE}.add_jubilee_log"
        ) as add_jubilee_log:
            doc.get_jubilee_token()

        logged = add_jubilee_log.call_args.kwargs["request_body"]
        self.assertEqual(logged["password"], "***")
        self.assertNotIn("super-secret", str(logged))
        self.assertEqual(logged["username"], "provider")
