# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/09_log.ipynb.

# %% auto 0
__all__ = ['Node', 'QueryTree', 'Log']

# %% ../nbs/09_log.ipynb 3
from .imports import *
from .schemas import Query, Batch

# %% ../nbs/09_log.ipynb 5
class Node():
    def __init__(self, query: Query, iteration: int):
        self.query = query
        self.iteration = iteration
        self.id = self.query.id
        self.parent = None
        self.children = {}
        self.prepare()
        
    def prepare(self):
        self.mean_score = None
        self.max_score = None
        self.removed = self.query.internal.removed
        
        result_scores = [i.score for i in self.query.valid_results() if (i.score is not None)]
        if result_scores:
            result_scores = np.array(result_scores)
            self.mean_score = result_scores.mean()
            self.max_score = result_scores.max()
            
    def add_child(self, child):
        child.parent = self
        self.children[child.id] = child
        
    def add_parent(self, parent):
        self.parent = parent
        parent.children[self.id] = self

# %% ../nbs/09_log.ipynb 6
class QueryTree():
    def __init__(self):
        self.id_dict = {}
        self.nodes = []
        self.root_nodes = []
        
    def add_node(self, query: Query, iteration: int):
        node = Node(query, iteration)
        parent_id = query.internal.parent_id
        parent = self.id_dict.get(parent_id, None)
        
        if parent is None:
            self.root_nodes.append(node)
        else:
            node.add_parent(parent)
            
        self.id_dict[node.id] = node
        self.nodes.append(node)
        
    def leaf_nodes(self, include_removed=False):
        for node in self.nodes:
            parent_check = node.parent is not None
            child_check = not node.children
            removed_check = True if include_removed else (not node.removed)
            if parent_check and child_check and removed_check:
                yield node
                
    def backtrack_node(self, node=None, node_id=None):
        if node_id is not None:
            node = self.id_dict.get(node_id)
            
        outputs = []
        current = node
        while current:
            outputs.append(current)
            current = current.parent
            
        return outputs 

# %% ../nbs/09_log.ipynb 8
class Log():
    def __init__(self):
        self.batch_log = []
        self.query_tree = QueryTree()
        
    def get_item(self, 
                 iteration: int, 
                 query_index: Optional[int]=None, 
                 result_index: Optional[int]=None):
        
        result = self.batch_log[iteration]
        
        if query_index is not None:
            result = result.queries[query_index]
            
        if result_index is not None:
            result = result.query_results[result_index]
        
        return result
    
    def add_batch(self, batch: Batch):
        iteration = len(self.batch_log)
        self.batch_log.append(batch)
        for query in batch:
            self.query_tree.add_node(query, iteration)

    def compile_results(self, skip_removed: bool=True):
        output_dict = {}
        for batch in self.batch_log:
            for _, result in batch.enumerate_query_results(skip_removed):
                result_dict = result.model_dump()
                if result_dict.get('internal', None) is not None:
                    result_dict.pop('internal')
                    
                output_dict[result.id] = result_dict
                
        results = sorted([i for i in output_dict.values()], 
                         key=lambda x: x['score'] if x['score'] else float('-inf'), reverse=True)
        return results
    
    def dump_batch_log(self):
        output = {'batch_log' : [i.model_dump() for i in self.batch_log]}
        return output
