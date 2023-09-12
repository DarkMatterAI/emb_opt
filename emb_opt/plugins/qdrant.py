# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/plugins/01_qdrant.ipynb.

# %% auto 0
__all__ = ['QdrantDataPlugin']

# %% ../../nbs/plugins/01_qdrant.ipynb 3
from ..imports import *
from ..schemas import Query, Item, DataSourceResponse
from ..utils import build_batch_from_embeddings
from ..data_source import DataSourcePlugin, DataSourceModule

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except:
    warnings.warn('Failed to import Qdrant client - check package install')

# %% ../../nbs/plugins/01_qdrant.ipynb 5
class QdrantDataPlugin(DataSourcePlugin):
    '''
    QdrantDataPlugin - data plugin for working with 
    a qdrant vector database.
    
    The data query will run `k` nearest neighbors against the 
    qdrant collection `collection_name`
    
    Optionally, `item_key` denotes the key in an object's payload 
    corresponding to the item value
    
    `search_request_kwargs` are optional kwargs sent to 
    `models.SearchRequest`
    '''
    def __init__(self,
                 k: int,                                     # k nearest neighbors to return
                 collection_name: str,                       # qdrant collection name
                 qdrant_client: QdrantClient,                # qdrant client
                 item_key: Optional[str]=None,               # key in qdrant payload denoting item value
                 search_request_kwargs: Optional[dict]=None  # optional kwargs for `SearchRequest`
                ):
        
        self.k = k
        self.collection_name = collection_name
        self.qdrant_client = qdrant_client
        self.item_key = item_key
        self.search_request_kwargs = search_request_kwargs if search_request_kwargs else {}
        
    def __call__(self, inputs: List[Query]) -> List[DataSourceResponse]:
        
        search_queries = [models.SearchRequest(vector=i.embedding,
                                               limit=self.k,
                                               with_payload=True,
                                               with_vector=True,
                                               **self.search_request_kwargs
                                              )
                          for i in inputs]
        
        res = self.qdrant_client.search_batch(collection_name=self.collection_name, requests=search_queries)
        
        outputs = []
        for query_idx, result_batch in enumerate(res):
            items = []
            query_data = {'query_distance':[]}
            for query_result in result_batch:
                payload = query_result.payload
                item_value = payload.pop(self.item_key) if self.item_key is not None else None
                item = Item(id=query_result.id,
                            item=item_value,
                            embedding=query_result.vector,
                            score=None,
                            data=payload
                           )
                items.append(item)
                query_data['query_distance'].append(query_result.score)
                
            result = DataSourceResponse(valid=bool(items), data=query_data, query_results=items)
            outputs.append(result)
            
        return outputs
