#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np  # type: ignore
import joblib  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore
from sklearn.metrics import classification_report, roc_auc_score  # type: ignore
from sklearn.ensemble import RandomForestClassifier  # type: ignore

from feature_extractor import extract_features


def list_videos(directory: str) -> List[str]:
	paths: List[str] = []
	for root, _, files in os.walk(directory):
		for f in files:
			if f.lower().endswith(('.mp4', '.mov', '.mkv', '.avi', '.webm')):
				paths.append(os.path.join(root, f))
	# Deterministic ordering so "top N" is stable
	paths.sort()
	return paths


def build_dataset(
	real_dir: str,
	fake_dir: str,
	max_per_class: Optional[int] = None,
	frame_stride: int = 5,
	ear_blink_threshold: float = 0.21,
) -> Tuple[np.ndarray, np.ndarray]:
	real_paths = list_videos(real_dir)
	fake_paths = list_videos(fake_dir)
	if max_per_class is not None:
		real_paths = real_paths[:max_per_class]
		fake_paths = fake_paths[:max_per_class]
	X: List[List[float]] = []
	y: List[int] = []
	skipped_real_zero_blink = 0

	for p in real_paths:
		features = extract_features(p, frame_stride=frame_stride, ear_blink_threshold=ear_blink_threshold)
		# Skip real samples with zero blink rate to avoid false negatives from failure to detect blinks
		blink_rate = (features.video.avg_blink_rate_per_minute if features.video else 0.0) or 0.0
		if blink_rate == 0.0:
			skipped_real_zero_blink += 1
			continue
		X.append(features.to_feature_vector())
		y.append(0)

	for p in fake_paths:
		features = extract_features(p, frame_stride=frame_stride, ear_blink_threshold=ear_blink_threshold)
		X.append(features.to_feature_vector())
		y.append(1)

	if skipped_real_zero_blink:
		print(f"Skipped {skipped_real_zero_blink} real samples with zero blink rate")
	return np.asarray(X, dtype=float), np.asarray(y, dtype=int)


def main():
	import argparse
	parser = argparse.ArgumentParser(description="Train deepfake classifier from real/fake folders")
	parser.add_argument("real_dir", help="Directory of real videos")
	parser.add_argument("fake_dir", help="Directory of fake videos")
	parser.add_argument("--out", dest="out_path", default=os.path.join(os.path.dirname(__file__), 'model.pkl'))
	parser.add_argument("--max-per-class", type=int, default=None, help="Limit number of videos per class")
	parser.add_argument("--frame-stride", type=int, default=5, help="Analyze every Nth frame for speed")
	parser.add_argument("--blink-threshold", type=float, default=0.21, help="EAR threshold for blink detection")
	args = parser.parse_args()

	real_dir = args.real_dir
	fake_dir = args.fake_dir
	out_path = args.out_path

	if not Path(real_dir).exists() or not Path(fake_dir).exists():
		print("Provided directories do not exist")
		sys.exit(2)

	print("Extracting features...")
	X, y = build_dataset(
		real_dir,
		fake_dir,
		max_per_class=args.max_per_class,
		frame_stride=args.frame_stride,
		ear_blink_threshold=args.blink_threshold,
	)
	print(f"Dataset: X={X.shape}, y={y.shape}, positives={int(y.sum())}")

	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

	model = RandomForestClassifier(n_estimators=300, max_depth=None, random_state=42, n_jobs=-1)
	model.fit(X_train, y_train)

	probs = model.predict_proba(X_test)[:, 1]
	preds = (probs >= 0.5).astype(int)
	print(classification_report(y_test, preds, digits=4))
	try:
		auc = roc_auc_score(y_test, probs)
		print(f"ROC AUC: {auc:.4f}")
	except Exception:
		pass

	joblib.dump(model, out_path)
	print(f"Saved model to {out_path}")


if __name__ == '__main__':
	main()


