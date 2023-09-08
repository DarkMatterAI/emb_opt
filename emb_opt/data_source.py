# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_data_source.ipynb.

# %% auto 0
__all__ = ['DataSourceModule', 'NumpyPlugin', 'HugggingfaceDataPlugin']

# %% ../nbs/03_data_source.ipynb 3
from .imports import *
from .core import Module, build_batch_from_embeddings
from .schemas import Item, Query, Batch, DataSourceFunction, DataSourceResponse

# %% ../nbs/03_data_source.ipynb 4
class DataSourceModule(Module):
    def __init__(self,
                 function: DataSourceFunction,
                ):
        super().__init__(DataSourceResponse, function)
        
    def gather_inputs(self, batch: Batch) -> (List[Tuple], List[Query]):
        idxs, inputs = batch.flatten_queries()
        return (idxs, inputs)
    
    def scatter_results(self, batch: Batch, idxs: List[Tuple], results: List[DataSourceResponse]):
        for (q_idx, r_idx), result in zip(idxs, results):
            batch_item = batch.get_item(q_idx, r_idx)
            if result.data:
                batch_item.data.update(result.data)

            if result.valid:
                if result.query_results:
                    batch_item.add_query_results(result.query_results)

                else:
                    batch_item.data['_internal']['remove'] = True
                    batch_item.data['_internal']['remove_details'] = 'query returned no results'

            else:
                batch_item.data['_internal']['remove'] = True
                batch_item.data['_internal']['remove_details'] = 'query response invalid'

# %% ../nbs/03_data_source.ipynb 6
class NumpyPlugin():
    def __init__(self, embeddings, k, embedding_data=None, distance_metric='euclidean'):
        self.embeddings = embeddings
        self.distance_metric = distance_metric
        self.k = k
        self.embedding_data = embedding_data

    def __call__(self, inputs: List[Query]) -> List[DataSourceResponse]:
        queries = np.array([i.embedding for i in inputs])
        
        distances = cdist(queries, self.embeddings, metric=self.distance_metric)
        topk = distances.argsort(-1)[:, :self.k]
        
        outputs = []
        for i in range(len(inputs)):
            items = []
            for j in topk[i]:
                item_data = dict(self.embedding_data[j]) if self.embedding_data else None
                item = Item(embedding=self.embeddings[j], data=item_data)
                item.data['_internal']['query_distance'] = distances[i,j]
                items.append(item)
            result = DataSourceResponse(valid=True, data=None, query_results=items)
            outputs.append(result)
            
        return outputs

# %% ../nbs/03_data_source.ipynb 14
class HugggingfaceDataPlugin():
    def __init__(self, dataset, index_name, k):
        self.dataset = dataset
        self.index_name = index_name
        self.k = k
        self.index = self.dataset.get_index(index_name)
        
    def __call__(self, inputs: List[Query]) -> List[DataSourceResponse]:
        queries = np.array([i.embedding for i in inputs])
        
        res = self.index.search_batch(queries, k=self.k)

        distances = res.total_scores
        indices = res.total_indices
        
        outputs = []
        for i in range(indices.shape[0]):
            items = []
            for j in range(indices.shape[1]):
                db_idx = indices[i, j]

                data_dict = dict(self.dataset[int(db_idx)])
                embedding = data_dict.pop(self.index_name)

                item = Item(embedding=embedding, data=data_dict)
                item.data['_internal']['query_distance'] = distances[i, j]
                items.append(item)

            result = DataSourceResponse(valid=True, data=None, query_results=items)
            outputs.append(result)
            
        return outputs
