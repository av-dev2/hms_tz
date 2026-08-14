from __future__ import unicode_literals

import frappe
from frappe.utils.telemetry import capture

# Not cacheable: get_boot() embeds a per-session CSRF token in the rendered page.
cache = 0


def get_context():
    context = get_boot()
    if frappe.session.user != "Guest":
        capture("active_site", "frontend")

    return context


def get_boot():
    return frappe._dict(
        {
            "default_route": "/frontend",
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
            "csrf_token": frappe.sessions.get_csrf_token(),
        }
    )
