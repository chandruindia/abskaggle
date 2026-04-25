from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import xml.etree.ElementTree as ET
from huggingface_hub import InferenceClient
import os
import random
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = 'antibiotic-stewardship-secret-key-2026'
CORS(app)  # Enable CORS for frontend

# ============================================
# DATABASE CLASS WITH UNRESOLVED QUERIES
# ============================================

class Database:
    """Simple database class for storing queries and unresolved queries"""
    
    def __init__(self):
        self.queries = []           # Resolved queries (successful recommendations)
        self.unresolved_queries = [] # Unresolved queries (no research available)
    
    def save_query(self, query_data):
        """Save a resolved query (successful recommendation)"""
        self.queries.append(query_data)
        return True
    
    def save_unresolved_query(self, query_data):
        """Save an unresolved query (no research available)"""
        query_data['saved_at'] = str(datetime.now())
        self.unresolved_queries.append(query_data)
        return True
    
    def get_recent_queries(self, limit=10):
        """Get recent resolved queries"""
        return self.queries[-limit:]
    
    def get_unresolved_queries(self, limit=50):
        """Get unresolved queries for admin panel"""
        return self.unresolved_queries[-limit:]
    
    def get_all_unresolved_queries(self):
        """Get all unresolved queries"""
        return self.unresolved_queries
    
    def get_unresolved_count(self):
        """Get count of unresolved queries"""
        return len(self.unresolved_queries)
    
    def get_resolved_count(self):
        """Get count of resolved queries"""
        return len(self.queries)

db = Database()

# ============================================
# DISEASES WITH NO RESEARCH (VIRAL/NON-BACTERIAL CONDITIONS)
# ============================================

NO_RESEARCH_DISEASES = {
    "Pediatrics": [
        "chickenpox", "measles", "rubella", "roseola", "fifth disease",
        "epilepsy", "autism spectrum", "autism"
    ],
    "PregnantWomen": [
        "hypothyroidism", "preeclampsia", "eclampsia", "ectopic pregnancy"
    ],
    "Elders": [
        "hypertension", "high blood pressure", "ischemic heart disease", 
        "heart failure", "dyslipidemia", "high cholesterol", "stroke",
        "parkinson's disease", "parkinson"
    ]
}

# ============================================
# ANTIBIOTIC DATABASE (from drugsnew.txt and data_enhanced.xml)
# ============================================

