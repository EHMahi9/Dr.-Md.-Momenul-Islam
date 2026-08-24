import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
model_name = "ai4bharat/indictrans2-indic-en-dist-200M"
print("Loading model...")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)
    print("Model loaded.")
    texts = ["এটা একটা পরীক্ষা", "paracetamol koto mg khabo", "what is this"]
    for t in texts:
        # indictrans2 typically expects src_lang and tgt_lang to be set, 
        # or we might need to prepend something like `<2en> <ben>` depending on the exact model.
        # But let's try direct first.
        inputs = tokenizer(t, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=50)
        print(f"'{t}' -> '{tokenizer.decode(outputs[0], skip_special_tokens=True)}'")
except Exception as e:
    print(f"Error: {e}")
