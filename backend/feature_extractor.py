import os
import math
import tempfile
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from collections import deque

# Video
try:
	import cv2  # type: ignore
except Exception as _:
	cv2 = None  # type: ignore

# Facial landmarks
try:
	import mediapipe as mp  # type: ignore
except Exception as _:
	mp = None  # type: ignore

# Audio
try:
	import numpy as np  # type: ignore
	import librosa  # type: ignore
except Exception as _:
	np = None  # type: ignore
	librosa = None  # type: ignore

try:
	import ffmpeg  # type: ignore
except Exception as _:
	ffmpeg = None  # type: ignore


@dataclass
class VideoFeatureStats:
	avg_blink_rate_per_minute: float
	facial_jitter_std_dev: float
	frames_analyzed: int


@dataclass
class AudioFeatureStats:
	audio_mfcc_mean: float
	audio_mfcc_std: float
	sample_rate: int
	duration_seconds: float


@dataclass
class MetadataStats:
	container_format: Optional[str]
	file_size_bytes: Optional[int]
	duration_seconds: Optional[float]
	bit_rate: Optional[int]
	has_video: bool
	has_audio: bool
	video_codec: Optional[str]
	video_width: Optional[int]
	video_height: Optional[int]
	video_avg_fps: Optional[float]
	audio_codec: Optional[str]
	audio_sample_rate: Optional[int]
	audio_channels: Optional[int]


@dataclass
class ExtractedFeatures:
	video: Optional[VideoFeatureStats]
	audio: Optional[AudioFeatureStats]
	metadata: Optional[MetadataStats]

	def to_dict(self) -> Dict:
		return {
			"video": asdict(self.video) if self.video else None,
			"audio": asdict(self.audio) if self.audio else None,
			"metadata": asdict(self.metadata) if self.metadata else None,
		}

	def to_feature_vector(self) -> List[float]:
		"""
		Return a stable, fixed-length numeric vector.
		Order:
		0: video.avg_blink_rate_per_minute (0 if None)
		1: video.facial_jitter_std_dev (0 if None)
		2: audio.audio_mfcc_mean (0 if None)
		3: audio.audio_mfcc_std (0 if None)
		4: metadata.duration_seconds (0 if None)
		5: metadata.bit_rate (0 if None)
		6: metadata.video_avg_fps (0 if None)
		7: metadata.video_width (0 if None)
		8: metadata.video_height (0 if None)
		9: metadata.audio_sample_rate (0 if None)
		"""
		def g(x: Optional[float]) -> float:
			return float(x) if x is not None else 0.0

		return [
			g(self.video.avg_blink_rate_per_minute) if self.video else 0.0,
			g(self.video.facial_jitter_std_dev) if self.video else 0.0,
			g(self.audio.audio_mfcc_mean) if self.audio else 0.0,
			g(self.audio.audio_mfcc_std) if self.audio else 0.0,
			g(self.metadata.duration_seconds) if self.metadata else 0.0,
			float(self.metadata.bit_rate) if (self.metadata and self.metadata.bit_rate is not None) else 0.0,
			g(self.metadata.video_avg_fps) if self.metadata else 0.0,
			float(self.metadata.video_width) if (self.metadata and self.metadata.video_width is not None) else 0.0,
			float(self.metadata.video_height) if (self.metadata and self.metadata.video_height is not None) else 0.0,
			float(self.metadata.audio_sample_rate) if (self.metadata and self.metadata.audio_sample_rate is not None) else 0.0,
		]


# -----------------------------
# Utility math helpers
# -----------------------------

def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
	return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def eye_aspect_ratio(eye_points: List[Tuple[float, float]]) -> float:
	"""
	Compute Eye Aspect Ratio (EAR) from 6 eye landmark points.
	Expected order: [p1, p2, p3, p4, p5, p6]
	p1-p4 is horizontal, (p2,p6) and (p3,p5) are vertical pairs.
	"""
	p1, p2, p3, p4, p5, p6 = eye_points
	vertical = euclidean_distance(p2, p6) + euclidean_distance(p3, p5)
	horizontal = euclidean_distance(p1, p4)
	if horizontal == 0:
		return 0.0
	return vertical / (2.0 * horizontal)


# -----------------------------
# Video feature extraction
# -----------------------------

