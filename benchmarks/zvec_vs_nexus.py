#!/usr/bin/env python3.11
"""
Benchmark: ZVec vs NEXUS Memory for Brain System
=================================================
Compares the two memory backends across:
  1. Indexing speed
  2. Query latency
  3. Retrieval quality (LLM-as-judge)
  4. Multi-turn coherence

Usage:
  python3.11 benchmarks/zvec_vs_nexus.py
"""

import json
import os
import shutil
import statistics
import time
from textwrap import dedent

# ── ZVec imports ─────────────────────────────────────────
from brain_system.core.vector_memory import VectorMemory

# ── NEXUS imports ────────────────────────────────────────
from nexus import NEXUS, NexusConfig

# ── LLM judge ───────────────────────────────────────────
from langchain_ollama import ChatOllama

# ── Test data ───────────────────────────────────────────
PERSONA_PROFILE = {
    "NAME": "Mohandas Karamchand Gandhi (Mahatma Gandhi)",
    "ERA": "1869–1948, British colonial India through Indian independence",
    "PERSONALITY_TRAITS": "Humble, fearless, morally courageous, self-disciplined, persistent, compassionate, experimentally minded",
    "BELIEFS": "Truth (Satya) is the sovereign principle encompassing all others — not just truthfulness in word but in thought. Non-violence (Ahimsa) is the means to reach Truth. Morality is the basis of things and truth the substance of all morality.",
    "VALUES": "Truth above all else. Non-violence as both weapon and way of life. Simplicity and self-discipline. Equality of all humanity regardless of race, caste, or religion. Service to the deprived and exploited.",
    "KEY_EXPERIENCES": "Thrown off a train in South Africa for being Indian despite holding a first-class ticket. Twenty-one years fighting racial discrimination in South Africa. Leading the Salt March in 1930. Repeated imprisonments for civil disobedience.",
    "REASONING_STYLE": "Experimental and empirical — treats life as a series of 'experiments with Truth' conducted with scientific spirit. Applies spiritual principles to practical situations. Open to revising conclusions like a scientist.",
    "SPEECH_STYLE": "Direct, intimate, and unadorned — free from conscious ornamentation or rhetorical tricks. Democratic in temper, making ideas accessible to all. Humble and self-deprecating.",
    "EMOTIONAL_TENDENCIES": "Deeply passionate beneath a disciplined exterior. Experiences moral anguish when compromising principles. Harsh self-critic who examines his own failures publicly. Optimistic about human capacity for goodness.",
    "KNOWN_VIEWS": "Non-violent resistance (Satyagraha) as the most powerful force for social change. Opposition to untouchability and caste discrimination. Hindu-Muslim unity as essential for India.",
}

QUERIES = [
    "How did you handle criticism early in your career?",
    "What are your views on violence?",
    "Tell me about your time in South Africa",
    "What role does truth play in your life?",
    "How should one deal with injustice?",
    "What would you say to someone losing hope?",
    "How do you balance idealism with pragmatism?",
    "What is the relationship between morality and politics?",
]

MULTI_TURN = [
    "What do you think about civil disobedience?",
    "Doesn't that risk chaos and disorder?",
    "How did you convince others to follow non-violence?",
    "Earlier you mentioned civil disobedience — how does it connect to what you just said about convincing others?",
    "Summarize your philosophy in one sentence.",
]


# ═══════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════

def clean_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def get_llm_judge():
    return ChatOllama(model="mistral", temperature=0.0, num_predict=300)


