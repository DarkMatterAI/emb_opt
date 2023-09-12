# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/plugins/00_hf.ipynb.

# %% auto 0
__all__ = ['DatasetExecutor', 'HugggingfaceDataPlugin']

# %% ../../nbs/plugins/00_hf.ipynb 3
from ..imports import *
from ..schemas import Query, Item, DataSourceResponse
from ..data_source import DataSourcePlugin, DataSourceModule
from ..executor import Executor
from ..utils import build_batch_from_embeddings

try:
    import datasets
    from datasets import Dataset
except:
    warnings.warn('Failed to import Datasets library - check package install')

# %% ../../nbs/plugins/00_hf.ipynb 5
class DatasetExecutor(Executor):
    '''
    DatasetExecutor - executes function in parallel 
    using `Dataset.map`
    '''
    def __init__(self,
                 function: Callable,              # function to be wrapped
                 batched: bool,                   # if inputs should be batched
                 batch_size: int=1,               # batch size (set batch_size=0 to pass all inputs)
                 concurrency: Optional[int]=1,    # number of concurrent threads
                 map_kwargs: Optional[dict]=None  # kwargs for `Dataset.map`
                ):
        
        self.function = function
        self.batched = batched
        self.concurrency = concurrency
        self.batch_size = batch_size
        self.map_kwargs = map_kwargs if map_kwargs else {}
        
    def batch_inputs(self, inputs: List[BaseModel]):
        dataset = datasets.Dataset.from_list([i.model_dump() for i in inputs])
        return dataset
            
    def unbatch_inputs(self, dataset):
        return dataset.to_list()

    def execute(self, dataset):
        dataset = dataset.map(lambda row: self.function(row), batched=self.batched, 
                             batch_size=self.batch_size, num_proc=self.concurrency, **self.map_kwargs)
        return dataset

# %% ../../nbs/plugins/00_hf.ipynb 8
class HugggingfaceDataPlugin(DataSourcePlugin):
    '''
    HugggingfaceDataPlugin - data plugin for working with 
    huggingface datasets library.
    
    The input `dataset` should have a faiss embedding index 
    denoted by `index_name`.
    
    The data query will run `k` nearest neighbors against the 
    dataset index based on the metric used to create the index
    
    Optionally, `item_key` denotes the column in `dataset` defining a 
    specific item, and `id_key` denotes the column defining an item's ID
    '''
    def __init__(self,
                 k: int,                       # k nearest neighbors to return
                 dataset: datasets.Dataset,    # input dataset
                 index_name: str,              # name of the faiss index in `dataset`
                 item_key: Optional[str]=None, # dataset column denoting item value
                 id_key: Optional[str]=None    # dataset column denoting item id
                ):
        
        self.k = k
        self.dataset = dataset
        self.index_name = index_name
        self.index = self.dataset.get_index(index_name)
        self.item_key = item_key
        self.id_key = id_key
        
    def __call__(self, inputs: List[Query]) -> List[DataSourceResponse]:
        queries = np.array([i.embedding for i in inputs])
        
        res = self.index.search_batch(queries, k=self.k)
        distances = res.total_scores
        indices = res.total_indices
        
        outputs = []
        for i in range(indices.shape[0]):
            items = []
            query_data = {'query_distance' : []}
            for j in range(indices.shape[1]):
                query_data['query_distance'].append(distances[i,j])
                
                dataset_index = indices[i, j]
                item_data = dict(self.dataset[int(dataset_index)])
                embedding = item_data.pop(self.index_name)
                item = item_data.pop(self.item_key) if self.item_key else None
                item_id = item_data.pop(self.id_key) if self.id_key else None
                
                item = Item(id=item_id, 
                            item=item,
                            embedding=embedding, 
                            data=item_data, 
                            score=None)
                items.append(item)
                
            result = DataSourceResponse(valid=True, data=query_data, query_results=items)
            outputs.append(result)
            
        return outputs       
