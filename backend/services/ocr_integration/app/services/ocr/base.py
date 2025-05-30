# import json
# from fastapi.exceptions import RequestValidationError
# from typing import Dict

# from app.services.admin.schemas import CredentialOut
# from app.services.ocr.extractors import InvoiceExtractor


# def proces_document(payload: Dict, cif: CredentialOut):

#     extractor = InvoiceExtractor(json_data=parsed_payload, cif=cif)

#     main_fields = extractor.extract_main_fields()

#     lines = extract_lines(amount_total)

#     full_text = self.ocr_data.get("text", {}).get("text", "")

#     regex_factory = RegexExtractor()

#     valid_tax_identification = regex_factory.extract_all_patterns(text=full_text)

#     if tax_identification_supplier == self.cif or not tax_identification_supplier:

#         tax_identification_supplier = self.set_tax_identificacion_supplier(
#             valid_tax_identification, self.cif
#         )
