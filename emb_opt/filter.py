# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/05_filter.ipynb.

# %% auto 0
__all__ = ['FilterModule', 'FilterPlugin', 'CompositeFilterPlugin']

# %% ../nbs/05_filter.ipynb 3
from .imports import *
from .module import Module
from .schemas import Item, Query, Batch, FilterFunction, FilterResponse

# %% ../nbs/05_filter.ipynb 5
class FilterModule(Module):
    def __init__(self,
                 function: FilterFunction # filter function
                ):
        super().__init__(FilterResponse, function)
        
    def gather_inputs(self, batch: Batch) -> (List[Tuple], List[Item]):
        idxs, inputs = batch.flatten_query_results()
        return (idxs, inputs)
        
    def scatter_results(self, batch: Batch, idxs: List[Tuple], results: List[FilterResponse]):
        for (q_idx, r_idx), result in zip(idxs, results):
            batch_item = batch.get_item(q_idx, r_idx)
            if result.data:
                batch_item.data.update(result.data)
                
            if not result.valid:
                batch_item.update_internal(removed=True, removal_reason='filter response invalid')
                
        for query in batch:
            query.update_internal()

# %% ../nbs/05_filter.ipynb 7
class FilterPlugin():
    '''
    FilterPlugin - documentation for plugin functions to `FilterFunction`
    
    A valid `FilterFunction` is any function that maps `List[Item]` to
    `List[FilterResponse]`. The inputs will be given as `Item` objects. 
    The outputs can be either a list of `FilterResponse` objects or a list 
    of valid json dictionaries that match the `FilterResponse` schema.
    
    Item schema:
    
    `{
        'id' : Optional[Union[str, int]]
        'item' : Optional[Any],
        'embedding' : List[float],
        'score' : None, # will be None at this stage
        'data' : Optional[Dict],
    }`
    
    Input schema:
    
    `List[Item]`
    
    FilterResponse schema:

    `{
        'valid' : bool,
        'data' : Optional[Dict],
    }`
    
    Output schema:
    
    `List[FilterResponse]`
    
    '''
    def __call__(self, inputs: List[Item]) -> List[FilterResponse]:
        pass

# %% ../nbs/05_filter.ipynb 9
class CompositeFilterPlugin():
    def __init__(self, 
                 functions: List[FilterFunction] # list of filter functions
                ):
        self.functions = functions
        
    def __call__(self, inputs: List[Item]) -> List[FilterResponse]:
        results = [func(inputs) for func in self.functions]
        
        outputs = []
        
        for i in range(len(inputs)):
            data = {'filter_results' : [result[i].model_dump() for result in results]}
            valid = all([result[i].valid for result in results])
                
            outputs.append(FilterResponse(valid=valid, data=data))
            
        return outputs
