import os
import warnings

# pyrefly: ignore [missing-import]
from huggingface_hub import hf_hub_download

warnings.filterwarnings("ignore")

CATEGORY = "Video_Games"
HF_REPO = "McAuley-Lab/Amazon-Reviews-2023"
LOCAL_DIR = os.path.dirname(__file__)

review_path = hf_hub_download(
    repo_id=HF_REPO,
    filename=f"raw/review_categories/{CATEGORY}.jsonl",
    repo_type="dataset",
    local_dir=LOCAL_DIR,
)

meta_path = hf_hub_download(
    repo_id=HF_REPO,
    filename=f"raw/meta_categories/meta_{CATEGORY}.jsonl",
    repo_type="dataset",
    local_dir=LOCAL_DIR,
)

print(f"reviews  → {review_path}")
print(f"metadata → {meta_path}")