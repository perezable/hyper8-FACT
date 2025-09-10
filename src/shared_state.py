"""
Shared state module for FACT system components.
This allows different modules to share instances like the enhanced retriever.
"""

import structlog

logger = structlog.get_logger(__name__)

# Shared enhanced retriever instance
_enhanced_retriever = None

def get_enhanced_retriever():
    """Get the shared enhanced retriever instance."""
    return _enhanced_retriever

def set_enhanced_retriever(retriever):
    """Set the shared enhanced retriever instance."""
    global _enhanced_retriever
    _enhanced_retriever = retriever
    if retriever:
        logger.info("Enhanced retriever set in shared state")
    else:
        logger.warning("Enhanced retriever cleared from shared state")

# Shared driver instance
_driver = None

def get_driver():
    """Get the shared driver instance."""
    return _driver

def set_driver(driver):
    """Set the shared driver instance."""
    global _driver
    _driver = driver