# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_schemas.ipynb.

# %% auto 0
__all__ = ['Embedding', 'DataSourceFunction', 'FilterFunction', 'ScoreFunction', 'Item', 'Query', 'Batch', 'DataSourceResponse',
           'FilterResponse', 'ScoreResponse']

# %% ../nbs/01_schemas.ipynb 3
from .imports import *

# %% ../nbs/01_schemas.ipynb 5
Embedding = List[float]

# %% ../nbs/01_schemas.ipynb 6
class Item(BaseModel):
    item: Optional[str]
    embedding: Embedding
    score: Optional[float]
    data: Optional[dict]
        
    @model_validator(mode='before')
    @classmethod
    def _fill_data(cls, inputs: Any) -> Any:
        if type(inputs)==dict:
            if inputs.get('data', None) is None:
                inputs['data'] = {}
                
            if '_internal' not in inputs['data']:
                inputs['data']['_internal'] = {'id' : str(uuid.uuid1())}

            if inputs.get('score', None) is None:
                inputs['score'] = None

            if inputs.get('item', None) is None:
                inputs['item'] = None

        return inputs

# %% ../nbs/01_schemas.ipynb 7
class Query(BaseModel):
    item: Optional[str]
    embedding: Optional[Embedding]
    data: Optional[dict]
    query_results: Optional[list[Item]]
        
    @model_validator(mode='before')
    @classmethod
    def _fill_data(cls, inputs: Any) -> Any:
        if inputs.get('data', None) is None:
            inputs['data'] = {}
            
        if '_internal' not in inputs['data']:
            inputs['data']['_internal'] = {'id' : str(uuid.uuid1())}
        
        if inputs.get('query_results', None) is None:
            inputs['query_results'] = []
            
        if inputs.get('item', None) is None:
            inputs['item'] = None

        return inputs
    
    def __iter__(self):
        return iter(self.query_results)

    def __getitem__(self, idx: int):
        return self.query_results[idx]
    
    def __len__(self):
        return len(self.query_results)
    
    def add_query_results(self, query_results: List[Item]):
        query_id = self.data['_internal']['id']
        collection_idx = self.data['_internal'].get('collection_index', None)
        for result in query_results:
            result.data['_internal']['parent'] = query_id
            result.data['_internal']['collection_index'] = collection_idx
            self.query_results.append(result)

# %% ../nbs/01_schemas.ipynb 8
class Batch(BaseModel):
    queries: List[Query]
        
    def __iter__(self):
        return iter(self.queries)

    def __getitem__(self, idx: int):
        return self.queries[idx]
    
    def __len__(self):
        return len(self.queries)
    
    def get_item(self, query_index, result_index=None):
        if result_index is not None:
            return self.queries[query_index][result_index]
        else:
            return self.queries[query_index]
    
    def enumerate_queries(self):
        for i, query in enumerate(self.queries):
            yield ((i,None), query)
            
    def enumerate_query_results(self):
        for i, query in enumerate(self.queries):
            for j, result in enumerate(query):
                yield ((i,j), result)
                
    def flatten_queries(self):
        idxs = []
        outputs = []
        for i, q in self.enumerate_queries():
            idxs.append(i)
            outputs.append(q)
        return idxs, outputs
                
    def flatten_query_results(self):
        idxs = []
        outputs = []
        for i, r in self.enumerate_query_results():
            idxs.append(i)
            outputs.append(r)
        return idxs, outputs
    
    def clean_queries(self, remove_empty=False):
        keep = []
        remove = []
        for query in self.queries:
            if query.data['_internal'].get('remove', False) or (remove_empty and len(query)==0):
                remove.append(query)
            else:
                keep.append(query)
        self.queries = keep
        return remove
    
    def clean_results(self):
        remove = []
        for query in self.queries:
            keep = []
            for result in query:
                if result.data['_internal'].get('remove', False):
                    remove.append(result)
                else:
                    keep.append(result)
                    
            query.query_results = keep
            
        return remove

# %% ../nbs/01_schemas.ipynb 10
class DataSourceResponse(BaseModel):
    valid: bool
    data: Optional[Dict]
    query_results: List[Item]

# %% ../nbs/01_schemas.ipynb 11
DataSourceFunction = Callable[List[Query], List[DataSourceResponse]]

# %% ../nbs/01_schemas.ipynb 13
class FilterResponse(BaseModel):
    valid: bool
    data: Optional[dict]
        
    @model_validator(mode='before')
    @classmethod
    def _fill_data(cls, data: Any) -> Any:
        if "data" not in data:
            data["data"] = None
        return data

# %% ../nbs/01_schemas.ipynb 14
FilterFunction = Callable[List[Item], List[FilterResponse]]

# %% ../nbs/01_schemas.ipynb 16
class ScoreResponse(BaseModel):
    valid: bool
    score: float
    data: Optional[dict]
        
    @model_validator(mode='before')
    @classmethod
    def _fill_data(cls, data: Any) -> Any:
        if "data" not in data:
            data["data"] = None
        return data

# %% ../nbs/01_schemas.ipynb 17
ScoreFunction = Callable[List[Item], List[ScoreResponse]]