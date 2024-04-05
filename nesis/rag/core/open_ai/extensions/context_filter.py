from typing import Optional, Dict, List

from pydantic import BaseModel, Field


class ContextFilter(BaseModel):
    docs_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, List[str]]] = None