def extract_video_features(video_path: str, frame_stride: int = 5, ear_blink_threshold: float = 0.21) -> Optional[VideoFeatureStats]:
	if cv2 is None or mp is None:
		return None

	cap = cv2.VideoCapture(video_path)
	if not cap.isOpened():
		return None

	fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
	total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

	mp_face_mesh = mp.solutions.face_mesh
	face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)

	# Indices for eyes and a stable reference point (nose tip)
	# MediaPipe Face Mesh canonical landmarks
	LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]  # p1, p2, p3, p4, p5, p6
	RIGHT_EYE_IDX = [263, 387, 385, 362, 380, 373]
	NOSE_TIP_IDX = 1

	prev_nose: Optional[Tuple[float, float]] = None
	jitter_distances: List[float] = []
	blinks = 0
	frames_analyzed = 0

	# Blink detection improvements: smoothed EAR, adaptive threshold, refractory period
	ear_window = deque(maxlen=15)  # ~0.5s at 30fps; scales with stride implicitly
	prev_ear_above = True
	frames_since_last_blink = 9999
	min_frames_between_blinks = max(2, int((fps / frame_stride) * 0.15))  # ~150ms refractory

	frame_index = 0
	while True:
		ret, frame = cap.read()
		if not ret:
			break

		if frame_index % frame_stride != 0:
			frame_index += 1
			continue

		h, w = frame.shape[:2]
		rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		res = face_mesh.process(rgb)

		if res.multi_face_landmarks:
			landmarks = res.multi_face_landmarks[0]

			def get_xy(idx: int) -> Tuple[float, float]:
				pt = landmarks.landmark[idx]
				return (pt.x * w, pt.y * h)

			left_eye = [get_xy(i) for i in LEFT_EYE_IDX]
			right_eye = [get_xy(i) for i in RIGHT_EYE_IDX]
			ear_left = eye_aspect_ratio(left_eye)
			ear_right = eye_aspect_ratio(right_eye)
			ear_raw = (ear_left + ear_right) / 2.0
			# Smooth EAR using simple moving average
			ear_window.append(ear_raw)
			ear = float(sum(ear_window) / len(ear_window))

			# Adaptive threshold using robust stats (median - 1.5 * MAD)
			if len(ear_window) >= 5:
				arr = np.array(ear_window, dtype=float)
				med = float(np.median(arr))
				mad = float(np.median(np.abs(arr - med))) or 0.0
				adaptive_thr = max(ear_blink_threshold, med - 1.5 * mad)
			else:
				adaptive_thr = ear_blink_threshold

			# Blink detection with edge-trigger and refractory period
			is_below = ear < adaptive_thr
			if prev_ear_above and is_below and frames_since_last_blink >= min_frames_between_blinks:
				blinks += 1
				frames_since_last_blink = 0
			prev_ear_above = not is_below
			frames_since_last_blink += 1

			# Facial jitter via nose movement, normalized by inter-ocular distance and smoothed
			nose = get_xy(NOSE_TIP_IDX)
			# Inter-ocular distance as scale (between eye centers)
			left_center = ((left_eye[0][0] + left_eye[3][0]) / 2.0, (left_eye[0][1] + left_eye[3][1]) / 2.0)
			right_center = ((right_eye[0][0] + right_eye[3][0]) / 2.0, (right_eye[0][1] + right_eye[3][1]) / 2.0)
			scale = euclidean_distance(left_center, right_center) or 1.0
			if prev_nose is not None:
				disp = euclidean_distance(nose, prev_nose) / scale
				# Exponential smoothing to reduce noise
				if jitter_distances:
					alpha = 0.2
					smoothed = alpha * disp + (1.0 - alpha) * jitter_distances[-1]
					jitter_distances.append(smoothed)
				else:
					jitter_distances.append(disp)
			prev_nose = nose

			frames_analyzed += 1

		frame_index += 1

	cap.release()
	face_mesh.close()

	minutes_processed = (frames_analyzed * frame_stride) / (fps * 60.0) if fps > 0 else 0
	avg_blink_rate = (blinks / minutes_processed) if minutes_processed > 0 else float(blinks)
	jitter_std = float(np.std(jitter_distances)) if (np is not None and jitter_distances) else 0.0

	return VideoFeatureStats(
		avg_blink_rate_per_minute=float(avg_blink_rate),
		facial_jitter_std_dev=jitter_std,
		frames_analyzed=frames_analyzed,
	)


# -----------------------------
# Audio feature extraction
# -----------------------------

def _extract_audio_with_ffmpeg(video_path: str) -> Optional[Tuple[str, int, float]]:
	"""Extract audio track to a temporary WAV file using ffmpeg, return (wav_path, sr, duration)."""
	if ffmpeg is None:
		return None
	try:
		tmp_fd, tmp_wav = tempfile.mkstemp(suffix=".wav")
		os.close(tmp_fd)
		(
			ffmpeg
				.input(video_path)
				.output(tmp_wav, ac=1, ar=16000, format="wav", loglevel="error")
				.overwrite_output()
				.run()
		)
		# Probe duration if possible
		duration = 0.0
		try:
			probe = ffmpeg.probe(tmp_wav)
			for s in probe.get("streams", []):
				if s.get("codec_type") == "audio":
					duration = float(s.get("duration", 0.0) or 0.0)
					break
		except Exception:
			pass
		return tmp_wav, 16000, duration
	except Exception:
		return None


