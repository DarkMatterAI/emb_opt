from typing import Union, Optional, Callable, Tuple, Any, List, Dict
import warnings
from collections import defaultdict
import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# external
import numpy as np
import datasets
from datasets import Dataset
import pandas as pd
from pydantic import BaseModel, RootModel, field_validator, model_validator