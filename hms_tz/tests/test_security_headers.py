# Copyright (c) 2025, Aakvatech and Contributors
# See license.txt
from frappe.tests.utils import FrappeTestCase
from werkzeug.wrappers import Response

from hms_tz.security.headers import apply_security_headers


class TestSecurityHeaders(FrappeTestCase):
    def headers_for(self, **kwargs):
        response = Response()
        for key, value in kwargs.items():
            response.headers[key.replace("_", "-")] = value
        apply_security_headers(response=response, request=None)
        return response.headers

    def test_permissions_policy_is_set(self):
        self.assertIn("Permissions-Policy", self.headers_for())

    def test_camera_stays_allowed(self):
        """Facial patient authorization calls getUserMedia; camera=() breaks it."""
        self.assertIn("camera=(self)", self.headers_for()["Permissions-Policy"])

    def test_usb_stays_allowed(self):
        """The Mantra and DigitalPersona fingerprint readers must keep working."""
        self.assertIn("usb=(self)", self.headers_for()["Permissions-Policy"])

    def test_unused_features_are_denied(self):
        policy = self.headers_for()["Permissions-Policy"]
        for feature in ("geolocation=()", "microphone=()", "payment=()"):
            self.assertIn(feature, policy)

    def test_existing_headers_are_not_overwritten(self):
        """The site already serves some headers; duplicates confuse browsers."""
        headers = self.headers_for(X_Content_Type_Options="custom-value")

        self.assertEqual(headers["X-Content-Type-Options"], "custom-value")

    def test_missing_response_is_ignored(self):
        """frappe.app leaves response as None when it returns an HTTPException."""
        apply_security_headers(response=None, request=None)
