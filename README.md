**Automated OMR Evaluation System**
Project Overview


This is a full-stack web application designed to automate the process of evaluating OMR (Optical Mark Recognition) sheets. The system uses computer vision to accurately read student responses from a scanned OMR sheet image, providing instant, detailed score reports. This project aims to streamline the grading process, reduce manual effort, and minimize errors in evaluation.

**Features**

Automated Grading: Instantly evaluates OMR sheets by analyzing uploaded images.

Accurate Scoring: Uses computer vision algorithms to ensure precise detection of marked answers.

Detailed Score Reports: Provides a summary of the total score, percentage, and a subject-wise breakdown of marks.

Intuitive User Interface: A clean and easy-to-use front end built with Streamlit.

Scalable Architecture: A decoupled backend and frontend, making it easy to manage and extend.


**Tech Stack**

Backend: Python, Flask

Frontend: Streamlit

Computer Vision: OpenCV

Dependency Management: pip

Deployment: Docker (recommended for production)

**Quick Start Guide**

Follow these steps to set up and run the project locally.

**Prerequisites**

Python 3.8 or higher

**pip package manager**

1. Clone the repository
2. git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)

cd your-repo-name

3. Set up the backend
4. Navigate to the backend directory and install the required Python packages.

cd backend

pip install -r requirements.txt

flask run

3. Set up the frontend
4. Open a new terminal, navigate to the frontend directory, and install the required Python packages.

cd ..
cd frontend

pip install -r requirements.txt

streamlit run streamlit_app.py



