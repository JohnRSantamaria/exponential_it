from enum import Enum


class AddressTypeEnum(str, Enum):
    contact = "contact"  # Detalles de contacto (CEO, CFO, etc.)
    invoice = "invoice"  # Dirección de facturación
    delivery = "delivery"  # Dirección de entrega/envío
    private = "private"  # Dirección privada (visible solo a usuarios autorizados)
    other = "other"  # Otras direcciones (subsidiarias, etc.)


class AddressTypeEnum(str, Enum):
    contact = "contact"  # Detalles de contacto (CEO, CFO, etc.)
    invoice = "invoice"  # Dirección de facturación
    delivery = "delivery"  # Dirección de entrega/envío
    private = "private"  # Dirección privada (solo visible a usuarios autorizados)
    other = "other"  # Otras direcciones (subsidiarias, etc.)


class CompanyTypeEnum(str, Enum):
    company = "company"  # Empresa (jurídica)
    person = "person"  # Persona natural
