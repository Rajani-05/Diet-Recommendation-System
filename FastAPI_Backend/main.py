from fastapi import FastAPI
from pydantic import BaseModel, conlist
from typing import List, Optional
import pandas as pd
import os

# Limit OpenMP / BLAS threads to 1 — saves ~50 MB RAM on Render free tier
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from model import recommend, output_recommended_recipes

# Dataset path resolved relative to this file (works on Render)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load only needed columns with optimized dtypes to stay under 512MB on Render free tier
USED_COLS = [
    'Name', 'CookTime', 'PrepTime', 'TotalTime',
    'RecipeIngredientParts',
    'Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent',
    'SodiumContent', 'CarbohydrateContent', 'FiberContent', 'SugarContent',
    'ProteinContent', 'RecipeInstructions'
]
NUMERIC_COLS = [
    'Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent',
    'SodiumContent', 'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent'
]

# Use 50k-row sampled file (dataset_small.csv.gz) to stay within 512MB RAM limit.
# Falls back to full dataset.csv if the small one isn't present.
_small = os.path.join(BASE_DIR, "Data", "dataset_small.csv.gz")
_full  = os.path.join(BASE_DIR, "Data", "dataset.csv")

_path  = _small if os.path.exists(_small) else _full
_compression = "gzip"   # both files are gzip-compressed

dataset = pd.read_csv(
    _path,
    compression=_compression,
    usecols=lambda c: c in USED_COLS,
    encoding_errors='replace',
)

# Downcast numeric columns to float32 to halve memory usage
for col in NUMERIC_COLS:
    if col in dataset.columns:
        dataset[col] = pd.to_numeric(dataset[col], errors='coerce').astype('float32')

# Drop rows with any missing numeric values and free memory
dataset.dropna(subset=NUMERIC_COLS, inplace=True)
dataset.reset_index(drop=True, inplace=True)

app = FastAPI()

class Params(BaseModel):
    n_neighbors: int = 5
    return_distance: bool = False


class PredictionIn(BaseModel):
    nutrition_input: conlist(float, min_items=9, max_items=9)
    ingredients: List[str] = []
    params: Optional[Params]


class Recipe(BaseModel):
    Name: str
    CookTime: str
    PrepTime: str
    TotalTime: str
    RecipeIngredientParts: List[str]
    Calories: float
    FatContent: float
    SaturatedFatContent: float
    CholesterolContent: float
    SodiumContent: float
    CarbohydrateContent: float
    FiberContent: float
    SugarContent: float
    ProteinContent: float
    RecipeInstructions: List[str]


class PredictionOut(BaseModel):
    output: Optional[List[Recipe]] = None


@app.get("/")
def home():
    return {"health_check": "OK"}


@app.post("/predict/", response_model=PredictionOut)
def predict(prediction_input: PredictionIn):

    recommendation_dataframe = recommend(
        dataset,
        prediction_input.nutrition_input,
        prediction_input.ingredients,
        prediction_input.params.dict()
    )

    output = output_recommended_recipes(recommendation_dataframe)

    if output is None:
        return {"output": None}
    else:
        return {"output": output}