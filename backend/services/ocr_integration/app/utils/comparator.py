import difflib
from typing import List


def are_similar(a: str, b: str, threshold: float = 0.9) -> bool:
    """Compara dos strings y retorna True si son al menos `threshold` similares."""
    if not a or not b:
        return False
    return (
        difflib.SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()
        >= threshold
    )


def all_similar(items: List[str], threshold: float = 0.9) -> bool:
    """Verifica si todos los elementos en la lista son similares entre sí."""
    if not items:
        return False
    base = items[0]
    return all(are_similar(base, item, threshold=threshold) for item in items[1:])
