# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/04_huggingface.ipynb.

# %% auto 0
__all__ = ['HFDatabase']

# %% ../../nbs/04_huggingface.ipynb 3
from ..imports import *
from ..core import QueryResult, VectorDatabase, dataset_from_query_results

# %% ../../nbs/04_huggingface.ipynb 5
class HFDatabase(VectorDatabase):
    def __init__(self, 
                 dataset: Dataset, # `Dataset` with built vector index
                 index_name: str, # name of vector index
                 k: int, # returns `k` values per query vector
                ):
        'Huggingface backend'
        
        self.dataset = dataset
        self.index_name = index_name
        self.k = k
        
    def query(self, query_vectors: np.ndarray) -> Dataset:
        
        index = self.dataset.get_index(self.index_name)
        
        res = index.search_batch(query_vectors, k=self.k)
        distances = res.total_scores
        indices = res.total_indices
        
        n_queries, n_results = indices.shape
        
        results = []
        for query_idx in range(n_queries):
            for result_idx in range(n_results):
                db_idx = indices[query_idx, result_idx]
                
                data_dict = self.dataset[int(db_idx)]
                embedding = data_dict.pop(self.index_name)
                
                distance = distances[query_idx, result_idx]
                
                result = QueryResult(query_idx, db_idx, embedding, distance, data_dict)
                results.append(result)
                
        return dataset_from_query_results(results)
