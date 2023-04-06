# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/07_runner.ipynb.

# %% auto 0
__all__ = ['SearchLog', 'Runner']

# %% ../nbs/07_runner.ipynb 3
from .imports import *
from .utils import pack_dataset
from .core import VectorDatabase, Score, Filter, PassThroughFilter
from .query_update import QueryUpdate

# %% ../nbs/07_runner.ipynb 4
class SearchLog():
    def __init__(self):
        self.batch_log = {}
        
    def add_entry(self, 
                  iteration: int, 
                  query_vectors: np.ndarray, 
                  query_results: Dataset
                 ):
        self.batch_log[iteration] = {'queries' : query_vectors, 'results' : query_results}
        
    def compile_results(self) -> Dataset:
        results = []
        seen_keys = set()

        for k,v in self.batch_log.items():
            query_results = v['results']

            for row in query_results.to_list():
                if not (row['db_idx'] in seen_keys):
                    row.pop('query_idx')
                    row.pop('distance')
                    results.append(row)
                    seen_keys.update({row['db_idx']})

        return Dataset.from_list(results)
    
    def compile_trajectories(self) -> dict:
        
        n_queries = self.batch_log[0]['queries'].shape[0]
        n_iters = len(self.batch_log.keys())
        trajectories = {i:{'query_vectors':[], 'scores':[]} for i in range(n_queries)}
        
        for iteration in range(n_iters):
            queries = self.batch_log[iteration]['queries']
            score_dict = pack_dataset(self.batch_log[iteration]['results'], 'query_idx', ['score'])
            
            for query_idx in range(n_queries):
                trajectories[query_idx]['query_vectors'].append(queries[query_idx])
                trajectories[query_idx]['scores'].append(score_dict[query_idx]['score'])

        for query_idx in range(n_queries):
            trajectories[query_idx]['query_vectors'] = np.stack(trajectories[query_idx]['query_vectors'])
            
        return trajectories

# %% ../nbs/07_runner.ipynb 5
class Runner():
    def __init__(self, 
                 vector_db: VectorDatabase, 
                 score: Score, 
                 query_update: QueryUpdate, 
                 filter: Optional[Filter]=None
                ):
        
        self.vector_db = vector_db
        self.score = score
        self.query_update = query_update
        self.filter = filter if filter else PassThroughFilter()
        
    def search(self, 
               query_vectors: np.ndarray, 
               iterations: int
              ) -> SearchLog:
        log = SearchLog()
        
        for i in range(iterations):
            query_results = self.vector_db.query(query_vectors)
            query_results = self.filter(query_results)
            query_results = self.score(query_results)
            
            log.add_entry(i, query_vectors, query_results)
            
            query_vectors = self.query_update(query_vectors, query_results)
            
        return log