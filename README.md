# NotReal.ly - Deepfake Detection Platform

A comprehensive deepfake detection system built for hackathon demonstration, featuring a Next.js frontend and Flask backend with multi-modal AI analysis.

## Test at https://notreally.vercel.app/

##  Features

- **Multi-Modal Analysis**: Combines facial feature analysis, audio processing, and metadata extraction
- **Real-time Processing**: Fast analysis with live progress updates
- **Interactive Dashboard**: Beautiful charts and detailed feature breakdowns
- **Explainable AI**: Shows which features contributed to the authenticity score
- **Modern UI**: Built with Next.js, TypeScript, and Tailwind CSS

##  Architecture

```
wit-hackathon/
├── frontend/          # Next.js React application
│   ├── src/
│   │   ├── app/       # App router pages
│   │   ├── components/ # React components
│   │   └── types/     # TypeScript type definitions
│   └── package.json
├── backend/           # Flask Python API
│   ├── app.py         # Main Flask application
│   ├── requirements.txt
│   └── uploads/       # Temporary file storage
└── plan.md           # Detailed implementation plan
```

##  Tech Stack

### Frontend
- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Lucide React** for icons
- **Axios** for API communication

### Backend
- **Flask** for REST API
- **Flask-CORS** for cross-origin requests
- **OpenCV** for video processing
- **MediaPipe** for facial analysis
- **Librosa** for audio processing
- **XGBoost** for ML classification
- **SQLite** for data storage (planned)

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- FFmpeg (for video processing)

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Train the model (using your real/fake datasets)
```bash
cd backend
# Quotes are needed for the space in the real dataset folder name
python train_model.py "DFD_original sequences" DFD_manipulated_sequences
# This writes backend/model.pkl
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## 📊 Analysis Pipeline

1. **File Upload**: User uploads video file via drag-and-drop interface
2. **Feature Extraction**: 
   - Facial landmark detection using MediaPipe
   - Blink rate calculation
   - Facial jitter analysis
   - Audio MFCC extraction
3. **ML Classification**: XGBoost model predicts authenticity score
4. **Results Display**: Interactive dashboard with charts and explanations

## 🎯 Key Features

### File Upload Component
- Drag-and-drop interface
- File type and size validation
- Real-time upload progress
- Error handling

### Analysis Dashboard
- Authenticity score with confidence level
- Feature breakdown charts
- Detailed metrics table
- Explainable AI insights

### API Endpoints
- `POST /api/analyze` - Upload and analyze video
- `GET /api/results/<job_id>` - Get analysis results
- `GET /api/health` - Health check

## 🔧 Development

### Adding New Features
1. Update types in `frontend/src/types/`
2. Create components in `frontend/src/components/`
3. Add API endpoints in `backend/app.py`
4. Update the analysis pipeline as needed

### Testing
```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
python -m pytest
```

## 📈 Future Enhancements

- [ ] Real-time video streaming analysis
- [ ] Batch processing for multiple files
- [ ] User authentication and history
- [ ] Advanced ML models (CNN, Transformer)
- [ ] API rate limiting and security
- [ ] Docker containerization
- [ ] Cloud deployment (AWS/GCP)

## 🤝 Contributing

This is a hackathon project, but contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is created for educational and hackathon purposes.
