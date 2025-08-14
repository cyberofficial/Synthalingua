# rthook.py
# This script runs at application startup to patch the transformers library.

import sys

print("--- Executing runtime hook to patch transformers library ---")
try:
    # The 'transformers' library uses inspect.getsource to build docstrings,
    # which fails in a frozen application because the .py files are not available.
    # We find the problematic function and replace it with a dummy that does nothing.
    from transformers.utils import doc

    # This is the function that causes the "OSError: could not get source code"
    def safe_get_docstring_indentation_level(docstring):
        """A safe replacement that doesn't read source code."""
        return 0  # Returning an integer 0 is the correct type.

    # Apply the patch
    doc.get_docstring_indentation_level = safe_get_docstring_indentation_level
    print("--- Successfully patched transformers.utils.doc to prevent source code lookup ---")

except Exception as e:
    # If the patching fails for any reason, print a warning but do not crash.
    print(f"--- WARNING: Runtime hook failed to patch transformers. Error: {e} ---", file=sys.stderr)