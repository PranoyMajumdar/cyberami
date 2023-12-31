from __future__ import annotations

import asyncio
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import pandas as pd
import math

from datetime import timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

app = FastAPI()

# Step 0: Setup Helper functions


def get_system_uptime() -> str:
    """Function to get uptime"""
    with open('/proc/uptime', 'r', encoding='utf-8') as f:
        uptime_seconds: float = float(f.readline().split()[0])
        uptime_string: str = str(timedelta(seconds=uptime_seconds))
    return uptime_string


async def load_model_data():
    """Asynchronously load and preprocess data"""
    model_start_time = time.time()
    print("[Model] Started Processing Data...")
    data: pd.DataFrame = pd.read_csv("data/main.csv")
    data["Label"] = data["Label"].map({"bad": 0, "good": 1})
    X: pd.Series = data["URL"]
    Y: pd.Series = data["Label"]
    model: Pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('classifier', LogisticRegression(solver='lbfgs', max_iter=1000000))
    ])
    model.fit(X, Y)
    print("[Model] Processing Done...", math.floor(
        time.time() - model_start_time), end="s\n")
    return model

model_task = asyncio.create_task(load_model_data())


@app.get('/')
async def index(request: Request):
    """introduction, usage_time, uptime"""
    introduction: str = "Welcome to the Our API! This API provides information about phishing links. Go to `/checkurl`"
    usage_time: str = time.strftime("%Y-%m-%d %H:%M:%S")
    uptime: str = get_system_uptime()
    return {
        "introduction": introduction,
        "usage_time": usage_time,
        "uptime": uptime
    }


@app.get('/checkurl', response_class=JSONResponse)
async def check_url(request: Request, url: str = ""):
    """checkurl?url=...{ url, type }"""
    # Wait for the model to be loaded if not loaded yet
    model = await model_task
    prediction = model.predict([url])[0]
    return {"url": url, "type": "good" if prediction == 1 else "bad"}