ANTIBIOTIC_DATABASE = {
    "PregnantWomen": {
        "factors": {
            "age_range": "18-40",
            "contraindications": "Avoid teratogenic drugs; consider fetal safety",
            "precautions": "Monitor renal function; avoid near term for some drugs"
        },
        "antibiotics": [
            {
                "name": "Amoxicillin",
                "aware": "Access",
                "indications": ["UTI", "respiratory infections", "GBS prophylaxis"],
                "efficacy": 85,
                "risk": 15,
                "notes": "First-line for asymptomatic bacteriuria; safe in pregnancy",
                "best_for": "UTI, respiratory infections, GBS prophylaxis"
            },
            {
                "name": "Nitrofurantoin",
                "aware": "Access",
                "indications": ["uncomplicated UTI", "cystitis"],
                "efficacy": 88,
                "risk": 20,
                "notes": "Avoid near term (38+ weeks); first-line for cystitis",
                "best_for": "uncomplicated UTI, cystitis"
            },
            {
                "name": "Cefixime",
                "aware": "Watch",
                "indications": ["UTI", "pharyngitis", "gonorrhea"],
                "efficacy": 82,
                "risk": 25,
                "notes": "Good for pyelonephritis step-down",
                "best_for": "UTI, pharyngitis, gonorrhea"
            },
            {
                "name": "Ceftriaxone",
                "aware": "Watch",
                "indications": ["pyelonephritis", "sepsis", "gonorrhea"],
                "efficacy": 90,
                "risk": 35,
                "notes": "Reserve for severe infections; IV/IM only",
                "best_for": "pyelonephritis, sepsis, gonorrhea"
            },
            {
                "name": "Azithromycin",
                "aware": "Watch",
                "indications": ["respiratory infections", "chlamydia"],
                "efficacy": 85,
                "risk": 28,
                "notes": "Safe in pregnancy; short course",
                "best_for": "respiratory infections, chlamydia"
            },
            {
                "name": "Penicillin V",
                "aware": "Access",
                "indications": ["strep throat", "dental prophylaxis"],
                "efficacy": 80,
                "risk": 10,
                "notes": "Narrow spectrum; safe in pregnancy",
                "best_for": "strep throat, dental prophylaxis"
            }
        ]
    },
    
    "Pediatrics": {
        "factors": {
            "age_range": "<18",
            "contraindications": "Age-specific safety profiles",
            "precautions": "Weight-based dosing required"
        },
        "antibiotics": [
            {
                "name": "Amoxicillin",
                "aware": "Access",
                "indications": ["otitis media", "sinusitis", "strep throat", "CAP"],
                "efficacy": 75,
                "risk": 12,
                "notes": "First-line for AOM, CAP, pharyngitis",
                "best_for": "otitis media, sinusitis, strep throat"
            },
            {
                "name": "Amoxicillin-Clavulanate",
                "aware": "Access",
                "indications": ["recurrent AOM", "sinusitis", "CAP"],
                "efficacy": 82,
                "risk": 25,
                "notes": "Broader coverage; more GI side effects",
                "best_for": "recurrent AOM, sinusitis, CAP"
            },
            {
                "name": "Cefdinir",
                "aware": "Watch",
                "indications": ["AOM", "sinusitis", "CAP", "skin infections"],
                "efficacy": 85,
                "risk": 20,
                "notes": "Alternative for penicillin allergy",
                "best_for": "AOM, sinusitis, CAP, skin infections"
            },
            {
                "name": "Cefixime",
                "aware": "Watch",
                "indications": ["UTI", "gonorrhea", "typhoid fever"],
                "efficacy": 80,
                "risk": 22,
                "notes": "Good for UTI, pharyngitis",
                "best_for": "UTI, gonorrhea, typhoid fever"
            },
            {
                "name": "Ceftriaxone",
                "aware": "Watch",
                "indications": ["sepsis", "meningitis", "severe CAP"],
                "efficacy": 90,
                "risk": 30,
                "notes": "Reserve for severe infections requiring IV",
                "best_for": "sepsis, meningitis, severe CAP"
            },
            {
                "name": "Azithromycin",
                "aware": "Watch",
                "indications": ["atypical pneumonia", "pertussis", "mycoplasma"],
                "efficacy": 87,
                "risk": 18,
                "notes": "Short course; monitor for cardiac effects",
                "best_for": "atypical pneumonia, pertussis, mycoplasma"
            }
        ]
    },
    
    "Elders": {
        "factors": {
            "age_range": "60+",
            "contraindications": "Renal/hepatic considerations",
            "precautions": "Monitor for nephrotoxicity; adjust for renal function"
        },
        "antibiotics": [
            {
                "name": "Nitrofurantoin",
                "aware": "Access",
                "indications": ["uncomplicated UTI", "cystitis"],
                "efficacy": 85,
                "risk": 25,
                "notes": "Avoid if CrCl <30; well-tolerated",
                "best_for": "uncomplicated UTI, cystitis"
            },
            {
                "name": "Amoxicillin-Clavulanate",
                "aware": "Access",
                "indications": ["CAP", "sinusitis", "skin infections"],
                "efficacy": 80,
                "risk": 28,
                "notes": "Monitor renal function; adjust dose",
                "best_for": "CAP, sinusitis, skin infections"
            },
            {
                "name": "Cefpodoxime",
                "aware": "Watch",
                "indications": ["CAP", "UTI", "skin infections"],
                "efficacy": 83,
                "risk": 24,
                "notes": "Good oral option; renal adjustment",
                "best_for": "CAP, UTI, skin infections"
            },
            {
                "name": "Ceftriaxone",
                "aware": "Watch",
                "indications": ["severe CAP", "sepsis", "pyelonephritis"],
                "efficacy": 90,
                "risk": 38,
                "notes": "Reserve for severe infections requiring IV",
                "best_for": "severe CAP, sepsis, pyelonephritis"
            },
            {
                "name": "Doxycycline",
                "aware": "Watch",
                "indications": ["atypical pneumonia", "skin infections"],
                "efficacy": 82,
                "risk": 30,
                "notes": "Avoid in severe renal impairment; photosensitivity",
                "best_for": "atypical pneumonia, skin infections"
            },
            {
                "name": "Levofloxacin",
                "aware": "Reserve",
                "indications": ["CAP", "complicated UTI", "prostatitis"],
                "efficacy": 88,
                "risk": 45,
                "notes": "Avoid in elderly due to tendon rupture risk",
                "best_for": "CAP, complicated UTI, prostatitis"
            }
        ]
    }
}

