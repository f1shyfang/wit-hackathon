from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from datetime import datetime

from db import init_db, insert_job, update_job_result, get_job

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
		
		# TODO: Start background analysis process
		# For hackathon demo, simulate processing immediately
		mock_results = {
			'authenticity_score': 85.2,
			'confidence': 0.92,
			'features': {
				'blink_rate': 12.5,
				'facial_jitter': 0.15,
				'audio_mfcc_variance': 0.23
			}
		}
		update_job_result(job_id, status='completed', results=mock_results)
		
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
