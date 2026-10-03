# rthook.py
# This script runs at application startup to patch the transformers library.

import sys

# Demucs vocal isolation runs as a worker process of this same executable, and
# it never imports transformers. Skipping the patch there avoids paying the
# transformers import cost (and the startup messages) for every separation,
# which matters because stream mode spawns one demucs worker per audio chunk.
_IS_DEMUCS_WORKER = '--run-demucs-worker' in sys.argv

if not _IS_DEMUCS_WORKER:
    print("--- Executing runtime hook to patch transformers library ---")
    print(f"Python executable: {sys.executable}")
    print("Please note this may take longer on first run as it initializes the frozen environment.")
    print("Reruns after this will be faster since it'll be starting from a cached state.")
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
