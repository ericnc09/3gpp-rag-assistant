"""Build a clause-chunked index into its own ChromaDB collection (ADR-014).

The default ``3gpp_specs`` collection (fixed 1000-char chunks) is left
untouched, so the two can be compared with
``scripts/eval_retrieval.py --collection <name>``.

Usage:
    python scripts/build_index_clauses.py                       # 3gpp_clauses, with headers
    python scripts/build_index_clauses.py --no-context --collection 3gpp_clauses_plain
    COLLECTION_NAME=3gpp_clauses uvicorn src.api.main:app       # serve it
"""
import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.build_index_cpu import RAW_DIR, find_spec_files  # noqa: E402
from src.core.clause_chunker import chunk_docx  # noqa: E402
from src.core.embeddings import LocalEmbeddingGenerator  # noqa: E402
from src.core.spec_catalog import infer_spec_from_filename  # noqa: E402
from src.core.vector_store import VectorStore  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")


def catalog_metadata(path: Path) -> dict:
    entry = infer_spec_from_filename(path.name)
    if not entry:
        return {"domain": "unknown", "generation": "unknown",
                "spec_number": "unknown", "spec_title": "unknown"}
    return {"domain": entry["domain"], "generation": entry["generation"],
            "spec_number": entry["spec_number"], "spec_title": entry["title"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--collection", default="3gpp_clauses")
    parser.add_argument("--context", action=argparse.BooleanOptionalAction, default=True,
                        help="Prepend the spec/clause header to each chunk (default on)")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=None, help="Only the first N files")
    args = parser.parse_args()

    files = [f for f in find_spec_files(RAW_DIR) if f.suffix.lower() == ".docx"]
    skipped = [f for f in find_spec_files(RAW_DIR) if f.suffix.lower() != ".docx"]
    if args.limit:
        files = files[: args.limit]
    if skipped:
        print(f"Skipping {len(skipped)} non-DOCX files (no heading styles): "
              f"{', '.join(f.name for f in skipped)}")

    store = VectorStore(collection_name=args.collection)
    store.clear()
    generator = LocalEmbeddingGenerator(model_name="bge-small", device="cpu", batch_size=64)
    print(f"Building '{args.collection}' from {len(files)} specs "
          f"(context headers: {'on' if args.context else 'off'})", flush=True)

    start = time.time()
    total = 0
    for i, path in enumerate(files, 1):
        meta = catalog_metadata(path)
        chunks = chunk_docx(path, meta, chunk_size=args.chunk_size, contextual=args.context)
        for b in range(0, len(chunks), 500):
            store.add_chunks(generator.embed_chunks(chunks[b:b + 500]))
        total += len(chunks)
        sections = len({c["metadata"]["section_id"] for c in chunks})
        rate = total / max(time.time() - start, 1e-6)
        print(f"[{i}/{len(files)}] TS {meta['spec_number']}: {len(chunks)} chunks, "
              f"{sections} clauses | total {total} | {rate:.1f} chunks/s", flush=True)

    print(f"Done: {total} chunks in '{args.collection}' "
          f"({store.get_stats()['total_chunks']} stored) in {(time.time() - start) / 60:.1f} min")


if __name__ == "__main__":
    main()
