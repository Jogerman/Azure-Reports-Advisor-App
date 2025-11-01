# Authentication app for Azure AD integration

import logging
logger = logging.getLogger(__name__)

try:
    # Explicitly import authentication classes to ensure they're loaded
    from .authentication import JWTAuthentication, AzureADAuthentication
    logger.critical("=" * 80)
    logger.critical("SUCCESS: JWTAuthentication and AzureADAuthentication imported in __init__.py")
    logger.critical("=" * 80)
    __all__ = ['JWTAuthentication', 'AzureADAuthentication']
except Exception as e:
    logger.critical("=" * 80)
    logger.critical(f"ERROR importing authentication classes in __init__.py: {e}")
    logger.critical("=" * 80)
    import traceback
    logger.critical(traceback.format_exc())
    raise