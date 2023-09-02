# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_schemas.ipynb.

# %% auto 0
__all__ = ['Item']

# %% ../nbs/01_schemas.ipynb 3
from .imports import *

# %% ../nbs/01_schemas.ipynb 5
class Item(BaseModel):
    item: Optional[str]
    embedding: list[float]
    score: Optional[float]
    data: Optional[dict]
