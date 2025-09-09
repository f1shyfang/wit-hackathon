from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from datetime import datetime

from db import init_db, insert_job, update_job_result, get_job
from feature_extractor import extract_features
from predictor import predict_proba, load_model
import numpy as np  # type: ignore

app = Flask(__name__)
CORS(app)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
	os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Initialize database
init_db()

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
	"""Upload and analyze a video file for deepfake detection"""
	if 'file' not in request.files:
		return jsonify({'error': 'No file provided'}), 400
	
	file = request.files['file']
	if file.filename == '':
		return jsonify({'error': 'No file selected'}), 400
	
	if file:
		# Generate unique job ID
		job_id = str(uuid.uuid4())
		
		# Save file
		filename = f"{job_id}_{file.filename}"
		filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
		file.save(filepath)
		
		# Persist job
		created_at = datetime.now().isoformat()
		insert_job(job_id=job_id, filename=file.filename, filepath=filepath, status='processing', created_at=created_at)
		
		# Run synchronous analysis (can be moved to background worker later)
		try:
			features = extract_features(filepath)
			vector = np.array(features.to_feature_vector(), dtype=float)
			model = load_model()
			prob_real, prob_fake = predict_proba(vector, model=model)
			authenticity_score = float(prob_real * 100.0)

			# Legacy demo fields expected by frontend dashboard
			legacy_features = {
				'blink_rate': (features.video.avg_blink_rate_per_minute if features.video else 0.0) or 0.0,
				'facial_jitter': (features.video.facial_jitter_std_dev if features.video else 0.0) or 0.0,
				'audio_mfcc_variance': (features.audio.audio_mfcc_std if features.audio else 0.0) or 0.0,
			}

			# Human-readable summary
			if authenticity_score >= 80.0:
				summary_text = "This appears to be a real video."
			else:
				parts = []
				if legacy_features['blink_rate'] < 10:
					parts.append("low blink rate")
				if legacy_features['facial_jitter'] >= 0.2:
					parts.append("high facial jitter")
				if legacy_features['audio_mfcc_variance'] >= 0.3:
					parts.append("synthetic-sounding audio patterns")
				reason = ", ".join(parts) if parts else "multiple subtle cues"
				summary_text = f"Potential deepfake indicators: {reason}."

			results = {
				'authenticity_score': authenticity_score,
				'confidence': float(max(prob_real, prob_fake)),
				'probabilities': {
					'real': prob_real,
					'fake': prob_fake
				},
				'features': legacy_features,
				'summary': summary_text,
			}
			update_job_result(job_id, status='completed', results=results)
		except Exception as e:
			update_job_result(job_id, status='failed', results={'error': str(e)})
		
		return jsonify({
			'job_id': job_id,
			'status': 'processing',
			'message': 'Video uploaded successfully'
		})

@app.route('/api/results/<job_id>', methods=['GET'])
def get_results(job_id):
	"""Get analysis results for a specific job"""
	job = get_job(job_id)
	if not job:
		return jsonify({'error': 'Job not found'}), 404
	return jsonify(job)

@app.route('/api/health', methods=['GET'])
def health_check():
	"""Health check endpoint"""
	return jsonify({'status': 'healthy', 'message': 'NotReal.ly API is running'})

if __name__ == '__main__':
	app.run(debug=True, port=52513)
