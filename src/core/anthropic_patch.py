"""
Anthropic module patch to prevent proxy parameter injection.
This module should be imported BEFORE any other imports of anthropic.
"""

import sys
import os

def patch_anthropic():
    """
    Patch the Anthropic module to prevent proxy parameter injection.
    This must be called before importing anthropic anywhere else.
    """
    
    # Clear proxy environment variables first
    proxy_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'
    ]
    
    for var in proxy_vars:
        os.environ.pop(var, None)
    
    # Set NO_PROXY to everything
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    
    # Now patch the anthropic module if it's already imported
    if 'anthropic' in sys.modules:
        import anthropic
        
        # Save the original Anthropic class
        if not hasattr(anthropic, '_OriginalAnthropic'):
            anthropic._OriginalAnthropic = anthropic.Anthropic
            
            # Create a patched version that filters out 'proxies'
            class PatchedAnthropic:
                def __init__(self, **kwargs):
                    # Remove 'proxies' if it exists
                    filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'proxies'}
                    
                    # Create the actual client
                    self._client = anthropic._OriginalAnthropic(**filtered_kwargs)
                
                def __getattr__(self, name):
                    return getattr(self._client, name)
            
            # Replace the Anthropic class
            anthropic.Anthropic = PatchedAnthropic

# Auto-patch on import
patch_anthropic()