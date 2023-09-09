# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_module.ipynb.

# %% auto 0
__all__ = ['Module']

# %% ../nbs/03_module.ipynb 3
from .imports import *
from .schemas import Batch

# %% ../nbs/03_module.ipynb 4
class Module():
    def __init__(self, 
                 output_schema: BaseModel,
                 function: Callable[List[BaseModel], List[BaseModel]], 
                ):
        self.output_schema = output_schema
        self.function = function
        
    def gather_inputs(self, batch: Batch) -> (List[Tuple], List[BaseModel]):
        raise NotImplementedError
        
    def validate_schema(self, results: List[BaseModel]) -> List[BaseModel]:
        results = [self.output_schema.model_validate(i) for i in results]
        return results
        
    def scatter_results(self, batch: Batch, idxs: List[Tuple], results: List[BaseModel]) -> None:
        raise NotImplementedError
        
    def __call__(self, batch: Batch) -> Batch:
        
        idxs, inputs = self.gather_inputs(batch)
        results = self.function(inputs)
        results = self.validate_schema(results)
        self.scatter_results(batch, idxs, results)
        return batch
