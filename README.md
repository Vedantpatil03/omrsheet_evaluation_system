# 🎯 OMR Evaluation System

An **Automated Optical Mark Recognition (OMR) Evaluation System** built with Flask backend and Streamlit frontend. This system can automatically evaluate OMR answer sheets and provide detailed subject-wise scoring.

![OMR System Demo](https://img.shields.io/badge/Status-Active-green) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Flask](https://img.shields.io/badge/Flask-2.0+-red) ![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-orange)

## ✨ Features

- 🔍 **Automated OMR Detection** - Uses OpenCV for bubble detection and evaluation
- 📊 **Subject-wise Scoring** - Breaks down scores by individual subjects
- 🎨 **Modern Web Interface** - Beautiful, responsive Streamlit frontend
- 📱 **Multi-version Support** - Handles different exam versions (A, B, C)
- 💾 **Database Storage** - SQLite database for result persistence
- 🚀 **Real-time Processing** - Instant evaluation and results
- 📈 **Performance Analytics** - Visual score breakdown and percentages

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Streamlit
- **Image Processing**: OpenCV, NumPy
- **Database**: SQLite
- **Deployment**: Ready for Heroku/Docker

## 📋 Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Vedantpatil03/omrsheet_evaluation_system.git
cd omrsheet_evaluation_system
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application

**Option A: Use the startup script (Windows)**
```bash
start.bat
```

**Option B: Manual startup**
```bash
# Terminal 1: Start Flask Backend
python app.py

# Terminal 2: Start Streamlit Frontend
streamlit run streamlit_app.py
```

### 5. Access the Application
- **Streamlit UI**: http://localhost:8501
- **Flask API**: http://localhost:5000

## 📁 Project Structure

```
omr_evaluation_system/
├── 📁 omr_logic/
│   ├── __init__.py
│   └── evaluation.py          # Core OMR processing logic
├── 📄 app.py                  # Flask backend API
├── 📄 streamlit_app.py        # Streamlit frontend
├── 📄 subject_config.json     # Subject configuration
├── 📄 start.bat              # Windows startup script
├── 📄 requirements.txt       # Python dependencies
├── 📄 Procfile              # Deployment configuration
├── 📄 .gitignore            # Git ignore rules
└── 📄 README.md             # Project documentation
```

## 🎮 How to Use

1. **Start the System**: Run both Flask backend and Streamlit frontend
2. **Upload OMR Sheet**: Select and upload a clear image of the filled OMR sheet
3. **Enter Details**: 
   - Student ID
   - Exam Version (A, B, or C)
4. **Evaluate**: Click "Evaluate Sheet" to process
5. **View Results**: Get instant subject-wise scores and total percentage

## 📊 Supported Subjects

The system evaluates 5 subjects (20 questions each):
- **Python Programming**
- **Data Analysis** 
- **MySQL Database**
- **PowerBI**
- **Advanced Statistics**

## 🔧 Configuration

### Subject Configuration
Edit [`subject_config.json`](subject_config.json) to modify subjects and question counts:

```json
{
  "subjects": [
    {"name": "Python", "questions": 20},
    {"name": "Data Analysis", "questions": 20},
    {"name": "MySQL", "questions": 20},
    {"name": "PowerBI", "questions": 20},
    {"name": "Adv Stats", "questions": 20}
  ]
}
```

## 📸 Screenshots

### Main Interface
![Main Interface](https://via.placeholder.com/800x400?text=OMR+Evaluation+Interface)

### Results Display
![Results](https://via.placeholder.com/800x400?text=Subject-wise+Results)


## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**



## 👨‍💻 Developer

**Vedant Patil**
- GitHub: [@Vedantpatil03](https://github.com/Vedantpatil03)
- LinkedIn: [Connect with me](https://linkedin.com/in/vedant-patil)



## 🙏 Acknowledgments

- OpenCV community for image processing capabilities
- Streamlit team for the amazing web framework
- Flask community for the robust backend framework

---
