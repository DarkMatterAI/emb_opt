# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/07_runner.ipynb.

# %% auto 0
__all__ = ['SearchLog', 'Runner']

# %% ../nbs/07_runner.ipynb 3
from .imports import *
from .utils import pack_dataframe
from .core import VectorDatabase, Score, Filter, PassThroughFilter
from .query_update import QueryUpdate

from .backends.hf import HFDatabase
from .query_update import RLUpdate

# %% ../nbs/07_runner.ipynb 4
class SearchLog():
    'Logs results from `Runner`'
    def __init__(self):
        self.batch_log = {}
        
    def add_entry(self, 
                  iteration: int, 
                  query_vectors: np.ndarray, 
                  query_results: Dataset
                 ):
        self.batch_log[iteration] = {'queries' : query_vectors, 'results' : query_results.to_pandas()}
        
    def compile_results(self) -> Dataset:
        results = []
        seen_keys = set()

        for k,v in self.batch_log.items():
            query_results = v['results']

            for idx, row in query_results.iterrows():
                row = dict(row)
                if not (row['db_idx'] in seen_keys):
                    row.pop('query_idx')
                    row.pop('distance')
                    results.append(row)
                    seen_keys.update({row['db_idx']})

        output = Dataset.from_list(results)
        output = output.sort('score', reverse=True)
        return output
    
    def compile_trajectories(self) -> dict:
        
        n_queries = self.batch_log[0]['queries'].shape[0]
        n_iters = len(self.batch_log.keys())
        trajectories = {i:{'query_vectors':[], 'scores':[]} for i in range(n_queries)}
        
        for iteration in range(n_iters):
            queries = self.batch_log[iteration]['queries']
            score_dict = pack_dataframe(self.batch_log[iteration]['results'], 'query_idx', ['score'])
            
            for query_idx in range(n_queries):
                trajectories[query_idx]['query_vectors'].append(queries[query_idx])
                trajectories[query_idx]['scores'].append(score_dict[query_idx]['score'])

        for query_idx in range(n_queries):
            trajectories[query_idx]['query_vectors'] = np.stack(trajectories[query_idx]['query_vectors'])
            
        return trajectories

# %% ../nbs/07_runner.ipynb 6
class Runner():
    'Runs embedding optimization search'
    def __init__(self, 
                 vector_db: VectorDatabase, # vector database backend
                 score: Score, # score function
                 query_update: QueryUpdate, # query update
                 filter: Optional[Filter]=None # optional filter
                ):
        
        self.vector_db = vector_db
        self.score = score
        self.query_update = query_update
        self.filter = filter if filter else PassThroughFilter()
        
    def step(self, iteration, query_vectors, log=None):
        query_results = self.vector_db.query(query_vectors)
        query_results = self.filter(query_results)
        query_results = self.score(query_results)

        if log:
            log.add_entry(iteration, query_vectors, query_results)

        query_vectors = self.query_update(query_vectors, query_results)
        return query_vectors
        
    def search(self, 
               query_vectors: np.ndarray, 
               iterations: int
              ) -> SearchLog:
        log = SearchLog()
        
        for i in range(iterations):
            query_vectors = self.step(i, query_vectors, log)
            
        return log