# ============================================
# GEMMA MODEL CLASS (USING INFERENCECLIENT)
# ============================================

class GemmaModel:
    def __init__(self):
        # Try to get token from environment variable, otherwise use None (will work for some models)
        self.token = os.getenv("HF_TOKEN", None)
        try:
            self.client = InferenceClient(
                model="google/gemma-2b-it",
                token=self.token
            )
            self.available = True
        except Exception as e:
            print(f"Warning: Could not initialize Gemma client: {e}")
            self.available = False
            self.client = None

    def generate_clinical_recommendation(self, patient_type, diagnosis, antibiotic):
        if not self.available:
            # Fallback response when Gemma is not available
            return self._generate_fallback_recommendation(patient_type, diagnosis, antibiotic)
        
        prompt = f"""You are a clinical pharmacist. Provide a brief, evidence-based recommendation.

Patient: {patient_type}
Diagnosis: {diagnosis}
Recommended Antibiotic: {antibiotic.get('name', 'Unknown')}

Provide a 2-3 sentence explanation of why this antibiotic is appropriate, including key clinical considerations."""

        try:
            response = self.client.text_generation(
                prompt,
                max_new_tokens=150,
                temperature=0.3,
                do_sample=True
            )
            return response.strip()
        except Exception as e:
            print(f"Gemma API Error: {e}")
            return self._generate_fallback_recommendation(patient_type, diagnosis, antibiotic)
    
    def _generate_fallback_recommendation(self, patient_type, diagnosis, antibiotic):
        """Fallback when Gemma API is unavailable"""
        templates = {
            "PregnantWomen": f"For a pregnant patient with {diagnosis}, {antibiotic['name']} is recommended due to its favorable safety profile in pregnancy. It provides effective coverage against common pathogens while minimizing fetal risk.",
            "Pediatrics": f"For this pediatric patient with {diagnosis}, {antibiotic['name']} is the appropriate choice. Weight-based dosing should be used, and clinical response should be monitored within 48-72 hours.",
            "Elders": f"For this elderly patient with {diagnosis}, {antibiotic['name']} is recommended. Renal function should be assessed before dosing, and the patient should be monitored for adverse effects."
        }
        return templates.get(patient_type, f"{antibiotic['name']} is recommended for {diagnosis} in this patient population.")


# ============================================
# ANTIBIOTIC ADVISOR CLASS
# ============================================

