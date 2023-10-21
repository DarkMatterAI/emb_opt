from typing import Union, Optional, Callable, Tuple, Any, List, Dict
import warnings
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import uuid

# external
import numpy as np
from scipy.spatial.distance import cdist
from pydantic import BaseModel, RootModel, field_validator, model_validator