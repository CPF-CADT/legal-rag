"""Export readable BM25 vocabulary lists for the dictionary experiment."""
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("compare_bm25_dictionary.py")
spec = importlib.util.spec_from_file_location("bm25_experiment", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def main() -> None:
    chunks = module.load_chunks()
    dictionary_terms = module.load_terms()
    variants = {
        "without_dictionary": None,
        "with_dictionary": dictionary_terms,
    }
    vocabularies: dict[str, set[str]] = {}
    for name, terms in variants.items():
        vocabulary = set()
        for chunk in chunks:
            vocabulary.update(module.tokenize_variant(module.chunk_text(chunk), terms))
        vocabularies[name] = vocabulary
        output = module.OUTPUT_DIR / f"terms_{name}.txt"
        output.write_text("\n".join(sorted(vocabulary)) + "\n", encoding="utf-8")
        print(f"{name}: {len(vocabulary)} terms -> {output}")

    added = sorted(vocabularies["with_dictionary"] - vocabularies["without_dictionary"])
    removed = sorted(vocabularies["without_dictionary"] - vocabularies["with_dictionary"])
    (module.OUTPUT_DIR / "terms_added_by_dictionary.txt").write_text("\n".join(added) + "\n", encoding="utf-8")
    (module.OUTPUT_DIR / "terms_removed_by_dictionary.txt").write_text("\n".join(removed) + "\n", encoding="utf-8")
    print(f"added: {len(added)} terms")
    print(f"removed: {len(removed)} terms")


if __name__ == "__main__":
    main()
