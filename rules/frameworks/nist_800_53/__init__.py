from .nist_framework import NIST80053Framework

# Create framework instance
nist_framework = NIST80053Framework()

# For backward compatibility, provide the old NIST_CONTROLS list
NIST_CONTROLS = nist_framework.get_all_controls()

# Export the framework for new usage
__all__ = ['NIST80053Framework', 'nist_framework', 'NIST_CONTROLS'] 