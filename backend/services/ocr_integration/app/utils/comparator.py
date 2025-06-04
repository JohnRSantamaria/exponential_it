import difflib


def are_similar(a: str, b: str, threshold: float = 0.9) -> bool:
    """Compara dos strings y retorna True si son al menos `threshold` similares."""
    if not a or not b:
        return False
    return (
        difflib.SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()
        >= threshold
    )
