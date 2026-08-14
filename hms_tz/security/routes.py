"""Routes reachable on the site that no HMS workflow uses."""

ROUTE_BLOCKING_ENABLED = True

# Blocked for everyone. Frappe and ERPNext ship these; HMS routes to none of them.
# "_test" also covers Frappe's /_test* page tree, which renders raw template errors.
BLOCKED_ROUTES = frozenset(
    {
        "_test",
        "admissions",
        "backups",
        "blog",
        "first",
        "members",
        "partners",
        "project",
        "sitemap.xml",
        "student",
    }
)

BLOCKED_PREFIXES = ("_test",)

# Matched on two segments so /.well-known/security.txt stays reachable: Frappe serves
# it in app.py after before_request hooks run, so a bare ".well-known" block kills it.
BLOCKED_PATHS = frozenset({".well-known/openid-configuration"})

# Deliberately NOT blocked, all verifiably in use:
#   printview  - patient_encounter.js and patient_appointment.js print Sales Invoices
#   address, list, employee - portal routes
