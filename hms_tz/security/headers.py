"""Response security headers, registered as an `after_request` hook."""

# camera and usb must stay allowed: patient authorization uses getUserMedia for facial
# recognition and local agents for the Mantra and DigitalPersona fingerprint readers.
# Denying either breaks admissions, lab and pharmacy.
PERMISSIONS_POLICY = (
    "camera=(self), "
    "usb=(self), "
    "fullscreen=(self), "
    "accelerometer=(), "
    "autoplay=(), "
    "display-capture=(), "
    "encrypted-media=(), "
    "geolocation=(), "
    "gyroscope=(), "
    "magnetometer=(), "
    "microphone=(), "
    "midi=(), "
    "payment=(), "
    "xr-spatial-tracking=()"
)

# No Content-Security-Policy: the fingerprint readers talk to local agents on
# localhost/127.0.0.1, so any connect-src a CSP could realistically set would break
# patient authorization. See the assessment response letter.


def apply_security_headers(response=None, request=None, **kwargs):
    """Add headers the site does not already serve, leaving existing ones untouched."""
    if response is None or not hasattr(response, "headers"):
        return

    response.headers.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
