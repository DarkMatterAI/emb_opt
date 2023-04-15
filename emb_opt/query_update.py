# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_query_update.ipynb.

# %% auto 0
__all__ = ['QueryUpdate', 'RLUpdate', 'TopKUpdate']

# %% ../nbs/02_query_update.ipynb 3
from .imports import *
from .utils import pack_dataset, whiten
from .backends.hf import HFDatabase
from .core import Score

# %% ../nbs/02_query_update.ipynb 5
class QueryUpdate():
    'Query update base class'
    def __call__(self, 
                 query_vectors: np.ndarray, # query vectors
                 query_dataset: Dataset # scored dataset
                ) -> np.ndarray: # new query vectors
        return query_vectors

# %% ../nbs/02_query_update.ipynb 7
class RLUpdate(QueryUpdate):
    'Reinforcement Learning update'
    def __init__(self, 
                 lr: float, # learning rate
                 distance_penalty: float=0.0 # query distance penalty
                ):
        self.lr = lr
        self.distance_penalty = distance_penalty
        
    def __call__(self, 
                 query_vectors: np.ndarray, # query vectors
                 query_dataset: Dataset # scored dataset
                ) -> np.ndarray: # new query vectors
        
        packed_dict = pack_dataset(query_dataset, 'query_idx', ['embedding', 'score'])
        grads = []
        mean_embs = []
        
        for query_idx in range(query_vectors.shape[0]):
            if len(packed_dict[query_idx]['score'])>0:
                embs = np.array(packed_dict[query_idx]['embedding'])
                scores = np.array(packed_dict[query_idx]['score'])

                advantages = whiten(scores)
                grad = (advantages[:,None] * (2*(query_vectors[query_idx][None] - embs))).mean(0)
                
                mean_embs.append(2*(query_vectors[query_idx] - embs.mean(0)))
                
            else:
                # case where no results returned for vector
                grad = np.zeros(query_vectors[query_idx].shape)
                mean_embs.append(np.zeros(query_vectors[query_idx].shape))
                
            grads.append(grad)

        grads = np.array(grads)
        mean_embs = np.array(mean_embs)
        updated_query_vectors = query_vectors - self.lr*grads - self.distance_penalty*mean_embs
        return updated_query_vectors

# %% ../nbs/02_query_update.ipynb 11
class TopKUpdate(QueryUpdate):
    'Top K update'
    def __init__(self, 
                 k: int, # top k value
                 score_weighting: bool=True # if True, top k average is weighted by score
                ):
        self.k = k
        self.score_weighting = score_weighting
        
    def __call__(self, 
                 query_vectors: np.ndarray, # query vectors
                 query_dataset: Dataset # scored dataset
                ) -> np.ndarray: # new query vectors
        
        packed_dict = pack_dataset(query_dataset, 'query_idx', ['embedding', 'score'])
        new_queries = []
        
        for query_idx in range(query_vectors.shape[0]):
            if len(packed_dict[query_idx]['score'])>0:
                embs = np.array(packed_dict[query_idx]['embedding'])
                scores = np.array(packed_dict[query_idx]['score'])

                topk_idxs = scores.argsort()[::-1][:self.k]
                topk_embs = embs[topk_idxs]
                topk_scores = scores[topk_idxs]

                if self.score_weighting:
                    new_queries.append(np.average(topk_embs, 0, weights=topk_scores))
                else:
                    new_queries.append(np.average(topk_embs, 0))
            else:
                new_queries.append(query_vectors[query_idx])

        query_vectors = np.array(new_queries)
        
        return query_vectors