class AntibioticAdvisor:
    def __init__(self):
        self.database = ANTIBIOTIC_DATABASE
        self.xml_data = self.load_xml_data()
        self.no_research_diseases = NO_RESEARCH_DISEASES

    def load_xml_data(self):
        """Load XML data if available"""
        try:
            tree = ET.parse('data_enhanced.xml')
            return tree.getroot()
        except Exception as e:
            print(f"Could not load data_enhanced.xml: {e}")
            return None

    def _check_no_research(self, patient_type, diagnosis):
        """Check if the diagnosis has no research/antibiotic indication"""
        if patient_type not in self.no_research_diseases:
            return False
        
        diagnosis_lower = diagnosis.lower().strip()
        for disease in self.no_research_diseases[patient_type]:
            if disease.lower() in diagnosis_lower:
                return True
        return False

    def _score_antibiotic(self, ab, diagnosis, patient_type, age=None, weight=None, comorbidities=None):
        """Score an antibiotic based on multiple factors"""
        score = ab["efficacy"] - (ab["risk"] * 0.3)  # Base score
        
        # Boost score based on diagnosis match
        diagnosis_lower = diagnosis.lower()
        best_for = ab.get("best_for", "").lower()
        if best_for and any(indication.lower() in diagnosis_lower for indication in ab["indications"]):
            score += 15
        
        # Adjust for patient-specific factors
        if patient_type == "Pediatrics" and weight and weight < 10:
            if "suspension" in ab["notes"].lower() or "oral" in ab["notes"].lower():
                score += 5
        
        if patient_type == "Elders" and age and age > 75:
            if ab["risk"] > 35:
                score -= 20
        
        if comorbidities:
            comorb_lower = comorbidities.lower()
            if "renal" in comorb_lower or "kidney" in comorb_lower:
                if "renal" in ab["notes"].lower() or "crcl" in ab["notes"].lower():
                    score -= 15
            if "penicillin allergy" in comorb_lower and "penicillin" in ab["notes"].lower():
                score -= 50
        
        # AWaRe preference
        if ab["aware"] == "Access":
            score += 3
        elif ab["aware"] == "Reserve":
            score -= 2
            
        return max(0, score)  # Score can't be negative

    def recommend_antibiotic(self, patient_type: str, diagnosis: str, 
                            age: int = None, weight: float = None, 
                            comorbidities: str = None):
        """
        Recommend best antibiotic based on patient factors and diagnosis.
        
        Returns:
            Tuple of (best_antibiotic_dict, list_of_alternative_names, no_research_flag)
        """
        # Check if diagnosis has no research available
        no_research = self._check_no_research(patient_type, diagnosis)
        if no_research:
            return None, None, True
        
        # Validate patient type
        if patient_type not in self.database:
            return None, None, False
        
        # Get available antibiotics for this patient group
        available_abs = self.database[patient_type]["antibiotics"]
        
        # Score each antibiotic
        scored_abs = []
        for ab in available_abs:
            score = self._score_antibiotic(ab, diagnosis, patient_type, age, weight, comorbidities)
            scored_abs.append((ab, score))
        
        # Sort by score (highest first)
        scored_abs.sort(key=lambda x: x[1], reverse=True)
        
        if not scored_abs or scored_abs[0][1] <= 0:
            return None, None, False
        
        # Get best antibiotic and alternatives
        best_antibiotic = scored_abs[0][0]
        alternatives = [ab["name"] for ab, _ in scored_abs[1:4]]
        
        return best_antibiotic, alternatives, False


# ============================================
# INITIALIZE COMPONENTS
# ============================================

