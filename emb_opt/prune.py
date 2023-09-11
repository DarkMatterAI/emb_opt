# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/07_prune.ipynb.

# %% auto 0
__all__ = ['PruneModule', 'PrunePlugin', 'TopKGlobalPrune', 'TopKPruneLocal']

# %% ../nbs/07_prune.ipynb 3
from .imports import *
from .module import Module
from .schemas import Item, Query, Batch, PruneFunction, PruneResponse

# %% ../nbs/07_prune.ipynb 4
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
                batch_item.update_internal(removed=True, removal_reason='prune response invalid')

# %% ../nbs/07_prune.ipynb 6
class PrunePlugin():
    def __call__(self, inputs: List[Query]) -> List[PruneResponse]:
        pass

# %% ../nbs/07_prune.ipynb 7
class TopKGlobalPrune():
    def __init__(self,
                 k: int,
                 agg: str='mean'
                ):
        self.k = k
        self.agg = agg
        assert self.agg in ['mean', 'max']
        
    def prune_queries(self, queries: List[Query]) -> List[PruneResponse]:
        scores = []
        for query in queries:
            result_scores = np.array([i.score for i in query.valid_results()])
            if self.agg=='mean':
                result_scores = result_scores.mean()
            elif self.agg == 'max':
                result_scores = result_scores.max()
            scores.append(result_scores)
            
        scores = np.array(scores)
        topk_idxs = set(scores.argsort()[::-1][:self.k])
        
        outputs = [PruneResponse(valid=(i in topk_idxs), data={f'{self.agg}_score':scores[i]})
                  for i in range(len(queries))]
        
        return outputs
    
    def __call__(self, queries: List[Query]) -> List[PruneResponse]:
        outputs = self.prune_queries(queries)
            
        return outputs

# %% ../nbs/07_prune.ipynb 9
class TopKPruneLocal(TopKGlobalPrune):
    def __call__(self, queries: List[Query]) -> List[PruneResponse]:
        query_groups = defaultdict(list)
        idx_groups = defaultdict(list)
        
        outputs = [None for i in queries]
        
        for i, query in enumerate(queries):
            collection_id = query.internal.collection_id
            query_groups[collection_id].append(query)
            idx_groups[collection_id].append(i)
            
        for collection_id, query_list in query_groups.items():
            prune_results = self.prune_queries(query_list)
            scatter_idxs = idx_groups[collection_id]
            
            for i, result in enumerate(prune_results):
                outputs[scatter_idxs[i]] = result
                    
        return outputs
