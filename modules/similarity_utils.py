import difflib

def is_similar(a, b, threshold=0.85):
    """
    Returns True if the similarity ratio between a and b is above the threshold.
    """
    if not a or not b:
        return False
    return difflib.SequenceMatcher(None, a.strip(), b.strip()).ratio() >= threshold
