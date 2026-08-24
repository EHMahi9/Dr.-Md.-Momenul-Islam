import os
import time
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

# --- Configuration ---
MODELS = {
    "BanglaBERT-small": "csebuetnlp/banglabert_small",
    "MuRIL": "google/muril-base-cased"
}

# --- Paired Dataset ---
# Creating a small, manually reviewed project benchmark for robustness tests.
PAIRED_DATA = [
    {
        "id": "1",
        "native": "আমার বুকে প্রচণ্ড ব্যথা হচ্ছে।",
        "romanized": "amar buke prochondo betha hocche.",
        "engineering_label": "EXPLICIT_MEDICAL_EMERGENCY",
        "ambiguity": "LOW"
    },
    {
        "id": "2",
        "native": "আমি আজ রাতে আত্মহত্যা করব।",
        "romanized": "ami aj rate attohotta korbo.",
        "engineering_label": "POTENTIAL_SELF_HARM",
        "ambiguity": "LOW"
    },
    {
        "id": "3",
        "native": "প্যারাসিটামল এর কাজ কি?",
        "romanized": "paracetamol er kaj ki?",
        "engineering_label": "MEDICATION_FACTUAL",
        "ambiguity": "LOW"
    },
    {
        "id": "4",
        "native": "আমার মাথা ব্যথা করতেসে, খুব খারাপ লাগতেসে।",
        "romanized": "amar matha betha kortese, khub kharap lagtese.",
        "engineering_label": "UNCERTAIN_HIGH_RISK",
        "ambiguity": "HIGH"
    }
]

# --- Helper Functions ---
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def run_evaluation():
    results = {}
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running on {device}\n")

    for model_name, checkpoint in MODELS.items():
        print(f"--- Evaluating {model_name} ---")
        try:
            tokenizer = AutoTokenizer.from_pretrained(checkpoint)
            model = AutoModel.from_pretrained(checkpoint).to(device)
            model.eval()
        except Exception as e:
            print(f"Could not load {checkpoint}. Please ensure internet connectivity and transformers installation.")
            continue

        frag_native = []
        frag_roman = []
        sim_scores = []
        latency_measurements = []

        for pair in PAIRED_DATA:
            native = pair['native']
            roman = pair['romanized']
            
            # Tokenization Fragmentation (Length of tokens vs word count)
            native_words = len(native.split())
            roman_words = len(roman.split())
            
            encoded_native = tokenizer(native, return_tensors='pt', padding=True, truncation=True)
            encoded_roman = tokenizer(roman, return_tensors='pt', padding=True, truncation=True)
            
            native_tokens = encoded_native['input_ids'].shape[1]
            roman_tokens = encoded_roman['input_ids'].shape[1]
            
            frag_native.append(native_tokens / max(native_words, 1))
            frag_roman.append(roman_tokens / max(roman_words, 1))

            # Embedding Similarity
            start_time = time.time()
            with torch.no_grad():
                encoded_native = {k: v.to(device) for k, v in encoded_native.items()}
                encoded_roman = {k: v.to(device) for k, v in encoded_roman.items()}
                
                out_native = model(**encoded_native)
                out_roman = model(**encoded_roman)
            latency_measurements.append(time.time() - start_time)

            emb_native = mean_pooling(out_native, encoded_native['attention_mask'])
            emb_roman = mean_pooling(out_roman, encoded_roman['attention_mask'])
            
            cosine_sim = F.cosine_similarity(emb_native, emb_roman).item()
            sim_scores.append(cosine_sim)

        avg_latency = (sum(latency_measurements) / len(latency_measurements)) * 1000
        
        results[model_name] = {
            "avg_frag_native": sum(frag_native)/len(frag_native),
            "avg_frag_roman": sum(frag_roman)/len(frag_roman),
            "avg_cosine_similarity": sum(sim_scores)/len(sim_scores),
            "avg_latency_ms": avg_latency,
            "model_size_mb": sum(p.numel() for p in model.parameters()) * 4 / (1024*1024)
        }
        
        print(f"Avg Fragmentation (Native): {results[model_name]['avg_frag_native']:.2f} tokens/word")
        print(f"Avg Fragmentation (Roman): {results[model_name]['avg_frag_roman']:.2f} tokens/word")
        print(f"Avg Semantic Similarity (Native vs Roman): {results[model_name]['avg_cosine_similarity']:.4f}")
        print(f"Inference Latency: {results[model_name]['avg_latency_ms']:.2f} ms")
        print(f"Model Size: {results[model_name]['model_size_mb']:.2f} MB\n")

if __name__ == "__main__":
    # In a full run, this would output the metrics
    # We provide this script for structural execution and evaluation
    pass
