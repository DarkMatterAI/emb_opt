from typing import Union, Optional, Callable, Tuple, Any, List, Dict
import warnings
from collections import defaultdict
import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import uuid

# external
import numpy as np
from scipy.spatial.distance import cdist
import datasets
from datasets import Dataset
import pandas as pd
from pydantic import BaseModel, RootModel, field_validator, model_validator