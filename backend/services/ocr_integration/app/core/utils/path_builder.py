from datetime import date

MONTHS = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


class PathBuilder:

    def build(self, date: date):
        year = date.year
        quarter = f"Q{(date.month - 1) // 3 + 1}"
        month = f"{str(date.month).zfill(2)}-{MONTHS[date.month]}"
        remote_path = f"/{year}/{quarter}/{month}"
        return remote_path
