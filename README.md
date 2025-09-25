# FNOL Claim Processing Dashboard

A multi-agent orchestration system for First Notice of Loss (FNOL) claim processing with a real-time dashboard interface.

## 🏗️ Architecture

This project consists of two main components:

- **Backend**: FastAPI-based multi-agent system with SQLite database
- **Frontend**: React-based dashboard with real-time claim processing visualization

### Multi-Agent System

The backend implements a sophisticated multi-agent architecture:

- **Orchestrator Agent**: Coordinates the entire claim processing workflow
- **Intake Agent**: Handles initial claim data validation and processing
- **Risk Assessment Agent**: Evaluates claim risk levels and priorities
- **Routing Agent**: Determines appropriate processing paths based on claim characteristics

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **npm** or **yarn** (for frontend package management)

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the backend server:**
   ```bash
   python main.py
   ```

   The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend dashboard will be available at `http://localhost:5173`

## 🖥️ Usage

1. **Start both servers** (backend and frontend) as described above
2. **Open your browser** and navigate to `http://localhost:5173`
3. **View the dashboard** with real-time claim processing metrics
4. **Process claims** by clicking the "Process Claim" button in the Live Claim Processing section
5. **Monitor progress** through the workflow visualization and system metrics

## 📊 Dashboard Features

### System Metrics
- **Total Claims Processed**: Real-time count of processed claims
- **Processing Queue**: Number of claims currently in queue
- **Active Agents**: Status of multi-agent system components

### Live Claim Processing
- Real-time claim processing with workflow visualization
- Progress tracking through multiple processing stages
- Interactive claim processing controls

### Agent Status
- Multi-agent system health monitoring
- Individual agent status and performance metrics

### Results Summary
- Processing results and analytics
- Recently completed claims history
- System performance metrics

## 🔧 API Endpoints

### Claims Management
- `GET /claims` - Retrieve all claims
- `GET /claims/{claim_id}` - Get specific claim details
- `GET /claims/{claim_id}/status` - Get claim processing status
- `POST /claims/{claim_id}/process` - Trigger claim processing

### System Monitoring
- `GET /system/metrics` - Get system performance metrics
- `GET /system/agents/status` - Get multi-agent system status

## 🛠️ Development

### Backend Development
- **Framework**: FastAPI with async support
- **Database**: SQLite with SQLAlchemy ORM
- **Multi-Agent**: LangGraph for agent orchestration
- **API Documentation**: Available at `http://localhost:8000/docs` when running

### Frontend Development
- **Framework**: React 19 with Vite
- **Styling**: CSS with modern design patterns
- **Build Tool**: Vite for fast development and building

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
```

**Backend:**
The backend runs directly with Python. For production deployment, consider using:
- **Gunicorn** or **Uvicorn** for ASGI server
- **Docker** for containerization
- **Environment variables** for configuration

## 📁 Project Structure

```
zoop-assignment/
├── backend/
│   ├── agents/              # Multi-agent system components
│   ├── db/                  # Database configuration
│   ├── models/              # Data models
│   ├── routes/              # API route handlers
│   ├── schema/              # Pydantic schemas
│   ├── main.py              # FastAPI application entry point
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # Styling
│   │   └── main.jsx         # React entry point
│   ├── package.json         # Node.js dependencies
│   └── vite.config.js       # Vite configuration
└── README.md                # This file
```

## 🔍 Troubleshooting

### Common Issues

1. **Backend not starting:**
   - Ensure Python 3.8+ is installed
   - Check if virtual environment is activated
   - Verify all dependencies are installed

2. **Frontend not loading:**
   - Ensure Node.js 16+ is installed
   - Check if npm dependencies are installed
   - Verify backend is running on port 8000

3. **CORS issues:**
   - Backend is configured to allow frontend origin
   - Ensure both servers are running on correct ports

### Port Configuration

- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:5173`

If you need to change ports, update the configuration in:
- Backend: `main.py` (uvicorn configuration)
- Frontend: `vite.config.js` (server configuration)

## 📝 License

This project is part of a technical assignment and is for demonstration purposes.