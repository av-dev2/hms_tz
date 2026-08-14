"""Security baseline, re-applied on every migrate so no site drifts."""

import frappe

# allow_consecutive_login_attempts is what activates frappe's per-IP and per-user
# LoginAttemptTracker; at 0 both are inert and failed logins are unlimited.
SECURITY_BASELINE = {
    "allow_error_traceback": 0,
    "allow_consecutive_login_attempts": 5,
    "allow_login_after_fail": 900,
    "password_reset_limit": 2,
}

# frappe.www.contact.send_message is guest-callable and does not validate `subject`,
# which allows mail header injection. HMS does not use the public contact form.
CONTACT_US_BASELINE = {"is_disabled": 1}


def apply_security_settings():
    """Reset the Ministry of Health security baseline, overwriting any drift."""
    _apply("System Settings", SECURITY_BASELINE)
    _apply("Contact Us Settings", CONTACT_US_BASELINE)


def enforce_on_save(doc, method=None):
    """Hold the baseline whenever System Settings is saved.

    Login is authenticated in init_request, before before_request hooks run, so
    the disable_traceback flag cannot reach a failed login. allow_error_traceback
    is the only control for that endpoint, and it must not drift between migrates.
    """
    for field, value in SECURITY_BASELINE.items():
        if doc.get(field) != value:
            doc.set(field, value)


def _apply(doctype, baseline):
    settings = frappe.get_single(doctype)
    changed = {
        field: value
        for field, value in baseline.items()
        if settings.get(field) != value
    }
    if not changed:
        return

    settings.update(changed)
    settings.flags.ignore_permissions = True
    settings.save()
    frappe.logger().info(f"hms_tz: reset {doctype} {sorted(changed)}")
