"""Request-level security controls, registered as `before_request` hooks."""

import frappe
from werkzeug.exceptions import NotFound

from hms_tz.security.routes import BLOCKED_PATHS, BLOCKED_PREFIXES, BLOCKED_ROUTES, ROUTE_BLOCKING_ENABLED


def disable_traceback_leakage():
    """Keep server tracebacks out of every response.

    frappe.utils.response.is_traceback_allowed() ANDs on
    `not frappe.local.flags.disable_traceback`, so setting it here suppresses the JSON
    `exc` key, the HTML error page and the body of a 429 in one go. Error Log still
    records the full traceback server-side.
    """
    frappe.local.flags.disable_traceback = True


def block_unused_routes():
    """Return 404 for framework routes no HMS workflow uses.

    Raising NotFound here is caught by frappe.app, which returns the bare HTTP
    exception without rendering a template.
    """
    if not ROUTE_BLOCKING_ENABLED:
        return

    path = (frappe.local.request.path or "/").strip("/").lower()
    if not path:
        return

    if path in BLOCKED_PATHS:
        raise NotFound

    root = path.split("/", 1)[0]
    if root in BLOCKED_ROUTES or root.startswith(BLOCKED_PREFIXES):
        raise NotFound