advisor = AntibioticAdvisor()
gemma = GemmaModel()

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        patient_type = data.get('patient_type')
        diagnosis = data.get('diagnosis')
        age = data.get('age')
        weight = data.get('weight')
        comorbidities = data.get('comorbidities')
        
        # Validate required fields
        if not patient_type:
            return jsonify({'success': False, 'error': 'patient_type is required'}), 400
        if not diagnosis:
            return jsonify({'success': False, 'error': 'diagnosis is required'}), 400
        
        # Get recommendation
        result = advisor.recommend_antibiotic(patient_type, diagnosis, age, weight, comorbidities)
        
        # Handle case with no research available
        if result and len(result) == 3 and result[2] == True:
            # Save to unresolved queries database
            unresolved_data = {
                'patient_type': patient_type,
                'diagnosis': diagnosis,
                'age': age,
                'weight': weight,
                'comorbidities': comorbidities,
                'reason': 'NO_RESEARCH_AVAILABLE',
                'timestamp': str(datetime.now()),
                'status': 'pending_review'
            }
            db.save_unresolved_query(unresolved_data)
            
            return jsonify({
                'success': False,
                'no_research': True,
                'error': f'There are no antibiotic research or recommendations available for {diagnosis} in {patient_type} patients. This condition may be viral, non-bacterial, or require non-antibiotic management. This query has been saved to unresolved queries for admin review.'
            }), 404
        
        if not result or result[0] is None:
            # Save failed recommendation to unresolved queries
            unresolved_data = {
                'patient_type': patient_type,
                'diagnosis': diagnosis,
                'age': age,
                'weight': weight,
                'comorbidities': comorbidities,
                'reason': 'NO_SUITABLE_ANTIBIOTIC_FOUND',
                'timestamp': str(datetime.now()),
                'status': 'pending_review'
            }
            db.save_unresolved_query(unresolved_data)
            
            return jsonify({
                'success': False,
                'error': f'No suitable antibiotic found for {patient_type} with diagnosis: {diagnosis}. This query has been saved to unresolved queries for admin review.'
            }), 404
        
        antibiotic, alternatives, _ = result
        
        # Generate Gemma clinical recommendation
        gemma_text = gemma.generate_clinical_recommendation(
            patient_type, diagnosis, antibiotic
        )
        
        # Save to resolved queries database
        db.save_query({
            'patient_type': patient_type,
            'diagnosis': diagnosis,
            'recommendation': antibiotic['name'],
            'timestamp': str(datetime.now()),
            'status': 'resolved'
        })
        
        return jsonify({
            'success': True,
            'antibiotic': antibiotic['name'],
            'aware_category': antibiotic['aware'],
            'efficacy_score': antibiotic['efficacy'],
            'risk_score': antibiotic['risk'],
            'alternatives': alternatives,
            'analysis': gemma_text,
            'prescribing_notes': antibiotic['notes']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/unresolved-queries', methods=['GET'])
def get_unresolved_queries():
    """Get all unresolved queries for admin panel"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        unresolved = db.get_unresolved_queries(limit)
        return jsonify({
            'success': True,
            'count': len(unresolved),
            'total_unresolved': db.get_unresolved_count(),
            'total_resolved': db.get_resolved_count(),
            'unresolved_queries': unresolved
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/unresolved-queries/all', methods=['GET'])
def get_all_unresolved_queries():
    """Get all unresolved queries"""
    try:
        unresolved = db.get_all_unresolved_queries()
        return jsonify({
            'success': True,
            'count': len(unresolved),
            'unresolved_queries': unresolved
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recent-queries', methods=['GET'])
def get_recent_queries():
    """Get recent resolved queries"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        queries = db.get_recent_queries(limit)
        return jsonify({
            'success': True,
            'queries': queries
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'patient_groups': list(ANTIBIOTIC_DATABASE.keys()),
        'gemma_available': gemma.available,
        'no_research_diseases': NO_RESEARCH_DISEASES,
        'unresolved_count': db.get_unresolved_count(),
        'resolved_count': db.get_resolved_count()
    })

@app.route('/api/patient-groups', methods=['GET'])
def get_patient_groups():
    groups = {}
    for group_name, group_data in ANTIBIOTIC_DATABASE.items():
        groups[group_name] = {
            'factors': group_data['factors'],
            'available_antibiotics': [ab['name'] for ab in group_data['antibiotics']],
            'no_research_conditions': NO_RESEARCH_DISEASES.get(group_name, [])
        }
    return jsonify(groups)


# ============================================
# RUN
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("Antibiotic Advisor API with Gemma Integration")
    print("=" * 50)
    print(f"Available patient groups: {list(ANTIBIOTIC_DATABASE.keys())}")
    print(f"Gemma model available: {gemma.available}")
    print(f"No research conditions loaded for each patient group")
    print(f"Unresolved queries will be saved for admin review")
    print("\nStarting Flask server on http://localhost:5000")
    print("API Endpoints:")
    print("  POST /api/recommend - Get antibiotic recommendation")
    print("  GET  /api/health    - Health check")
    print("  GET  /api/patient-groups - List available groups")
    print("  GET  /api/unresolved-queries - View unresolved queries (Admin)")
    print("  GET  /api/recent-queries - View recent resolved queries")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
