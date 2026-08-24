"""
Gate 5.10 — Focused Strategy Evaluation Engine
1. Computes candidate pool metrics for all 16 candidate configurations (instantaneous).
2. Performs Cross-Encoder reranking on the 6 key comparative strategies.
"""

import json
import os
import time
import math
import re
import numpy as np
from collections import defaultdict
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
OPT_DIR = os.path.join(ROOT_DIR, "gate_5_9_optimization")
CHUNKS_FILE = os.path.join(OPT_DIR, "chunks", "hybrid_600", "provenance_manifest.json")
BENCHMARK_FILE = os.path.join(ROOT_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
GOLD_LABELS_FILE = os.path.join(OPT_DIR, "chunk_gold_labels.json")
BASELINE_FILE = os.path.join(BASE_DIR, "..", "baseline", "dev_baseline_reproduced.json")
EVAL_OUT_DIR = os.path.join(BASE_DIR, "..", "evaluations")

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
    print("Loading data and embedding models...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    with open(BASELINE_FILE, "r", encoding="utf-8") as f:
        baseline_results = json.load(f)
    baseline_top1 = {q["query_id"]: q["r5_chunk_r1"] for q in baseline_results}

    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")

    query_texts = [f"query: {q['query_text']}" for q in dev_queries]
    query_embeddings = dense_model.encode(query_texts, normalize_embeddings=True)

    # 1. Standard Passages Dense
    standard_passages = [f"passage: {c['text']}" for c in chunks]
    standard_chunk_embeddings = dense_model.encode(standard_passages, normalize_embeddings=True)
    sim_matrix_standard = np.dot(query_embeddings, standard_chunk_embeddings.T)

    # 2. Contextual Passages Dense
    contextual_passages = []
    for c in chunks:
        sid = c["parent_source_id"]
        doc_title = DOC_TITLES.get(sid, c.get("source_title", "Medical Guidance"))
        sec_title = extract_section_title(c["text"])
        ctx_text = f"Document: {doc_title} | Section: {sec_title} | Content: {c['text']}"
        contextual_passages.append(f"passage: {ctx_text}")

    contextual_chunk_embeddings = dense_model.encode(contextual_passages, normalize_embeddings=True)
    sim_matrix_contextual = np.dot(query_embeddings, contextual_chunk_embeddings.T)

    # 3. BM25 Index
    chunk_raw_texts = [c["text"] for c in chunks]
    bm25 = BM25Okapi(chunk_raw_texts)

    # === STEP 1: CANDIDATE POOL DIAGNOSTIC SUITE ===
    print("\n" + "="*80)
    print("STEP 1: CANDIDATE POOL RECALL DIAGNOSTICS ACROSS ALL CONFIGURATIONS")
    print("="*80)

    candidate_configs = [
        ("DENSE_STANDARD", sim_matrix_standard, False),
        ("DENSE_CONTEXTUAL", sim_matrix_contextual, False),
        ("HYBRID_BM25_STANDARD", sim_matrix_standard, True),
        ("HYBRID_BM25_CONTEXTUAL_COMBO", sim_matrix_contextual, True)
    ]

    candidate_diagnostics = {}

    for config_name, sim_mat, use_rrf in candidate_configs:
        cand_results = []
        for i, q in enumerate(dev_queries):
            qid = q["query_id"]
            q_text = q["query_text"]
            acceptable_cids = gold_labels[qid]["gold_chunk_ids"]
            dense_scores = sim_mat[i]

            if use_rrf:
                dense_rank_order = np.argsort(-dense_scores)
                bm25_scores = bm25.get_scores(q_text)
                bm25_rank_order = np.argsort(-bm25_scores)

                rrf_scores = np.zeros(len(chunks))
                for rank, idx in enumerate(dense_rank_order):
                    rrf_scores[idx] += 1.0 / (60 + rank + 1)
                for rank, idx in enumerate(bm25_rank_order):
                    rrf_scores[idx] += 1.0 / (60 + rank + 1)

                order = np.argsort(-rrf_scores)
            else:
                order = np.argsort(-dense_scores)

            ranked_cids = [chunks[idx]["chunk_id"] for idx in order]
            gold_ranks = [ranked_cids.index(cid) + 1 for cid in acceptable_cids if cid in ranked_cids]
            min_rank = min(gold_ranks) if gold_ranks else 999

            cand_results.append({
                "query_id": qid,
                "min_rank": min_rank,
                "r1": min_rank <= 1,
                "r3": min_rank <= 3,
                "r5": min_rank <= 5,
                "r10": min_rank <= 10,
                "r15": min_rank <= 15,
                "r20": min_rank <= 20
            })

        n = len(dev_queries)
        m = {
            "r1": f"{sum(1 for r in cand_results if r['r1'])}/{n} ({sum(1 for r in cand_results if r['r1'])/n*100:.2f}%)",
            "r3": f"{sum(1 for r in cand_results if r['r3'])}/{n} ({sum(1 for r in cand_results if r['r3'])/n*100:.2f}%)",
            "r5": f"{sum(1 for r in cand_results if r['r5'])}/{n} ({sum(1 for r in cand_results if r['r5'])/n*100:.2f}%)",
            "r10": f"{sum(1 for r in cand_results if r['r10'])}/{n} ({sum(1 for r in cand_results if r['r10'])/n*100:.2f}%)",
            "r15": f"{sum(1 for r in cand_results if r['r15'])}/{n} ({sum(1 for r in cand_results if r['r15'])/n*100:.2f}%)",
            "r20": f"{sum(1 for r in cand_results if r['r20'])}/{n} ({sum(1 for r in cand_results if r['r20'])/n*100:.2f}%)",
            "mrr": round(sum(1.0/r["min_rank"] for r in cand_results if r["min_rank"] <= len(chunks)) / n, 4)
        }
        candidate_diagnostics[config_name] = m
        print(f"\n[{config_name}]")
        print(f"  R@1:  {m['r1']}")
        print(f"  R@3:  {m['r3']}")
        print(f"  R@5:  {m['r5']}")
        print(f"  R@10: {m['r10']}")
        print(f"  R@15: {m['r15']}")
        print(f"  R@20: {m['r20']}")
        print(f"  MRR:  {m['mrr']}")

    with open(os.path.join(EVAL_OUT_DIR, "candidate_pool_diagnostics.json"), "w", encoding="utf-8") as f:
        json.dump(candidate_diagnostics, f, indent=2, ensure_ascii=False)

    # === STEP 2: CROSS-ENCODER RERANKING ON KEY STRATEGIES ===
    print("\n" + "="*80)
    print("STEP 2: CROSS-ENCODER RERANKING EVALUATION ON KEY STRATEGIES")
    print("="*80)

    rerank_strategies = [
        ("BASELINE_STANDARD_K5", "standard", False, 5),
        ("STRATEGY_EXPANDED_DEPTH_K10", "standard", False, 10),
        ("STRATEGY_EXPANDED_DEPTH_K15", "standard", False, 15),
        ("STRATEGY_CONTEXTUAL_K10", "contextual", False, 10),
        ("STRATEGY_HYBRID_BM25_K10", "standard", True, 10),
        ("STRATEGY_SYNERGISTIC_COMBO_K10", "contextual", True, 10),
        ("STRATEGY_SYNERGISTIC_COMBO_K15", "contextual", True, 15)
    ]

    strategy_candidate_orders = {}
    unique_pairs = set()

    for strat_name, mat_type, use_rrf, k_depth in rerank_strategies:
        sim_mat = sim_matrix_contextual if mat_type == "contextual" else sim_matrix_standard
        orders = []
        for i, q in enumerate(dev_queries):
            q_text = q["query_text"]
            dense_scores = sim_mat[i]
            if use_rrf:
                dense_rank_order = np.argsort(-dense_scores)
                bm25_scores = bm25.get_scores(q_text)
                bm25_rank_order = np.argsort(-bm25_scores)

                rrf_scores = np.zeros(len(chunks))
                for rank, idx in enumerate(dense_rank_order):
                    rrf_scores[idx] += 1.0 / (60 + rank + 1)
                for rank, idx in enumerate(bm25_rank_order):
                    rrf_scores[idx] += 1.0 / (60 + rank + 1)

                cand_order = np.argsort(-rrf_scores)[:k_depth]
            else:
                cand_order = np.argsort(-dense_scores)[:k_depth]

            orders.append(cand_order)
            for idx in cand_order:
                unique_pairs.add((q_text, chunks[idx]["text"]))
        strategy_candidate_orders[strat_name] = orders

    print(f"Total unique pairs to score for Cross-Encoder: {len(unique_pairs)}")

    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")
    unique_pairs_list = list(unique_pairs)
    t0_rerank = time.time()
    all_scores = reranker.predict(unique_pairs_list, batch_size=16, show_progress_bar=True)
    pair_score_map = {pair: score for pair, score in zip(unique_pairs_list, all_scores)}
    print(f"Reranker scoring completed in {time.time() - t0_rerank:.2f}s")

    all_strategy_results = {}

    for strat_name, mat_type, use_rrf, k_depth in rerank_strategies:
        strat_candidate_orders = strategy_candidate_orders[strat_name]
        strat_query_results = []

        for i, q in enumerate(dev_queries):
            qid = q["query_id"]
            q_text = q["query_text"]
            lang = q["language_category"]
            acceptable_cids = gold_labels[qid]["gold_chunk_ids"]

            top_k_indices = strat_candidate_orders[i]
            candidate_cids = [chunks[idx]["chunk_id"] for idx in top_k_indices]

            r_scores = [pair_score_map[(q_text, chunks[idx]["text"])] for idx in top_k_indices]
            r_order = np.argsort(-np.array(r_scores))
            r_top_k_cids = [candidate_cids[idx] for idx in r_order]

            cand_hits = [cid in acceptable_cids for cid in candidate_cids]
            r_hits = [cid in acceptable_cids for cid in r_top_k_cids]

            cand_r1 = cand_hits[0]
            cand_r3 = any(cand_hits[:3])
            cand_r5 = any(cand_hits[:5])

            r_r1 = r_hits[0]
            r_r3 = any(r_hits[:3])
            r_r5 = any(r_hits[:5])

            cand_rank = (cand_hits.index(True) + 1) if any(cand_hits) else 0
            r_rank = (r_hits.index(True) + 1) if any(r_hits) else 0

            was_baseline_r1 = baseline_top1[qid]
            if not was_baseline_r1 and r_r1:
                movement = "FAILURE_TO_SUCCESS"
            elif was_baseline_r1 and not r_r1:
                movement = "SUCCESS_TO_FAILURE"
            else:
                movement = "UNCHANGED"

            strat_query_results.append({
                "query_id": qid,
                "query_text": q_text,
                "language_category": lang,
                "acceptable_gold_chunks": acceptable_cids,
                "candidate_top_cids": candidate_cids,
                "rerank_top_cids": r_top_k_cids,
                "cand_r1": cand_r1,
                "cand_r3": cand_r3,
                "cand_r5": cand_r5,
                "cand_rank": cand_rank,
                "rerank_r1": r_r1,
                "rerank_r3": r_r3,
                "rerank_r5": r_r5,
                "rerank_rank": r_rank,
                "movement": movement
            })

        n = len(dev_queries)
        c_r1 = sum(1 for r in strat_query_results if r["cand_r1"]) / n
        c_r3 = sum(1 for r in strat_query_results if r["cand_r3"]) / n
        c_r5 = sum(1 for r in strat_query_results if r["cand_r5"]) / n
        c_mrr = sum(1.0 / r["cand_rank"] for r in strat_query_results if r["cand_rank"] > 0) / n

        r_r1 = sum(1 for r in strat_query_results if r["rerank_r1"]) / n
        r_r3 = sum(1 for r in strat_query_results if r["rerank_r3"]) / n
        r_r5 = sum(1 for r in strat_query_results if r["rerank_r5"]) / n
        r_mrr = sum(1.0 / r["rerank_rank"] for r in strat_query_results if r["rerank_rank"] > 0) / n

        failures_to_success = sum(1 for r in strat_query_results if r["movement"] == "FAILURE_TO_SUCCESS")
        success_to_failures = sum(1 for r in strat_query_results if r["movement"] == "SUCCESS_TO_FAILURE")
        unchanged = sum(1 for r in strat_query_results if r["movement"] == "UNCHANGED")

        # Linguistic breakdown
        lang_breakdown = {}
        for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
            l_subs = [r for r in strat_query_results if r["language_category"] == lang]
            ln = len(l_subs)
            lr_r1 = sum(1 for r in l_subs if r["rerank_r1"]) / ln
            lr_r3 = sum(1 for r in l_subs if r["rerank_r3"]) / ln
            lr_r5 = sum(1 for r in l_subs if r["rerank_r5"]) / ln
            lr_mrr = sum(1.0 / r["rerank_rank"] for r in l_subs if r["rerank_rank"] > 0) / ln
            lang_breakdown[lang] = {
                "n": ln,
                "r1_count": f"{sum(1 for r in l_subs if r['rerank_r1'])}/{ln}",
                "r1_pct": round(lr_r1 * 100, 2),
                "r3_count": f"{sum(1 for r in l_subs if r['rerank_r3'])}/{ln}",
                "r3_pct": round(lr_r3 * 100, 2),
                "r5_count": f"{sum(1 for r in l_subs if r['rerank_r5'])}/{ln}",
                "r5_pct": round(lr_r5 * 100, 2),
                "mrr": round(lr_mrr, 4)
            }

        strategy_summary = {
            "strategy_name": strat_name,
            "passage_representation": mat_type,
            "use_bm25_rrf": use_rrf,
            "candidate_depth_k": k_depth,
            "n_queries": n,
            "candidate_recall": {
                "r1_count": f"{sum(1 for r in strat_query_results if r['cand_r1'])}/{n}",
                "r1_pct": round(c_r1 * 100, 2),
                "r3_count": f"{sum(1 for r in strat_query_results if r['cand_r3'])}/{n}",
                "r3_pct": round(c_r3 * 100, 2),
                "r5_count": f"{sum(1 for r in strat_query_results if r['cand_r5'])}/{n}",
                "r5_pct": round(c_r5 * 100, 2),
                "mrr": round(c_mrr, 4)
            },
            "reranked_recall": {
                "r1_count": f"{sum(1 for r in strat_query_results if r['rerank_r1'])}/{n}",
                "r1_pct": round(r_r1 * 100, 2),
                "r3_count": f"{sum(1 for r in strat_query_results if r['rerank_r3'])}/{n}",
                "r3_pct": round(r_r3 * 100, 2),
                "r5_count": f"{sum(1 for r in strat_query_results if r['rerank_r5'])}/{n}",
                "r5_pct": round(r_r5 * 100, 2),
                "mrr": round(r_mrr, 4)
            },
            "failure_movement": {
                "failure_to_success": failures_to_success,
                "success_to_failure": success_to_failures,
                "unchanged": unchanged,
                "net_improvement": failures_to_success - success_to_failures
            },
            "language_breakdown": lang_breakdown,
            "query_results": strat_query_results
        }

        all_strategy_results[strat_name] = strategy_summary

        print(f"\n[{strat_name}] (Candidate Depth K={k_depth})")
        print(f"  Candidate Pool: R@1={round(c_r1*100,2)}%, R@3={round(c_r3*100,2)}%, R@5={round(c_r5*100,2)}%, MRR={round(c_mrr,4)}")
        print(f"  Post-Rerank:    R@1={round(r_r1*100,2)}% ({int(r_r1*n)}/40), R@3={round(r_r3*100,2)}% ({int(r_r3*n)}/40), R@5={round(r_r5*100,2)}% ({int(r_r5*n)}/40), MRR={round(r_mrr,4)}")
        print(f"  Movement:       Net=+{failures_to_success - success_to_failures} (F->S: {failures_to_success}, S->F: {success_to_failures})")

    out_file = os.path.join(EVAL_OUT_DIR, "all_strategies_dev_comparison.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_strategy_results, f, indent=2, ensure_ascii=False)

    print(f"\nSUCCESS! Saved all strategy results to {out_file}")

if __name__ == "__main__":
    main()
