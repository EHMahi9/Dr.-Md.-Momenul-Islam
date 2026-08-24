"""
Gate 5.12 — Phase 2 & 3: Controlled Improvement Candidate Implementation and DEV Evaluation
Evaluates 5 controlled strategies on the 40 DEV queries (DOC-NHS-004 to DOC-NHS-007).
"""

import json
import os
import re
import time
import math
import hashlib
import numpy as np
from collections import defaultdict
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
OPT_DIR = os.path.join(ROOT_DIR, "gate_5_9_optimization")
CHUNKS_FILE = os.path.join(OPT_DIR, "chunks", "hybrid_600", "provenance_manifest.json")
BENCHMARK_FILE = os.path.join(ROOT_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
GOLD_LABELS_FILE = os.path.join(OPT_DIR, "chunk_gold_labels.json")
EVAL_OUT_FILE = os.path.join(BASE_DIR, "..", "evaluations", "gate_5_12_dev_strategy_comparison.json")

DOC_TITLES = {
    "DOC-NHS-004": "Asthma",
    "DOC-NHS-005": "Burns and scalds",
    "DOC-NHS-006": "Cuts and grazes",
    "DOC-NHS-007": "Dehydration",
    "DOC-NHS-008": "Diarrhoea and vomiting",
    "DOC-NHS-009": "Headaches",
    "DOC-NHS-010": "High temperature (fever) in children",
    "DOC-NHS-011": "Anaphylaxis"
}

# Deterministic Clinical Concept Normalizer (Non-LLM, Rule-Based Dictionary)
BANGLA_BANGLISH_MAPPINGS = [
    (r'\b(pani\s*shunnota|pani\s*kom|dehydration|ডিহাইড্রেশন|পানিশূন্যতা)\b', 'dehydration fluid rehydration oral fluids'),
    (r'\b(shash\s*kosto|shash\s*nite\s*kosto|inhaler|asthma|হাঁপানি|শ্বাসকষ্ট|ইনহেলার)\b', 'asthma attack inhaler spacer breathing difficulty'),
    (r'\b(pura|pure\s*geche|burn|scald|blister|পুড়ে\s*গেলে|পোড়া|ফোস্কা)\b', 'burns scalds cold water cool running water blister first aid'),
    (r'\b(kete\s*geche|rokto|bleeding|cut|graze|antiseptic|কাটা|রক্তপাত|জীবাণুনাশক)\b', 'cuts grazes bleeding pressure clean dressing wound'),
    (r'\b(bomi|patla\s*paykhana|diarrhoea|vomiting|বমি|ডায়রিয়া|পাতলা\s*পায়খানা)\b', 'diarrhoea vomiting oral rehydration fluids'),
    (r'\b(matha\s*betha|headache|painkiller|paracetamol|মাথাব্যথা|প্যারাসিটামল)\b', 'headache pain relief painkillers paracetamol'),
    (r'\b(jor|fever|temperature|বাচ্চার\s*জ্বর|জ্বর)\b', 'fever high temperature children fluids paracetamol'),
    (r'\b(allergy|anaphylaxis|shash\s*bondho|অ্যালার্জি|অ্যানাফাইলাক্সিস)\b', 'anaphylaxis severe allergic reaction adrenaline 999'),
    (r'\b(emergency|999|hospital|duto|জরুরি|হাসপাতাল)\b', 'emergency call 999 go to A&E')
]

def normalize_query_text(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in BANGLA_BANGLISH_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        return f"{query} ({' '.join(norm_terms)})"
    return query

def extract_section_title(text: str) -> str:
    lines = text.strip().split("\n")
    first_line = lines[0].strip() if lines else ""
    if len(first_line) < 60 and not first_line.endswith("."):
        return first_line
    return "Overview and Guidance"

class BM25Okapi:
    def __init__(self, corpus_docs, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus_docs)
        self.tokenized_corpus = [self._tokenize(doc) for doc in corpus_docs]
        self.doc_lens = [len(doc) for doc in self.tokenized_corpus]
        self.avgdl = sum(self.doc_lens) / self.corpus_size if self.corpus_size > 0 else 1.0

        self.df = defaultdict(int)
        for doc in self.tokenized_corpus:
            for term in set(doc):
                self.df[term] += 1

        self.idf = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def _tokenize(self, text: str):
        return re.findall(r'[\w]+', text.lower())

    def get_scores(self, query: str):
        query_terms = self._tokenize(query)
        scores = np.zeros(self.corpus_size)

        for term in query_terms:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]
            for i, doc in enumerate(self.tokenized_corpus):
                if term not in doc:
                    continue
                tf = doc.count(term)
                denom = tf + self.k1 * (1 - self.b + self.b * (self.doc_lens[i] / self.avgdl))
                scores[i] += idf_val * (tf * (self.k1 + 1.0) / denom)

        return scores

def main():
    print("Loading data and models...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]
    unsupported_queries = [q for q in benchmark if q["expected_source_id"] == "NONE" and q["benchmark_split"] == "DEV"]
    if not unsupported_queries:
        # Check DEV hard negatives
        unsupported_queries = [q for q in benchmark if q["expected_source_id"] == "NONE"][:6]

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    # 1. Standard Passages
    standard_passages = [f"passage: {c['text']}" for c in chunks]
    emb_standard_passages = dense_model.encode(standard_passages, normalize_embeddings=True)

    # 2. Contextual Passages
    contextual_chunk_texts = []
    for c in chunks:
        sid = c["parent_source_id"]
        doc_title = DOC_TITLES.get(sid, c.get("source_title", "Medical Guidance"))
        sec_title = extract_section_title(c["text"])
        ctx_text = f"Topic: {doc_title} | Section: {sec_title}\n{c['text']}"
        contextual_chunk_texts.append(ctx_text)

    contextual_passages = [f"passage: {t}" for t in contextual_chunk_texts]
    emb_contextual_passages = dense_model.encode(contextual_passages, normalize_embeddings=True)

    # 3. BM25 Index
    bm25 = BM25Okapi([c["text"] for c in chunks])

    # 4. Standard Queries & Normalized Queries
    raw_query_texts = [q["query_text"] for q in dev_queries]
    norm_query_texts = [normalize_query_text(q["query_text"]) for q in dev_queries]

    emb_raw_queries = dense_model.encode([f"query: {t}" for t in raw_query_texts], normalize_embeddings=True)
    emb_norm_queries = dense_model.encode([f"query: {t}" for t in norm_query_texts], normalize_embeddings=True)

    # Similarity matrices
    sim_raw_std = np.dot(emb_raw_queries, emb_standard_passages.T)
    sim_norm_std = np.dot(emb_norm_queries, emb_standard_passages.T)
    sim_norm_ctx = np.dot(emb_norm_queries, emb_contextual_passages.T)
    sim_raw_ctx = np.dot(emb_raw_queries, emb_contextual_passages.T)

    strategies = [
        {
            "name": "CANDIDATE_1_GATE_5_11_BASELINE",
            "description": "Dense multilingual-e5-small Top-15 -> bge-reranker-v2-m3 Top-5 (Standard Passages)",
            "use_query_norm": False,
            "passage_mode": "standard",
            "use_bm25_union": False,
            "candidate_k": 15,
            "sim_matrix": sim_raw_std,
            "query_texts": raw_query_texts
        },
        {
            "name": "CANDIDATE_2_DETERMINISTIC_QUERY_NORM_K15",
            "description": "Deterministic Banglish/Bangla Normalization -> Dense Top-15 -> Reranker Top-5",
            "use_query_norm": True,
            "passage_mode": "standard",
            "use_bm25_union": False,
            "candidate_k": 15,
            "sim_matrix": sim_norm_std,
            "query_texts": norm_query_texts
        },
        {
            "name": "CANDIDATE_3_DENSE_BM25_HYBRID_UNION_K20",
            "description": "Dense + BM25 Candidate Union (K=20) -> Reranker Top-5",
            "use_query_norm": False,
            "passage_mode": "standard",
            "use_bm25_union": True,
            "candidate_k": 20,
            "sim_matrix": sim_raw_std,
            "query_texts": raw_query_texts
        },
        {
            "name": "CANDIDATE_4_CONTEXTUAL_PASSAGE_ENRICHMENT_K15",
            "description": "Contextual Passage Embeddings & Cross-Encoder Text (Title + Heading) -> Top-15 -> Reranker Top-5",
            "use_query_norm": False,
            "passage_mode": "contextual",
            "use_bm25_union": False,
            "candidate_k": 15,
            "sim_matrix": sim_raw_ctx,
            "query_texts": raw_query_texts
        },
        {
            "name": "CANDIDATE_5_SYNERGISTIC_UNIFIED_PIPELINE",
            "description": "Deterministic Query Normalization + Dense/BM25 Hybrid Union (K=20) + Contextual Passage Reranking",
            "use_query_norm": True,
            "passage_mode": "contextual",
            "use_bm25_union": True,
            "candidate_k": 20,
            "sim_matrix": sim_norm_ctx,
            "query_texts": norm_query_texts
        }
    ]

    all_results = {}

    print("\n" + "="*80)
    print("EVALUATING CONTROLLED CANDIDATES ON DEV SPLIT (N=40)")
    print("="*80)

    for strat in strategies:
        s_name = strat["name"]
        s_k = strat["candidate_k"]
        s_sim = strat["sim_matrix"]
        s_q_texts = strat["query_texts"]
        s_use_bm25 = strat["use_bm25_union"]
        s_ctx = (strat["passage_mode"] == "contextual")

        t0_strat = time.time()
        strat_query_evals = []

        for i, q in enumerate(dev_queries):
            qid = q["query_id"]
            raw_q = q["query_text"]
            eval_q = s_q_texts[i]
            lang = q["language_category"]
            expected_sid = q["expected_source_id"]
            gold_cids = gold_labels[qid]["gold_chunk_ids"]

            dense_scores = s_sim[i]

            if s_use_bm25:
                # Dense rank + BM25 rank RRF union
                dense_order = np.argsort(-dense_scores)
                bm25_scores = bm25.get_scores(eval_q)
                bm25_order = np.argsort(-bm25_scores)

                rrf_scores = np.zeros(len(chunks))
                for rank, idx in enumerate(dense_order):
                    rrf_scores[idx] += 1.0 / (60 + rank + 1)
                for rank, idx in enumerate(bm25_order):
                    rrf_scores[idx] += 1.0 / (60 + rank + 1)

                top_k_indices = np.argsort(-rrf_scores)[:s_k]
            else:
                top_k_indices = np.argsort(-dense_scores)[:s_k]

            candidate_cids = [chunks[idx]["chunk_id"] for idx in top_k_indices]

            # Cross-Encoder Reranking
            if s_ctx:
                pairs = [(eval_q, contextual_chunk_texts[idx]) for idx in top_k_indices]
            else:
                pairs = [(eval_q, chunks[idx]["text"]) for idx in top_k_indices]

            r_scores = reranker.predict(pairs)
            r_order = np.argsort(-r_scores)
            r_top_k_cids = [candidate_cids[idx] for idx in r_order]
            r_top_k_scores = [float(r_scores[idx]) for idx in r_order]

            final_top5_cids = r_top_k_cids[:5]
            final_top5_scores = r_top_k_scores[:5]

            # Candidate hits
            cand_hits = [cid in gold_cids for cid in candidate_cids]
            cand_r1 = cand_hits[0]
            cand_r3 = any(cand_hits[:3])
            cand_r5 = any(cand_hits[:5])
            cand_r10 = any(cand_hits[:10])
            cand_r15 = any(cand_hits[:15])
            cand_r20 = any(cand_hits[:20])
            cand_rank = (cand_hits.index(True) + 1) if any(cand_hits) else 0

            # Reranked hits
            r_hits = [cid in gold_cids for cid in final_top5_cids]
            r_r1 = r_hits[0]
            r_r3 = any(r_hits[:3])
            r_r5 = any(r_hits[:5])
            r_rank = (r_hits.index(True) + 1) if any(r_hits) else 0

            strat_query_evals.append({
                "query_id": qid,
                "query_text": raw_q,
                "language_category": lang,
                "expected_source_id": expected_sid,
                "gold_chunk_ids": gold_cids,
                "candidate_cids": candidate_cids,
                "final_top5_cids": final_top5_cids,
                "final_top5_scores": final_top5_scores,
                "cand_r1": cand_r1,
                "cand_r3": cand_r3,
                "cand_r5": cand_r5,
                "cand_r15": cand_r15,
                "cand_r20": cand_r20,
                "cand_rank": cand_rank,
                "rerank_r1": r_r1,
                "rerank_r3": r_r3,
                "rerank_r5": r_r5,
                "rerank_rank": r_rank
            })

        n = len(dev_queries)
        elapsed_s = time.time() - t0_strat

        # Aggregate Metrics
        c_r1 = sum(1 for r in strat_query_evals if r["cand_r1"])
        c_r5 = sum(1 for r in strat_query_evals if r["cand_r5"])
        c_r15 = sum(1 for r in strat_query_evals if r["cand_r15"])
        c_r20 = sum(1 for r in strat_query_evals if r["cand_r20"])
        c_mrr = sum(1.0 / r["cand_rank"] for r in strat_query_evals if r["cand_rank"] > 0) / n

        r_r1 = sum(1 for r in strat_query_evals if r["rerank_r1"])
        r_r3 = sum(1 for r in strat_query_evals if r["rerank_r3"])
        r_r5 = sum(1 for r in strat_query_evals if r["rerank_r5"])
        r_mrr = sum(1.0 / r["rerank_rank"] for r in strat_query_evals if r["rerank_rank"] > 0) / n

        # Linguistic Breakdown
        lang_breakdown = {}
        for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
            l_subs = [r for r in strat_query_evals if r["language_category"] == lang]
            ln = len(l_subs)
            lr_r1 = sum(1 for r in l_subs if r["rerank_r1"])
            lr_r3 = sum(1 for r in l_subs if r["rerank_r3"])
            lr_r5 = sum(1 for r in l_subs if r["rerank_r5"])
            lr_mrr = sum(1.0 / r["rerank_rank"] for r in l_subs if r["rerank_rank"] > 0) / ln
            lang_breakdown[lang] = {
                "n": ln,
                "r1": f"{lr_r1}/{ln} ({lr_r1/ln*100:.2f}%)",
                "r3": f"{lr_r3}/{ln} ({lr_r3/ln*100:.2f}%)",
                "r5": f"{lr_r5}/{ln} ({lr_r5/ln*100:.2f}%)",
                "mrr": round(lr_mrr, 4)
            }

        res_summary = {
            "strategy_name": s_name,
            "description": strat["description"],
            "candidate_depth_k": s_k,
            "elapsed_seconds": round(elapsed_s, 2),
            "avg_ms_per_query": round(elapsed_s / n * 1000, 2),
            "candidate_pool_metrics": {
                "r1": f"{c_r1}/{n} ({c_r1/n*100:.2f}%)",
                "r5": f"{c_r5}/{n} ({c_r5/n*100:.2f}%)",
                "r15": f"{c_r15}/{n} ({c_r15/n*100:.2f}%)",
                "r20": f"{c_r20}/{n} ({c_r20/n*100:.2f}%)",
                "mrr": round(c_mrr, 4)
            },
            "final_chunk_metrics": {
                "r1": f"{r_r1}/{n} ({r_r1/n*100:.2f}%)",
                "r3": f"{r_r3}/{n} ({r_r3/n*100:.2f}%)",
                "r5": f"{r_r5}/{n} ({r_r5/n*100:.2f}%)",
                "mrr": round(r_mrr, 4)
            },
            "language_breakdown": lang_breakdown,
            "query_evaluations": strat_query_evals
        }

        all_results[s_name] = res_summary

        print(f"\n[{s_name}]")
        print(f"  Candidate Pool: R@15={res_summary['candidate_pool_metrics']['r15']}, R@20={res_summary['candidate_pool_metrics']['r20']}")
        print(f"  Post-Rerank:    R@1={res_summary['final_chunk_metrics']['r1']} | R@3={res_summary['final_chunk_metrics']['r3']} | R@5={res_summary['final_chunk_metrics']['r5']} | MRR={res_summary['final_chunk_metrics']['mrr']}")
        print(f"  Bangla/Banglish R@5 Breakdown:")
        for l_k, l_v in lang_breakdown.items():
            print(f"    - {l_k}: R@5={l_v['r5']}, MRR={l_v['mrr']}")

    with open(EVAL_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved all DEV strategy comparisons to {EVAL_OUT_FILE}")

if __name__ == "__main__":
    main()
