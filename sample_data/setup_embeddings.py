"""Download the pinned embedding weights once. Run from the project root."""
from huggingface_hub import snapshot_download

from config import EMBEDDING_DIR, EMBEDDING_MODEL, EMBEDDING_REVISION


if __name__ == "__main__":
    snapshot_download(
        EMBEDDING_MODEL,
        revision=EMBEDDING_REVISION,
        local_dir=EMBEDDING_DIR,
        allow_patterns=[
            "config.json", "config_sentence_transformers.json", "modules.json",
            "model.safetensors", "1_Pooling/config.json", "sentence_bert_config.json",
            "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json",
            "vocab.txt",
        ],
    )
    print(f"Cached {EMBEDDING_MODEL} at {EMBEDDING_DIR} for offline use.")
