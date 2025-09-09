import os
from typing import Tuple

import numpy as np  # type: ignore
import joblib  # type: ignore

MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(os.path.dirname(__file__), "model.pkl"))


def load_model(model_path: str = MODEL_PATH):
	if not os.path.exists(model_path):
		raise FileNotFoundError(f"Model file not found: {model_path}")
	return joblib.load(model_path)


def predict_proba(feature_vector: np.ndarray, model=None) -> Tuple[float, float]:
	"""
	Return (prob_real, prob_fake). Assumes binary classifier with classes [0,1] where 1=fake.
	"""
	if model is None:
		model = load_model()
	fv = np.asarray(feature_vector, dtype=float).reshape(1, -1)
	probs = getattr(model, "predict_proba")(fv)
	prob_fake = float(probs[0][1])
	prob_real = float(probs[0][0])
	return prob_real, prob_fake
