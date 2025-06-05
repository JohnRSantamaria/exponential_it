# app/core/base_models.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Any, Dict


class BaseSanitizedModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    def clean_payload(self) -> Dict[str, Any]:
        """
        Retorna un dict limpio:
        - excluye None, strings vacíos y listas vacías
        - convierte datetime y date a ISO 8601
        """

        def is_useful(value: Any) -> bool:
            if value is None:
                return False
            if isinstance(value, str) and value.strip() == "":
                return False
            if isinstance(value, list) and len(value) == 0:
                return False
            return True

        raw = self.model_dump(exclude_none=True)

        cleaned = {}
        for k, v in raw.items():
            if not is_useful(v):
                continue
            if isinstance(v, (datetime, date)):
                cleaned[k] = v.isoformat()
            else:
                cleaned[k] = v

        return cleaned
