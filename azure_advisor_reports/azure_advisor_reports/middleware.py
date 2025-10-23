"""
Custom middleware for Azure Advisor Reports Platform.
"""


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers for Azure AD popup authentication.

    This middleware ensures that Cross-Origin-Opener-Policy (COOP) headers
    allow popup-based authentication with Azure AD.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Allow popups for Azure AD authentication
        # Set COOP to same-origin-allow-popups for development
        if not response.has_header('Cross-Origin-Opener-Policy'):
            response['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'

        # Ensure CORS headers are set for Azure AD
        if not response.has_header('Cross-Origin-Embedder-Policy'):
            response['Cross-Origin-Embedder-Policy'] = 'unsafe-none'

        return response
