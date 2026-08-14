# Copyright (c) 2025, Aakvatech and Contributors
# See license.txt
import frappe
from frappe.tests.utils import FrappeTestCase
from werkzeug.exceptions import NotFound

from hms_tz.security.request import block_unused_routes, disable_traceback_leakage


def request_for(path):
    return frappe._dict(path=path)


class TestTracebackSuppression(FrappeTestCase):
    def test_traceback_flag_is_set(self):
        """frappe.utils.response.is_traceback_allowed() reads this flag to decide
        whether to put `exc` in the response, so it must be set on every request."""
        frappe.local.flags.disable_traceback = False

        disable_traceback_leakage()

        self.assertTrue(frappe.local.flags.disable_traceback)


class TestRouteBlocking(FrappeTestCase):
    def setUp(self):
        self.original_request = getattr(frappe.local, "request", None)

    def tearDown(self):
        frappe.local.request = self.original_request

    def block(self, path):
        frappe.local.request = request_for(path)
        block_unused_routes()

    def assert_blocked(self, path):
        with self.assertRaises(NotFound, msg=f"{path} should be blocked"):
            self.block(path)

    def assert_allowed(self, path):
        try:
            self.block(path)
        except NotFound:
            self.fail(f"{path} must stay reachable")

    def test_unused_framework_routes_are_blocked(self):
        for path in ("/_test", "/backups", "/blog", "/partners", "/sitemap.xml"):
            self.assert_blocked(path)

    def test_test_page_tree_is_blocked(self):
        """The /_test* tree is what rendered the raw 'Illegal template' traceback."""
        self.assert_blocked("/_test_safe_render_on")
        self.assert_blocked("/_test/_test_folder")

    def test_blocking_ignores_case(self):
        """Frappe routes are case-sensitive, so /Members must be blocked too."""
        self.assert_blocked("/Members")

    def test_security_txt_stays_reachable(self):
        """Frappe serves /.well-known/security.txt after before_request runs, so a
        broad .well-known block would silently remove the disclosure contact."""
        self.assert_allowed("/.well-known/security.txt")

    def test_openid_configuration_is_blocked(self):
        self.assert_blocked("/.well-known/openid-configuration")

    def test_clinical_routes_stay_reachable(self):
        """printview prints Sales Invoices from the encounter and appointment forms;
        address and list are portal routes."""
        for path in (
            "/",
            "/app/patient-encounter",
            "/api/method/ping",
            "/frontend/appointments",
            "/printview",
            "/address",
            "/list",
            "/lab-test",
        ):
            self.assert_allowed(path)
