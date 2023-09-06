# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06_prune.ipynb.

# %% auto 0
__all__ = ['PruneModule']

# %% ../nbs/06_prune.ipynb 3
from .imports import *
from .core import Module
from .schemas import Item, Query, Batch, PruneFunction, PruneResponse

# %% ../nbs/06_prune.ipynb 4
class PruneModule(Module):
    def __init__(self,
                 function: PruneFunction,
                ):
        super().__init__(PruneResponse, function)
        
    def gather_inputs(self, batch: Batch) -> (List[Tuple], List[Query]):
        idxs, inputs = batch.flatten_queries()
        return (idxs, inputs)
    
    def scatter_results(self, batch: Batch, idxs: List[Tuple], results: List[PruneResponse]):
        for (q_idx, r_idx), result in zip(idxs, results):
            batch_item = batch.get_item(q_idx, r_idx)
            if result.data:
                batch_item.data.update(result.data)

            if not result.valid:
                batch_item.data['_internal']['remove'] = True
                batch_item.data['_internal']['remove_details'] = 'prune result invalid'
