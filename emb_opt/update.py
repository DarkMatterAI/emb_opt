# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/08_update.ipynb.

# %% auto 0
__all__ = ['UpdateModule', 'UpdatePlugin', 'UpdatePluginGradientWrapper', 'TopKDiscreteUpdate', 'TopKContinuousUpdate',
           'RLUpdate']

# %% ../nbs/08_update.ipynb 3
from .imports import *
from .utils import compute_rl_grad, query_to_rl_inputs
from .module import Module
from .schemas import Item, Query, Batch, UpdateFunction, UpdateResponse

# %% ../nbs/08_update.ipynb 5
class UpdateModule(Module):
    def __init__(self, function: UpdateFunction):
        super().__init__(UpdateResponse, function)
        
    def gather_inputs(self, batch: Batch) -> (List[Tuple], List[Query]):
        idxs, inputs = batch.flatten_queries()
        return (idxs, inputs)
    
    def scatter_results(self, inputs: List[Query], results: List[UpdateResponse]) -> Batch:
        id_dict = {i.id : i for i in inputs}
        
        new_queries = []
        for result in results:
            query = result.query
            parent_query = id_dict.get(result.parent_id, None)
            if parent_query is not None:
                query.update_internal(parent_id=parent_query.id, 
                                      collection_id=parent_query.internal.collection_id)

            new_queries.append(query)
            
        return Batch(queries=new_queries)
    
    def __call__(self, batch: Batch) -> Batch:
        
        idxs, inputs = self.gather_inputs(batch)
        results = self.function(inputs)
        results = self.validate_schema(results)
        new_batch = self.scatter_results(inputs, results)
        return new_batch

# %% ../nbs/08_update.ipynb 9
class UpdatePlugin():
    '''
    UpdatePlugin - documentation for plugin functions to `UpdateFunction`
    
    A valid `UpdateFunction` is any function that maps `List[Query]` to 
    `List[Query]`. The inputs will be given as `Query` objects. 
    The outputs can be either a list of `Query` objects or a list of 
    valid json dictionaries that match the `Query` schema. The number of 
    outputs can be different from the number of inputs
    
    Item schema:
    
    `{
        'id' : Optional[Union[str, int]]
        'item' : Optional[Any],
        'embedding' : List[float],
        'score' : float,
        'data' : Optional[Dict],
    }`
    
    
    Query schema:
    
    `{
        'item' : Optional[Any],
        'embedding' : List[float],
        'data' : Optional[Dict],
        'query_results': List[Item]
    }`
    
    UpdateResponse schema:
    
    `{
        'query' : Query,
        'parent_id' : Optional[str],
    }`
    
    Input schema:
    
    `List[Query]`

    Output schema:
    
    `List[UpdateResponse]`
    
    '''
    def __call__(self, inputs: List[Query]) -> List[UpdateResponse]:
        pass

# %% ../nbs/08_update.ipynb 10
class UpdatePluginGradientWrapper():
    '''
    UpdatePluginGradientWrapper - this class wraps a valid 
    `UpdateFunction` to estimate the gradient of new queries 
    using the results and scores computed for the parent query.
    
    This wrapper integrates with `DataPluginGradWrapper`, which 
    allows us to create new query vectors based on the gradient
    '''
    def __init__(self, 
                 function: UpdateFunction,                          # `UpdateFunction` to wrap
                 distance_penalty: float=0,                         # RL grad distance penalty
                 max_norm: Optional[float] = None,                  # max grad norm
                 norm_type: Optional[Union[float, int, str]] = 2.0  # grad norm type
                ):
        
        self.function = function
        self.distance_penalty = distance_penalty
        self.max_norm = max_norm
        self.norm_type = norm_type
        
    def __call__(self, inputs: List[Query]) -> List[UpdateResponse]:
        outputs = self.function(inputs)
        
        id_dict = {i.id : i for i in inputs}
        
        for update_result in outputs:
            query = update_result.query
            parent_id = update_result.parent_id
            parent = id_dict.get(parent_id, None)
            if parent:
                _, result_embeddings, scores = query_to_rl_inputs(parent)
                query_embedding = np.array(query.embedding)
                grad = compute_rl_grad(query_embedding, 
                                       result_embeddings, 
                                       scores,
                                       distance_penalty=self.distance_penalty,
                                       max_norm=self.max_norm, 
                                       norm_type=self.norm_type,
                                       score_grad=True
                                      )
            else:
                grad = np.zeros(np.array(query.embedding).shape)
                
            update_result.query.data['_score_grad'] = grad
            
        return outputs