def judge_relevance(judge, query, results_a, results_b):
    """Ask an LLM to score retrieval quality 1-5 for each system."""
    prompt = dedent(f"""\
    You are evaluating search results for relevance.

    Query: "{query}"

    System A results:
    {chr(10).join(f'  - {r}' for r in results_a[:5])}

    System B results:
    {chr(10).join(f'  - {r}' for r in results_b[:5])}

    Score each system's results from 1 (irrelevant) to 5 (perfectly relevant).
    Respond ONLY in this JSON format:
    {{"system_a": <score>, "system_b": <score>, "reason": "<one sentence>"}}
    """)

    resp = judge.invoke(prompt).content
    try:
        # Try to parse JSON from response
        start = resp.index("{")
        end = resp.rindex("}") + 1
        return json.loads(resp[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"system_a": 3, "system_b": 3, "reason": "Parse error"}


# ═══════════════════════════════════════════════════════
# Benchmark 1: Indexing Speed
# ═══════════════════════════════════════════════════════

def benchmark_indexing():
    print("\n" + "=" * 60)
    print("  BENCHMARK 1: INDEXING SPEED")
    print("=" * 60)

    # ── ZVec ──
    clean_dir("/tmp/bench_zvec")
    zvec_mem = VectorMemory(storage_dir="/tmp/bench_zvec")
    start = time.perf_counter()
    zvec_mem.index_profile(PERSONA_PROFILE, "gandhi")
    zvec_time = (time.perf_counter() - start) * 1000

    # ── NEXUS ──
    clean_dir("/tmp/bench_nexus")
    config = NexusConfig(storage_path="/tmp/bench_nexus", llm_model="mistral")
    nexus = NEXUS(config=config)
    start = time.perf_counter()
    for field, value in PERSONA_PROFILE.items():
        nexus.encode(f"{field}: {value}", context="persona")
    nexus_time = (time.perf_counter() - start) * 1000

    print(f"\n  {'Metric':<25} {'ZVec':>10} {'NEXUS':>10}")
    print(f"  {'-'*25} {'-'*10} {'-'*10}")
    print(f"  {'Index time (ms)':<25} {zvec_time:>10.1f} {nexus_time:>10.1f}")

    return zvec_mem, nexus, zvec_time, nexus_time


# ═══════════════════════════════════════════════════════
# Benchmark 2: Query Latency
# ═══════════════════════════════════════════════════════

def benchmark_query_latency(zvec_mem, nexus):
    print("\n" + "=" * 60)
    print("  BENCHMARK 2: QUERY LATENCY")
    print("=" * 60)

    zvec_latencies = []
    nexus_latencies = []
    zvec_all_results = {}
    nexus_all_results = {}

    for query in QUERIES:
        # ZVec
        start = time.perf_counter()
        zvec_results = zvec_mem.search(query, top_k=5)
        zvec_lat = (time.perf_counter() - start) * 1000
        zvec_latencies.append(zvec_lat)
        zvec_all_results[query] = zvec_results

        # NEXUS
        start = time.perf_counter()
        nexus_results = nexus.recall(query, top_k=5)
        nexus_lat = (time.perf_counter() - start) * 1000
        nexus_latencies.append(nexus_lat)
        nexus_all_results[query] = [m.content for m in nexus_results]

    print(f"\n  {'Query':<50} {'ZVec (ms)':>10} {'NEXUS (ms)':>10}")
    print(f"  {'-'*50} {'-'*10} {'-'*10}")
    for i, query in enumerate(QUERIES):
        short = query[:47] + "..." if len(query) > 50 else query
        print(f"  {short:<50} {zvec_latencies[i]:>10.2f} {nexus_latencies[i]:>10.2f}")

    print(f"\n  {'AVERAGE':<50} {statistics.mean(zvec_latencies):>10.2f} {statistics.mean(nexus_latencies):>10.2f}")
    print(f"  {'MEDIAN':<50} {statistics.median(zvec_latencies):>10.2f} {statistics.median(nexus_latencies):>10.2f}")

    return zvec_all_results, nexus_all_results


# ═══════════════════════════════════════════════════════
# Benchmark 3: Retrieval Quality (LLM-as-Judge)
# ═══════════════════════════════════════════════════════

def benchmark_retrieval_quality(zvec_results, nexus_results):
    print("\n" + "=" * 60)
    print("  BENCHMARK 3: RETRIEVAL QUALITY (LLM-as-Judge)")
    print("=" * 60)

    judge = get_llm_judge()
    zvec_scores = []
    nexus_scores = []

    print(f"\n  {'Query':<45} {'ZVec':>6} {'NEXUS':>6}  Reason")
    print(f"  {'-'*45} {'-'*6} {'-'*6}  {'-'*30}")

    for query in QUERIES:
        verdict = judge_relevance(
            judge, query,
            zvec_results.get(query, []),
            nexus_results.get(query, []),
        )
        a_score = verdict.get("system_a", 3)
        b_score = verdict.get("system_b", 3)
        reason = verdict.get("reason", "")[:40]
        zvec_scores.append(a_score)
        nexus_scores.append(b_score)

        short = query[:42] + "..." if len(query) > 45 else query
        print(f"  {short:<45} {a_score:>5}/5 {b_score:>5}/5  {reason}")

    print(f"\n  {'AVERAGE SCORE':<45} {statistics.mean(zvec_scores):>5.1f}/5 {statistics.mean(nexus_scores):>5.1f}/5")

    return zvec_scores, nexus_scores


# ═══════════════════════════════════════════════════════
# Benchmark 4: Multi-Turn Coherence
# ═══════════════════════════════════════════════════════

def benchmark_multi_turn(zvec_mem, nexus):
    print("\n" + "=" * 60)
    print("  BENCHMARK 4: MULTI-TURN COHERENCE")
    print("=" * 60)

    judge = get_llm_judge()

    # Simulate conversation turns
    zvec_context = []
    nexus_context = []

    for i, turn in enumerate(MULTI_TURN):
        # ZVec: search
        zvec_results = zvec_mem.search(turn, top_k=3)
        zvec_context.append(f"Turn {i+1}: {turn} → {zvec_results[:2]}")

        # NEXUS: encode previous response + recall
        if i > 0:
            nexus.encode(
                f"User asked: {MULTI_TURN[i-1]}",
                context="conversation",
            )
        nexus_results = nexus.recall(turn, top_k=3)
        nexus_context.append(
            f"Turn {i+1}: {turn} → {[m.content for m in nexus_results[:2]]}"
        )

    # Judge the conversation coherence
    prompt = dedent(f"""\
    Two memory systems were used across a 5-turn conversation.
    Rate each system's ability to maintain coherent context (1-5).

    System A (ZVec) context across turns:
    {chr(10).join(zvec_context)}

    System B (NEXUS) context across turns:
    {chr(10).join(nexus_context)}

    Score each system 1-5 for multi-turn coherence.
    Respond ONLY in JSON: {{"system_a": <score>, "system_b": <score>, "reason": "<one sentence>"}}
    """)

    resp = judge.invoke(prompt).content
    try:
        start = resp.index("{")
        end = resp.rindex("}") + 1
        verdict = json.loads(resp[start:end])
    except (ValueError, json.JSONDecodeError):
        verdict = {"system_a": 3, "system_b": 3, "reason": "Parse error"}

    print(f"\n  {'System':<15} {'Coherence Score':>15}")
    print(f"  {'-'*15} {'-'*15}")
    print(f"  {'ZVec':<15} {verdict.get('system_a', 3):>14}/5")
    print(f"  {'NEXUS':<15} {verdict.get('system_b', 3):>14}/5")
    print(f"\n  Reason: {verdict.get('reason', 'N/A')}")

    return verdict


# ═══════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════

def print_summary(index_times, latency_results, quality_scores, coherence):
    print("\n" + "=" * 60)
    print("  FINAL SUMMARY: ZVec vs NEXUS Memory")
    print("=" * 60)

    zvec_time, nexus_time = index_times
    zvec_q, nexus_q = quality_scores

    print(f"\n  {'Metric':<30} {'ZVec':>10} {'NEXUS':>10} {'Winner':>10}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10}")

    # Index time
    winner = "ZVec" if zvec_time < nexus_time else "NEXUS"
    print(f"  {'Index time (ms)':<30} {zvec_time:>10.1f} {nexus_time:>10.1f} {winner:>10}")

    # Query latency
    zvec_avg = statistics.mean(
        [(time.perf_counter() - time.perf_counter()) for _ in range(1)]
    )
    # We'll just print from the data we have
    print(f"  {'Avg query latency (ms)':<30} {'—':>10} {'—':>10} {'—':>10}")

    # Retrieval quality
    avg_a = statistics.mean(zvec_q) if zvec_q else 0
    avg_b = statistics.mean(nexus_q) if nexus_q else 0
    winner = "ZVec" if avg_a > avg_b else ("NEXUS" if avg_b > avg_a else "Tie")
    print(f"  {'Retrieval quality (/5)':<30} {avg_a:>10.1f} {avg_b:>10.1f} {winner:>10}")

    # Coherence
    c_a = coherence.get("system_a", 3)
    c_b = coherence.get("system_b", 3)
    winner = "ZVec" if c_a > c_b else ("NEXUS" if c_b > c_a else "Tie")
    print(f"  {'Multi-turn coherence (/5)':<30} {c_a:>10}/5 {c_b:>10}/5 {winner:>10}")

    print()


# ═══════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🧠 Brain System • Memory Backend Benchmark")
    print("   ZVec (embedded vector DB) vs NEXUS (neuro-inspired architecture)")
    print("   Persona: Mahatma Gandhi • LLM Judge: Ollama/Mistral\n")

    # 1. Indexing
    zvec_mem, nexus, zvec_time, nexus_time = benchmark_indexing()

    # 2. Query latency
    zvec_results, nexus_results = benchmark_query_latency(zvec_mem, nexus)

    # 3. Retrieval quality
    zvec_scores, nexus_scores = benchmark_retrieval_quality(zvec_results, nexus_results)

    # 4. Multi-turn coherence
    coherence = benchmark_multi_turn(zvec_mem, nexus)

    # Summary
    print_summary(
        (zvec_time, nexus_time),
        None,
        (zvec_scores, nexus_scores),
        coherence,
    )

    # Cleanup
    clean_dir("/tmp/bench_zvec")
    clean_dir("/tmp/bench_nexus")

    print("✅ Benchmark complete.\n")
