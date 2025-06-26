def calculate_tax_percentage_candidates(
    amount_untaxed: float, amount_total: float, amount_tax: float
) -> set:
    TAX_STANDARD_RATES = [0.0, 4.0, 10.0, 21.0]

    def normalize(value: float, tolerance: float = 0.03) -> float:
        """
        Redondea a una tasa estándar si está dentro del margen de tolerancia,
        de lo contrario mantiene el valor con dos decimales.
        """
        rounded = round(value, 2)
        for standard in TAX_STANDARD_RATES:
            if abs(rounded - standard) <= tolerance:
                return standard
        return rounded

    percentages = []

    try:
        if amount_untaxed:
            percentages.append(normalize((amount_tax / amount_untaxed) * 100))
            percentages.append(
                normalize(((amount_total - amount_untaxed) / amount_untaxed) * 100)
            )
        if amount_total and amount_tax:
            amount_untaxed_est = amount_total - amount_tax
            if amount_untaxed_est:
                percentages.append(normalize((amount_tax / amount_untaxed_est) * 100))
    except ZeroDivisionError:
        pass

    return set(percentages)