# %% ../nbs/08_update.ipynb 12
class TopKDiscreteUpdate(UpdatePlugin):
    '''
    TopKDiscreteUpdate - discrete update that 
    generates `k` new queries from the top `k` 
    scoring items in each input query
    '''
    def __init__(self, 
                 k: int # top k items to return as new queries
                ):
        self.k = k
        
    def __call__(self, inputs: List[Query]) -> List[UpdateResponse]:
        outputs = []
        
        for query in inputs:
            result_scores = np.array([i.score for i in query.valid_results()])
            topk_idxs = result_scores.argsort()[::-1][:self.k]
            top_items = [query[i] for i in topk_idxs]
            outputs += top_items
            
        outputs = [UpdateResponse(query=Query.from_item(i), parent_id=i.internal.parent_id) 
                                  for i in outputs]
        return outputs

# %% ../nbs/08_update.ipynb 14
class TopKContinuousUpdate():
    '''
    TopKContinuousUpdate - continuous update that 
    generates 1 new query by averaging the top `k` 
    scoring item embeddings for each input query
    '''
    def __init__(self, 
                 k: int # top k items to average
                ):
        self.k = k
        
    def __call__(self, inputs: List[Query]) -> List[UpdateResponse]:
        outputs = []
        
        for query in inputs:
            result_scores = np.array([i.score for i in query.valid_results()])
            topk_idxs = result_scores.argsort()[::-1][:self.k]
            topk_embs = np.array([query[i].embedding for i in topk_idxs])
            
            new_embedding = np.average(topk_embs, 0)
            output = UpdateResponse(query=Query.from_parent_query(embedding=new_embedding, 
                                                                  parent_query=query),
                                    parent_id=query.id)
            outputs.append(output)
        return outputs

# %% ../nbs/08_update.ipynb 16
class RLUpdate():
    '''
    RLUpdate - uses reinforcement learning to update queries
    
    To compute the gradient with RL:
    1. compute advantages by whitening scores
        1. `advantage[i] = (scores[i] - scores.mean()) / scores.std()`
    2. compute advantage loss
        1. `advantage_loss[i] = advantage[i] * (query_embedding - result_embedding[i])**2`
    3. compute distance loss
        1. `distance_loss[i] = distance_penalty * (query_embedding - result_embedding[i])**2`
    4. sum loss terms
        1. `loss[i] = advantage_loss[i] + distance_loss[i]`
    5. compute the gradient
    
    This gives a closed for calculation of the gradient as:
    
    `grad[i] = 2 * (advantage[i] + distance_penalty) * (query_embedding - result_embedding[i])`    
    '''
    def __init__(self,
                 lrs: Union[List[float], np.ndarray],            # list of learning rates
                 distance_penalty: float,                        # distance penalty coefficient
                 max_norm: Optional[float]=None,                 # optional max grad norm for clipping
                 norm_type: Optional[Union[float, int, str]]=2.0 # norm type
                ):
        self.lrs = np.array(lrs)
        self.distance_penalty = distance_penalty
        self.max_norm = max_norm
        self.norm_type = norm_type
        
    def compute_grad(self, query: Query):
        query_embedding, result_embeddings, scores = query_to_rl_inputs(query)
        
        grad = compute_rl_grad(query_embedding, result_embeddings, scores, 
                               self.distance_penalty, self.max_norm, self.norm_type)
        
        return grad
        
    def __call__(self, queries: List[Query]) -> List[UpdateResponse]:
        
        results = []
        
        for query in queries:
            grad = self.compute_grad(query)
            query_embedding = np.array(query.embedding)
            new_embeddings = query_embedding[None] - (grad[None] * self.lrs[:,None])  # (1,n) - (1,n) * (k,1)
            
            for i in range(new_embeddings.shape[0]):
                assert new_embeddings[i].shape == query_embedding.shape
                
                new_query = Query.from_parent_query(embedding=new_embeddings[i].tolist(), 
                                                    parent_query=query)
                
                new_query.data['rl_update_details'] = {
                                                        'parent_embedding' : query_embedding.tolist(),
                                                        'lr' : self.lrs[i],
                                                        'grad' : grad.tolist(),
                                                    }
                
                results.append(UpdateResponse(query=new_query, parent_id=query.id))
                
        return results
