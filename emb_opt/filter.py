# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_filter.ipynb.

# %% auto 0
__all__ = ['Filter']

# %% ../nbs/01_filter.ipynb 3
from .imports import *
from .utils import QueryDataset

# %% ../nbs/01_filter.ipynb 4
class Filter():
    def __init__(self, 
                 filter_func: Callable,
                 filter_kwargs_dict: Optional[dict]=None
                ):
        self.filter_func = filter_func
        self.filter_kwargs_dict = filter_kwargs_dict if filter_kwargs_dict else {}
        
    def __call__(self, query_dataset:QueryDataset) -> QueryDataset:
        return query_dataset.filter(lambda item: self.filter_func(item), **self.filter_kwargs_dict)
