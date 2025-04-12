# Quranic QnA Chatbot using T5

Welcome to **Quranic QnA Chatbot**! This project focuses on building a Question and Answer chatbot based on the Quran using large language models, starting with **T5** (Text-To-Text Transfer Transformer). The chatbot is trained on a synthetic reasoning dataset and Quranic verses in English, allowing it to answer questions about the Quran.

## Live Dataset

You can access the datasets used in this project through the following links:
- [Quranic Reasoning Synthetic Dataset (Kaggle)](https://www.kaggle.com/datasets/lazer999/quranic-reasoning-synthetic-dataset)
- [Quran in English (Kaggle)](https://www.kaggle.com/datasets/alizahidraja/quran-english)

## Project Status

🚧 **Status**: `In Progress - T5 Implemented, Testing Other LLMs Soon`

## Features

Here's a description of the current project implementation and features:

- **Data Loading and Preprocessing**
  - Loading datasets from Kaggle using `kagglehub` and formatting it for model training.

- **Modeling with T5**
  - Tokenization using `T5Tokenizer`
  - Fine-tuning `T5ForConditionalGeneration` model on the question-answer dataset

- **Training Setup**
  - Training and validation split using `train_test_split`
  - Custom Dataset class and PyTorch `DataLoader`
  - Training loop with optimizer `AdamW`

- **Evaluation**
  - Evaluation using BLEU and ROUGE scores to measure the quality of generated answers

- **Visualization**
  - Training progress and evaluation results visualized using `matplotlib`

- **Future Work**
  - Explore alternative models like **BART**, **LLaMa**, and other LLMs for improved performance

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
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer
```

## Setup & How to Run

1. Download the `.ipynb` notebook from the repository or open it in Google Colab.
2. Make sure to authenticate your Kaggle API to access the datasets.
3. Run all cells in the notebook sequentially.
4. Modify the dataset paths or batch size depending on your runtime environment.

⚠️ This program can be run directly on the `.ipynb` file altogether.

## Notes

- The chatbot currently uses the T5 model for generating answers.
- Integration and testing of other models like **BART** and **LLaMa** are planned in future iterations.

Feel free to fork the project, give it a ⭐, and contribute! 🙌