def extract_audio_features(video_path: str) -> Optional[AudioFeatureStats]:
	if np is None or librosa is None:
		return None

	y: Optional[np.ndarray] = None
	sr: int = 16000
	duration_seconds: float = 0.0

	# Try to load audio directly via librosa (audioread/ffmpeg backend)
	try:
		y, sr = librosa.load(video_path, sr=16000, mono=True)
		duration_seconds = float(len(y)) / float(sr)
	except Exception:
		# Fallback to explicit ffmpeg extraction
		ff = _extract_audio_with_ffmpeg(video_path)
		if ff is None:
			return None
		wav_path, sr, duration_seconds = ff
		try:
			y, _ = librosa.load(wav_path, sr=sr, mono=True)
		finally:
			try:
				os.remove(wav_path)
			except Exception:
				pass

	if y is None or len(y) == 0:
		return None

	# Compute MFCCs and summarize
	mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
	mfcc_mean = float(np.mean(mfcc))
	mfcc_std = float(np.std(mfcc))

	return AudioFeatureStats(
		audio_mfcc_mean=mfcc_mean,
		audio_mfcc_std=mfcc_std,
		sample_rate=sr,
		duration_seconds=duration_seconds,
	)


# -----------------------------
# Metadata extraction
# -----------------------------

def _safe_int(v: Any) -> Optional[int]:
	try:
		return int(v)
	except Exception:
		return None


def _safe_float(v: Any) -> Optional[float]:
	try:
		return float(v)
	except Exception:
		return None


def _fps_from_fraction(frac: str) -> Optional[float]:
	if not frac or frac == "0/0":
		return None
	try:
		num, den = frac.split("/")
		n = float(num)
		d = float(den)
		return n / d if d != 0 else None
	except Exception:
		return None


def extract_metadata_features(video_path: str) -> Optional[MetadataStats]:
	if ffmpeg is None:
		return None
	try:
		probe = ffmpeg.probe(video_path)
		fmt = probe.get("format", {})
		streams = probe.get("streams", [])

		container_format = fmt.get("format_name")
		file_size_bytes = _safe_int(fmt.get("size"))
		duration_seconds = _safe_float(fmt.get("duration"))
		bit_rate = _safe_int(fmt.get("bit_rate"))

		video_streams = [s for s in streams if s.get("codec_type") == "video"]
		audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

		v = video_streams[0] if video_streams else {}
		a = audio_streams[0] if audio_streams else {}

		video_codec = v.get("codec_name") if v else None
		video_width = _safe_int(v.get("width")) if v else None
		video_height = _safe_int(v.get("height")) if v else None
		video_avg_fps = _fps_from_fraction(v.get("avg_frame_rate", "")) if v else None

		audio_codec = a.get("codec_name") if a else None
		audio_sample_rate = _safe_int(a.get("sample_rate")) if a else None
		audio_channels = _safe_int(a.get("channels")) if a else None

		return MetadataStats(
			container_format=container_format,
			file_size_bytes=file_size_bytes,
			duration_seconds=duration_seconds,
			bit_rate=bit_rate,
			has_video=bool(video_streams),
			has_audio=bool(audio_streams),
			video_codec=video_codec,
			video_width=video_width,
			video_height=video_height,
			video_avg_fps=video_avg_fps,
			audio_codec=audio_codec,
			audio_sample_rate=audio_sample_rate,
			audio_channels=audio_channels,
		)
	except Exception:
		return None


# -----------------------------
# Public API
# -----------------------------

def extract_features(video_path: str, frame_stride: int = 5, ear_blink_threshold: float = 0.21) -> ExtractedFeatures:
	video_stats = extract_video_features(video_path, frame_stride=frame_stride, ear_blink_threshold=ear_blink_threshold)
	audio_stats = extract_audio_features(video_path)
	metadata_stats = extract_metadata_features(video_path)
	return ExtractedFeatures(video=video_stats, audio=audio_stats, metadata=metadata_stats)


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Extract video/audio features for deepfake detection")
	parser.add_argument("video_path", help="Path to input video file")
	parser.add_argument("--frame-stride", type=int, default=5, help="Analyze every Nth frame")
	parser.add_argument("--blink-threshold", type=float, default=0.21, help="EAR threshold for blink detection")
	parser.add_argument("--vector", action="store_true", help="Print only the numeric feature vector")
	args = parser.parse_args()

	if not os.path.exists(args.video_path):
		raise SystemExit(f"File not found: {args.video_path}")

	# Allow overriding defaults
	video_stats = extract_video_features(args.video_path, frame_stride=args.frame_stride, ear_blink_threshold=args.blink_threshold)
	audio_stats = extract_audio_features(args.video_path)
	metadata_stats = extract_metadata_features(args.video_path)
	features = ExtractedFeatures(video=video_stats, audio=audio_stats, metadata=metadata_stats)

	if args.vector:
		print(json.dumps(features.to_feature_vector()))
	else:
		print(json.dumps(features.to_dict(), indent=2))
