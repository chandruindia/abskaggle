# abskaggle
 A project for kaggle,antibiotic selection for vulnearable patients-Created by chandrasekaran kamatchi,TN.India
-----------

==========================================
ANTIBIOTIC ADVISOR FOR VULNERABLE PATIENTS
==========================================

Project using Gemma 4 AI to help doctors select antibiotics for:
- Pregnant Women
- Pediatrics (children)
- Elderly Patients

==========================================
REQUIREMENTS
==========================================

Python 3.9 or higher

Install these packages:
- flask
- flask-cors
- huggingface-hub

Install command:
pip install flask flask-cors huggingface-hub

==========================================
HOW TO RUN
==========================================

Step 1: Open terminal/command prompt

Step 2: Navigate to project folder
cd path/to/project

Step 3: Run the application
python app.py

Step 4: Wait 2-5 minutes (first time only)
- Model downloads from Hugging Face
- Libraries cache locally

Step 5: Open browser and go to
http://localhost:5000

==========================================
HOW TO USE
==========================================

1. Select Patient Group (Pregnant/Pediatric/Elder)
2. Enter Age and Weight (optional)
3. Enter Diagnosis (e.g., UTI, pneumonia)
4. Add allergies or conditions (optional)
5. Click "Get AI Recommendation"
6. View antibiotic suggestion + Gemma analysis

==========================================
SAMPLE INPUTS
==========================================

Test Case 1 - Pregnant with UTI:
- Patient Group: Pregnant Women
- Age: 28
- Weight: 65
- Diagnosis: urinary tract infection
- Comorbidities: none

Test Case 2 - Child with Pneumonia:
- Patient Group: Pediatrics
- Age: 4
- Weight: 16
- Diagnosis: pneumonia
- Comorbidities: none

Test Case 3 - Elderly with UTI:
- Patient Group: Elders
- Age: 74
- Weight: 68
- Diagnosis: UTI
- Comorbidities: diabetes, kidney problems

Test Case 4 - Penicillin Allergy:
- Patient Group: Pediatrics
- Age: 8
- Weight: 25
- Diagnosis: strep throat
- Comorbidities: penicillin allergy

==========================================
IMPORTANT NOTES
==========================================

⚠️ This is a DEMONSTRATION project
⚠️ Not for real medical use
⚠️ Dataset has only 10-15 real antibiotics
⚠️ Other drug data is randomly generated
⚠️ First run takes 2-5 minutes (model download)

==========================================
PROJECT STRUCTURE
==========================================

project/
├── app.py              # Main Flask application
├── templates/
│   └── index.html      # Web interface
├── data_enhanced.xml   # Knowledge base
└── requirements.txt    # Dependencies

==========================================
API ENDPOINTS
==========================================

POST /api/recommend  - Get antibiotic recommendation
GET  /api/health     - Check server status
GET  /api/patient-groups - List available groups

==========================================
TROUBLESHOOTING
==========================================

Problem: Server won't start
Solution: Check Python version and install all packages

Problem: Gemma not responding
Solution: Check internet connection (first time only)

Problem: Port 5000 already in use
Solution: Change port in app.py (last line)

==========================================
CONTACT
==========================================
Email: chandru009@gmail.com  
LinkedIn: [linkedin.com/chandruindia](https://www.linkedin.com/in/chandruindia/)

Project for Competition Submission
Model: Google Gemma 4 (2B-IT) via Hugging Face

==========================================
```
