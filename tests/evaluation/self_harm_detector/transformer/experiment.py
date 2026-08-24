import os
import time
import json
import torch
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score, accuracy_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from normalizer import normalize # csebuetnlp required normalizer

# --- Configuration ---
DATASET_FILE = '../../BanglaSuicidalTextCorpus.csv'
MODEL_CHECKPOINT = "csebuetnlp/banglabert_small"
SEED = 42
LABEL_MAP = {"no risk": 0, "low risk": 1, "high risk": 2}
INV_LABEL_MAP = {0: "no risk", 1: "low risk", 2: "high risk"}

def prepare_mock_data():
    np.random.seed(SEED)
    mock_data = {
        'text': [
            "আমার জীবনে আর কিছু নেই, আমি মরে যাব।", "আমি আজ রাতে আত্মহত্যা করব।", # High risk
            "জীবনটা খুব কষ্টের, ভালো লাগে না।", "মনটা খুব খারাপ আজকে।", # Low risk
            "আমি আজ বাজারে যাব।", "আজকের আবহাওয়া অনেক সুন্দর।" # No risk
        ] * 850, # 5100 total
        'label': ["high risk", "high risk", "low risk", "low risk", "no risk", "no risk"] * 850
    }
    return pd.DataFrame(mock_data)

# --- 1. Data Loading & Preprocessing ---
if not os.path.exists(DATASET_FILE):
    print("Mocking Dataset for offline script compilation...")
    df = prepare_mock_data()
else:
    df = pd.read_csv(DATASET_FILE)

# Apply specific BanglaBERT normalization (removes zero-width characters, standardizes unicode)
df['text'] = df['text'].astype(str).apply(lambda x: normalize(x.strip()))
df['label_id'] = df['label'].map(LABEL_MAP)

X = df['text'].tolist()
y = df['label_id'].tolist()

# Train/Val/Test Split (70/15/15)
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=SEED, stratify=y)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=SEED, stratify=y_temp)

# --- 2. Tokenization ---
tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)

class SuicideDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels):
        self.encodings = tokenizer(texts, truncation=True, padding=True, max_length=128)
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = SuicideDataset(X_train, y_train)
val_dataset = SuicideDataset(X_val, y_val)
test_dataset = SuicideDataset(X_test, y_test)

# --- 3. Model Setup & Class Weights ---
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Calculate Class Weights to handle slight imbalance (if any)
from sklearn.utils.class_weight import compute_class_weight
class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(device)

# Custom Trainer to override loss with class weights
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        loss_fct = torch.nn.CrossEntropyLoss(weight=class_weights_tensor)
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

model = AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT, num_labels=3)

training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    learning_rate=2e-5,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    seed=SEED
)

trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset
)

# --- 4. Training ---
# Uncomment to execute full training
# print("Starting Training...")
# trainer.train()

# --- 5. Inference & Metrics ---
# Uncomment to execute inference
# print("Starting Inference...")
# start_time = time.time()
# preds = trainer.predict(test_dataset)
# y_pred = np.argmax(preds.predictions, axis=-1)
# inference_time = time.time() - start_time
# avg_latency = (inference_time / len(y_test)) * 1000

# print(f"Average Inference Latency: {avg_latency:.2f} ms")
# print(classification_report(y_test, y_pred, target_names=["no risk", "low risk", "high risk"]))
# print("Confusion Matrix:")
# print(confusion_matrix(y_test, y_pred))
