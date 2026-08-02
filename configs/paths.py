"""
Project Paths

Centralized file and directory paths for the project.

Project:
AI-Powered Business Risk Analysis
and Recommendation System
"""

from pathlib import Path

# ==================================================
# Project Root
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ==================================================
# Data Directories
# ==================================================

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FINAL_DATA_DIR = DATA_DIR / "final"

# ==================================================
# Dataset Files
# ==================================================

RAW_DATASET_PATH = RAW_DATA_DIR / "dataset.jsonl"
PROCESSED_DATASET_PATH = PROCESSED_DATA_DIR / "dataset.jsonl"
FINAL_DATASET_PATH = FINAL_DATA_DIR / "dataset.jsonl"
TRAIN_DATASET_PATH = PROCESSED_DATA_DIR / "train.jsonl"
VALIDATION_DATASET_PATH = PROCESSED_DATA_DIR / "validation.jsonl"
TEST_DATASET_PATH = PROCESSED_DATA_DIR / "test.jsonl"

# ==================================================
# Checkpoints
# ==================================================

CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"

# ==================================================
# Outputs
# ==================================================

OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOG_DIR = OUTPUT_DIR / "logs"
REPORT_DIR = OUTPUT_DIR / "reports"
FIGURE_DIR = OUTPUT_DIR / "figures"

# ==================================================
# AI Model & Resources
# ==================================================

MODEL_DIR = PROJECT_ROOT / "models" / "v1"
TOKENIZER_DIR = MODEL_DIR / "tokenizer"
RESOURCES_DIR = PROJECT_ROOT / "resources"

# ==================================================
# Recommendation Subsystem Paths
# ==================================================

RECOMMENDATION_DIR = PROJECT_ROOT / "core" / "recommendation"
RECOMMENDATION_RULES_DIR = RECOMMENDATION_DIR / "knowledge" / "rules"
RECOMMENDATION_TEMPLATES_DIR = RECOMMENDATION_DIR / "templates"