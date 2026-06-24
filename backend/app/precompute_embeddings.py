from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.repository import CandidateRepository
from app.services.semantic import candidate_embedding_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Precompute offline candidate MiniLM embeddings.")
    parser.add_argument("--scope", choices=("sample", "full"), default="full")
    parser.add_argument("--model", default=settings.semantic_model)
    parser.add_argument("--output-dir", default=str(settings.semantic_artifact_dir))
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-candidates", type=int)
    parser.add_argument("--max-seq-length", type=int, default=128)
    parser.add_argument("--allow-download", action="store_true")
    args = parser.parse_args()

    repository = CandidateRepository(settings.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    expected = args.max_candidates or (50 if args.scope == "sample" else 100_000)
    model = SentenceTransformer(
        args.model, local_files_only=not args.allow_download, device="cpu"
    )
    model.max_seq_length = args.max_seq_length
    dimension = model.get_sentence_embedding_dimension()
    embeddings_tmp = output_dir / "candidate_embeddings.tmp.npy"
    ids_tmp = output_dir / "candidate_ids.tmp.txt"
    embeddings = np.lib.format.open_memmap(
        embeddings_tmp, mode="w+", dtype="float16", shape=(expected, dimension)
    )

    started = time.perf_counter()
    count = 0
    batch_candidates = []
    batch_texts = []
    with ids_tmp.open("w", encoding="utf-8", newline="\n") as ids_handle:
        for candidate in repository.iter_candidates(args.scope, args.max_candidates):
            batch_candidates.append(candidate)
            batch_texts.append(candidate_embedding_text(candidate))
            if len(batch_texts) < args.batch_size:
                continue
            vectors = model.encode(
                batch_texts, batch_size=args.batch_size, normalize_embeddings=True,
                convert_to_numpy=True, show_progress_bar=False,
            ).astype("float16")
            embeddings[count:count + len(vectors)] = vectors
            for item in batch_candidates:
                ids_handle.write(f"{item['candidate_id']}\n")
            count += len(vectors)
            if count % 1_000 == 0:
                elapsed = time.perf_counter() - started
                print(f"Embedded {count:,}/{expected:,} candidates ({count / max(elapsed, 0.001):.1f}/s)", flush=True)
            batch_candidates.clear()
            batch_texts.clear()

        if batch_texts:
            vectors = model.encode(
                batch_texts, batch_size=args.batch_size, normalize_embeddings=True,
                convert_to_numpy=True, show_progress_bar=False,
            ).astype("float16")
            embeddings[count:count + len(vectors)] = vectors
            for item in batch_candidates:
                ids_handle.write(f"{item['candidate_id']}\n")
            count += len(vectors)

    embeddings.flush()
    if count != expected:
        del embeddings
        embeddings = np.load(embeddings_tmp, mmap_mode="r")[:count].copy()
        with (output_dir / "candidate_embeddings.resized.npy").open("wb") as handle:
            np.save(handle, embeddings.astype("float16"))
        embeddings_tmp.unlink(missing_ok=True)
        os.replace(output_dir / "candidate_embeddings.resized.npy", output_dir / "candidate_embeddings.npy")
    else:
        del embeddings
        os.replace(embeddings_tmp, output_dir / "candidate_embeddings.npy")
    os.replace(ids_tmp, output_dir / "candidate_ids.txt")
    elapsed = time.perf_counter() - started
    metadata = {
        "model": args.model,
        "candidate_count": count,
        "dimension": dimension,
        "dtype": "float16",
        "normalized": True,
        "max_seq_length": args.max_seq_length,
        "scope": args.scope,
        "precompute_seconds": round(elapsed, 3),
        "ranking_network_required": False,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote {count:,} embeddings ({dimension}d) to {output_dir} in {elapsed:.1f}s.")


if __name__ == "__main__":
    main()
