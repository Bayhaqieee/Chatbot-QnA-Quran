# Quranic QnA Chatbot using Transformers (T5, BART, Pegasus)

Welcome to **Quranic QnA Chatbot**! This project focuses on building a Question and Answer chatbot based on the Quran using large language models. The chatbot is trained on a synthetic reasoning dataset and Quranic verses in English, enabling it to answer Quran-related questions using natural language understanding.

## Live Dataset

You can access the datasets used in this project through the following links:

* [Quranic Reasoning Synthetic Dataset (Kaggle)](https://www.kaggle.com/datasets/lazer999/quranic-reasoning-synthetic-dataset)
* [Quran in English (Kaggle)](https://www.kaggle.com/datasets/alizahidraja/quran-english)

## Project Status

🚧 **Status**: `In Progress - T5, BART, and Pegasus Implemented`

## Features

Here's a breakdown of the current implementation and features:

* **Data Loading and Preprocessing**

  * Load datasets using `kagglehub` and prepare them for training and evaluation.

* **Modeling with Transformers**

  * **T5**: Fine-tuned using `T5ForConditionalGeneration`
  * **BART**: Implemented with `BartForConditionalGeneration`
  * **Pegasus**: Integrated using `PegasusForConditionalGeneration`

* **Training Setup**

  * Data splitting using `train_test_split`
  * Custom `Dataset` class and PyTorch `DataLoader`
  * Training loop using `AdamW` optimizer
  * Support for running on GPU with PyTorch

* **Evaluation**

  * Quality of generated answers is measured using BLEU and ROUGE scores.

* **Visualization**

  * Training and evaluation metrics visualized using `matplotlib`.

* **Model Comparison (Coming Soon)**

  * Comparative analysis between T5, BART, and Pegasus on performance and accuracy.

## Technologies Used

```python
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
```

## Setup & How to Run

1. Open the `.ipynb` file in Jupyter Notebook or Google Colab.
2. Authenticate with Kaggle API to download the required datasets.
3. Run all the cells sequentially.
4. Modify model choice, hyperparameters, or dataset paths as needed for experimentation.

⚠️ This notebook-based program can be run directly by executing all cells.

## Notes

* The chatbot currently supports T5, BART, and Pegasus for answer generation.
* Comparative evaluation and model performance summary are under development.

Feel free to fork this project, leave a ⭐, and contribute improvements or new models! 🙌
