
Here is an updated `README.md` for your Quranic QnA Chatbot project.

# Quranic QnA Chatbot using Transformers and a Multi-Agent RAG System

Welcome to  **Quranic QnA Chatbot** ! This project focuses on building a Question and Answer chatbot based on the Quran using large language models and a multi-agent Retrieval Augmented Generation (RAG) system. The chatbot is trained on a synthetic reasoning dataset and Quranic verses in English, enabling it to answer Quran-related questions using natural language understanding.

## Live Dataset

You can access the datasets used in this project through the following links:

* [Quranic Reasoning Synthetic Dataset (Kaggle)](https://www.kaggle.com/datasets/lazer999/quranic-reasoning-synthetic-dataset)
* [Quran in English (Kaggle)](https://www.kaggle.com/datasets/alizahidraja/quran-english)

## Project Status

🚧  **Status** : `In Progress - T5, BART, Pegasus, and Multi-Agent RAG Implemented`

## Features

Here's a breakdown of the current implementation and features:

* **Data Loading and Preprocessing** : Load datasets using `kagglehub` and prepare them for training and evaluation.
* **Modeling with Transformers** :
* **T5** : Fine-tuned using `T5ForConditionalGeneration`
* **BART** : Implemented with `BartForConditionalGeneration`
* **Pegasus** : Integrated using `PegasusForConditionalGeneration`
* **Multi-Agent RAG System** : A multi-agent system for retrieving relevant information from a vector store and generating answers.
* **Training Setup** :
* Data splitting using `train_test_split`
* Custom `Dataset` class and PyTorch `DataLoader`
* Training loop using `AdamW` optimizer
* Support for running on GPU with PyTorch
* **Evaluation** : Quality of generated answers is measured using BLEU and ROUGE scores.
* **Visualization** : Training and evaluation metrics visualized using `matplotlib`.
* **Model Comparison (Coming Soon)** : Comparative analysis between T5, BART, Pegasus, and the RAG system on performance and accuracy.

## Technologies Used

**Python**

```
import numpy as np
import matplotlib.pyplot as plt
import kagglehub
from kagglehub import KaggleDatasetAdapter
from google.colab import files
import os
import pathlib
import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import (
    T5Tokenizer, T5ForConditionalGeneration,
    BartTokenizer, BartForConditionalGeneration,
    PegasusTokenizer, PegasusForConditionalGeneration
)
import torch
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer
from pymilvus import MilvusClient
from flask import Flask, render_template, request, jsonify
```

## RAG Deployment

Access the repository

```
cd Agent
```

### 1. Docker Setup for Milvus and SearXNG

This project uses Milvus as a vector store and SearXNG as a search engine. You can run both services using Docker Compose.

First, create a `docker-compose.yml` file with the following content:

**YAML**

```
version: '3.5'

services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "9001:9001"
      - "9000:9000"
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/minio:/minio_data
    command: minio server /minio_data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  standalone:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.4.1
    command: ["milvus", "run", "standalone"]
    security_opt:
    - seccomp:unconfined
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/milvus:/var/lib/milvus
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      start_period: 90s
      timeout: 20s
      retries: 3
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"

  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
    restart: unless-stopped

networks:
  default:
    name: milvus
```

Then, run the following command to start the services:

**Bash**

```
docker-compose up -d
```

### 2. Virtual Environment and Dependencies

It is recommended to use a virtual environment to manage the project's dependencies.

First, create a virtual environment:

**Bash**

```
python -m venv venv
```

Next, activate the virtual environment.

**On Windows:**

**Bash**

```
venv\Scripts\activate
```

**On macOS and Linux:**

**Bash**

```
source venv/bin/activate
```

Finally, install the required packages from the `requirements.txt` file:

**Bash**

```
pip install -r requirements.txt
```

### 3. Ingesting Vector Data

Before running the application, you need to ingest the Quranic data into the Milvus vector store. You can do this by running the `data_pipeline.py` script:

**Bash**

```
python data_pipeline.py
```

This script will download the Quranic dataset, process it, generate vector embeddings, and insert them into the Milvus collection.

### 4. Deploying the Web Application

The web application is built with Flask. To run the application, use the following command:

**Bash**

```
flask --app app run
```

The application will be available at `http://127.0.0.1:5000`.

## Notes

* T5, BART, Pegasus are all a scratch builded chatbot, so its only implemented on Notebook.
* The chatbot currently supports a multi-agent RAG system for answer generation.
* Comparative evaluation and model performance summary are under development.

Feel free to fork this project, leave a ⭐, and contribute improvements or new models! 🙌
