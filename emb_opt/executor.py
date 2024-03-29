# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_executor.ipynb.

# %% auto 0
__all__ = ['Executor', 'ProcessExecutor', 'ThreadExecutor', 'APIExecutor']

# %% ../nbs/02_executor.ipynb 3
from .imports import *
import httpx
import asyncio
from .utils import batch_list, unbatch_list

# %% ../nbs/02_executor.ipynb 5
class Executor():
    '''
    Basic Executor class. Batches inputs, sends 
    batches to `function`, unbatches outputs
    '''
    def __init__(self, 
                 function: Callable, # function to be wrapped
                 batched: bool,      # if inputs should be batched
                 batch_size: int=1   # batch size (set batch_size=0 to pass all inputs)
                ):
        self.function = function
        self.batched = batched
        self.batch_size = batch_size
    
    def batch_inputs(self, inputs: List[BaseModel]):
        if self.batched:
            inputs = batch_list(inputs, self.batch_size)
        return inputs
            
    def unbatch_inputs(self, results: List[BaseModel]):
        if self.batched:
            results = unbatch_list(results)
        return results

    def execute(self, inputs: List[BaseModel]):
        results = [self.function(i) for i in inputs]
        return results
        
    def __call__(self, inputs: List[BaseModel]) -> List[BaseModel]:
        
        inputs = self.batch_inputs(inputs)
        results = self.execute(inputs)
        results = self.unbatch_inputs(results)
            
        return results

# %% ../nbs/02_executor.ipynb 7
class ProcessExecutor(Executor):
    '''
    ProcessExecutor - executes function with 
    multiprocessing using `ProcessPoolExecutor`
    '''
    def __init__(self,
                 function: Callable,           # function to be wrapped
                 batched: bool,                # if inputs should be batched
                 batch_size: int=1,            # batch size (set batch_size=0 to pass all inputs)
                 concurrency: Optional[int]=1  # number of concurrent processes
                ):
        
        self.function = function
        self.batched = batched
        self.concurrency = concurrency
        self.batch_size = batch_size
        
    def execute(self, inputs: List[BaseModel]):
        if (self.concurrency is None) or (self.concurrency==1):
            results = [self.function(i) for i in inputs]
        else:
            with ProcessPoolExecutor(min(self.concurrency, len(inputs))) as p:
                results = list(p.map(self.function, inputs))
            
        return results

# %% ../nbs/02_executor.ipynb 9
class ThreadExecutor(Executor):
    '''
    ProcessExecutor - executes function with 
    multiple threads using `ThreadPoolExecutor`
    '''
    def __init__(self,
                 function: Callable,           # function to be wrapped
                 batched: bool,                # if inputs should be batched
                 batch_size: int=1,            # batch size (set batch_size=0 to pass all inputs)
                 concurrency: Optional[int]=1  # number of concurrent threads
                ):
        
        self.function = function
        self.batched = batched
        self.concurrency = concurrency
        self.batch_size = batch_size
        
    def execute(self, inputs: List[BaseModel]):
        if (self.concurrency is None) or (self.concurrency==1):
            results = [self.function(i) for i in inputs]
        else:
            with ThreadPoolExecutor(min(self.concurrency, len(inputs))) as p:
                results = list(p.map(self.function, inputs))
            
        return results

# %% ../nbs/02_executor.ipynb 11
class APIExecutor(Executor):
    def __init__(self,
                 url: str,                     # API URL
                 batch_size: int=1,            # batch size (set batch_size=0 to pass all inputs)
                 concurrency: Optional[int]=1  # number of concurrent threads
                ):
        
        self.url = url
        self.batched = True
        self.concurrency = concurrency
        self.batch_size = max(batch_size, 1)
        
    async def function(self, inputs: List[BaseModel], semaphore):
        if type(inputs[0]) == BaseModel:
            inputs = [i.model_dump() for i in inputs]
            
        async with semaphore:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.url, json=inputs)
                return response.json()
        
    async def execute_async(self, inputs: List[BaseModel]):
        semaphore = asyncio.Semaphore(self.concurrency)
        responses = await asyncio.gather(*(self.function(i, semaphore) for i in inputs))
        return responses
        
        
    def execute(self, inputs: List[BaseModel]):
        loop = asyncio.new_event_loop()
        results = loop.run_until_complete(self.execute_async(inputs))
        loop.close()
        return results
