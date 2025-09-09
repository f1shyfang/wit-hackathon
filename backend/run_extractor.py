#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from feature_extractor import extract_features


def main():
	if len(sys.argv) < 2:
		print("Usage: python run_extractor.py <video_path>")
		sys.exit(1)
	video_path = sys.argv[1]
	if not Path(video_path).exists():
		print(f"File not found: {video_path}")
		sys.exit(2)

	features = extract_features(video_path)
	print("=== JSON ===")
	print(json.dumps(features.to_dict(), indent=2))
	print("\n=== VECTOR ===")
	print(json.dumps(features.to_feature_vector()))


if __name__ == "__main__":
	main()
