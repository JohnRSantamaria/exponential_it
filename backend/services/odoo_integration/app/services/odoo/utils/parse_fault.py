def parse_fault_string(fault: str) -> str:
    """
    Extrae el mensaje de error relevante de un faultString XML-RPC de Odoo y lo formatea bien.
    """
    # 1. Reemplazar \n y \t para que se vea bien
    clean_text = fault.replace("\\n", "\n").replace("\\t", "\t").replace("\\'", "'")

    lines = clean_text.splitlines()
    for line in reversed(lines):
        if "Error" in line or "Exception" in line or "ValueError" in line:
            return line.strip()

    return "Unknown Odoo error"
