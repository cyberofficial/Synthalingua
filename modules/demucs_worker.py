"""
Demucs entry point that also relaxes torch.load for shipped model checkpoints.

Frozen builds apply the same relaxation from the --run-demucs-worker dispatch in
synthalingua.py. Source builds run this script instead, so a local model repo
behaves identically in both modes.

demucs 4.0.1 loads local repo checkpoints with torch.load(path, 'cpu') without a
weights_only argument. PyTorch 2.6 changed that default to True, which makes the
official Meta demucs checkpoints fail with an UnpicklingError naming
demucs.htdemucs.HTDemucs. Those checkpoints are trusted (they ship with the app
or come from demucs' own model repository), so weights_only is defaulted back to
False for this process only.

Usage, equivalent to `python -m demucs`:
    python modules/demucs_worker.py -n htdemucs -o out --two-stems vocals file.wav
"""
import os
import sys

# Allow this file to be executed directly from any working directory
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def relax_torch_load():
    """Default torch.load to weights_only=False for trusted demucs checkpoints."""
    import torch

    original_load = torch.load

    def _demucs_torch_load(*args, **kwargs):
        kwargs.setdefault('weights_only', False)
        return original_load(*args, **kwargs)

    torch.load = _demucs_torch_load


def main():
    """Apply the torch.load relaxation, then run the demucs command line."""
    relax_torch_load()
    from demucs.separate import main as demucs_main
    demucs_main()


if __name__ == '__main__':
    main()
