#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

import numpy as np  # type: ignore

from feature_extractor import extract_features
from predictor import predict_proba, load_model


def main():
	if len(sys.argv) < 2:
		print("Usage: python run_predict.py <video_path> [model_path]")
		sys.exit(1)
	video_path = sys.argv[1]
	model_path = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("MODEL_PATH")
	if not Path(video_path).exists():
		print(f"File not found: {video_path}")
		sys.exit(2)

	features = extract_features(video_path)
	vector = np.array(features.to_feature_vector(), dtype=float)

	model = load_model(model_path) if model_path else load_model()
	prob_real, prob_fake = predict_proba(vector, model=model)
	score_authentic = float(prob_real * 100.0)

	result = {
		"authenticity_score": score_authentic,
		"probabilities": {
			"real": prob_real,
			"fake": prob_fake,
		},
		"features": features.to_dict(),
	}
	print(json.dumps(result, indent=2))


if __name__ == "__main__":
	main()
