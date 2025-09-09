'use client';

import { useState, useRef } from 'react';
import { Upload, FileVideo, AlertCircle } from 'lucide-react';
import axios from 'axios';
import type { AnalysisResult } from '@/types/analysis';

interface FileUploadProps {
	onAnalysisStart: () => void;
	onAnalysisComplete: (result: AnalysisResult) => void;
}

export default function FileUpload({ onAnalysisStart, onAnalysisComplete }: FileUploadProps) {
	const [dragActive, setDragActive] = useState(false);
	const [uploading, setUploading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const fileInputRef = useRef<HTMLInputElement>(null);

	const handleDrag = (e: React.DragEvent) => {
		e.preventDefault();
		e.stopPropagation();
		if (e.type === 'dragenter' || e.type === 'dragover') {
			setDragActive(true);
		} else if (e.type === 'dragleave') {
			setDragActive(false);
		}
	};

	const handleDrop = (e: React.DragEvent) => {
		e.preventDefault();
		e.stopPropagation();
		setDragActive(false);
		
		if (e.dataTransfer.files && e.dataTransfer.files[0]) {
			handleFile(e.dataTransfer.files[0]);
		}
	};

	const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
		if (e.target.files && e.target.files[0]) {
			handleFile(e.target.files[0]);
		}
	};

	const handleFile = async (file: File) => {
		setError(null);
		
		// Validate file type
		if (!file.type.startsWith('video/')) {
			setError('Please upload a video file (MP4, AVI, MOV, etc.)');
			return;
		}

		// Validate file size (100MB limit)
		if (file.size > 100 * 1024 * 1024) {
			setError('File size must be less than 100MB');
			return;
		}

		setUploading(true);
		onAnalysisStart();

		try {
			const formData = new FormData();
			formData.append('file', file);

			const response = await axios.post('http://localhost:52513/api/analyze', formData, {
				headers: {
					'Content-Type': 'multipart/form-data',
				},
			});

			// Start polling for results
			pollForResults(response.data.job_id);
		} catch (err) {
			setError('Failed to upload file. Please try again.');
			setUploading(false);
			console.error('Upload error:', err);
		}
	};

	const pollForResults = async (jobId: string) => {
		const pollInterval = setInterval(async () => {
			try {
				const response = await axios.get(`http://localhost:52513/api/results/${jobId}`);
				
				if (response.data.status === 'completed') {
					clearInterval(pollInterval);
					setUploading(false);
					onAnalysisComplete(response.data as AnalysisResult);
				} else if (response.data.status === 'failed') {
					clearInterval(pollInterval);
					setError('Analysis failed. Please try again.');
					setUploading(false);
				}
			} catch (err) {
				clearInterval(pollInterval);
				setError('Failed to get analysis results.');
				setUploading(false);
				console.error('Polling error:', err);
			}
		}, 2000); // Poll every 2 seconds
	};

	return (
		<div className="w-full max-w-2xl mx-auto">
			<div
				className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
					dragActive
						? 'border-indigo-500 bg-indigo-50'
						: 'border-gray-300 hover:border-gray-400'
				} ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
				onDragEnter={handleDrag}
				onDragLeave={handleDrag}
				onDragOver={handleDrag}
				onDrop={handleDrop}
			>
				<input
					ref={fileInputRef}
					type="file"
					accept="video/*"
					onChange={handleFileInput}
					className="hidden"
				/>

				<div className="space-y-4">
					<div className="mx-auto w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">
						{uploading ? (
							<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
						) : (
							<FileVideo className="w-8 h-8 text-indigo-600" />
						)}
					</div>

					<div>
						<h3 className="text-lg font-semibold text-gray-900 mb-2">
							{uploading ? 'Uploading...' : 'Upload Video for Analysis'}
						</h3>
						<p className="text-gray-600 mb-4">
							Drag and drop your video file here, or click to browse
						</p>
					</div>

					{!uploading && (
						<button
							onClick={() => fileInputRef.current?.click()}
							className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
						>
							<Upload className="w-5 h-5 mr-2" />
							Choose Video File
						</button>
					)}

					<div className="text-sm text-gray-500">
						<p>Supported formats: MP4, AVI, MOV, WMV</p>
						<p>Maximum file size: 100MB</p>
					</div>
				</div>
			</div>

			{error && (
				<div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-center">
					<AlertCircle className="w-5 h-5 text-red-400 mr-2" />
					<span className="text-red-700">{error}</span>
				</div>
			)}
		</div>
	);
}
