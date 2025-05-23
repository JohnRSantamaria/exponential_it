# core/utils.py
from datetime import timedelta


def overlaps(start1, end1, start2, end2):
    return max(start1, start2) < min(end1, end2)
