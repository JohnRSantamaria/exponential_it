# applications\core\services\scheduled_activity.py
from datetime import datetime, timedelta


def check_activity_overlap(day, start_time, duration, current_id=None):
    """
    Verifica que no haya solapamiento ni que se exceda del día.
    """
    dummy_start = datetime(2000, 1, 1, start_time.hour, start_time.minute)
    dummy_end = dummy_start + timedelta(minutes=duration)
    end_time = dummy_end.time()

    if end_time < start_time:
        raise ValueError("La actividad termina después de medianoche.")

    from schedule.models import ScheduledActivity

    overlaps = ScheduledActivity.objects.filter(day=day).exclude(pk=current_id)

    for other in overlaps:
        other_start = other.start_time
        other_end = other.end_time
        if start_time < other_end and end_time > other_start:
            raise ValueError(
                f"Se solapa con {other.activity.name} ({other_start}–{other_end})"
            )
