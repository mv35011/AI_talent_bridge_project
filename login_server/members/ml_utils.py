import tensorflow as tf
import numpy as np
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

class ProfileScorer:
    def __init__(self):
        try:
            self.analyzer = pipeline('text-classification', model='bert-base-uncased')
        except Exception as e:
            print(f"Error initializing pipeline: {e}")
            self.analyzer = None
        self.vectorizer = TfidfVectorizer()

    def calculate_score(self, user_profile):
        try:

            resume_score = self.analyze_resume(user_profile.resume) if user_profile.resume else 0
            skill_score = self.evaluate_skills(user_profile.skills)
            college_score = self.evaluate_college(user_profile.department)
            experience_score = 0


            print(f"Resume score: {resume_score}")
            print(f"Skill score: {skill_score}")
            print(f"College score: {college_score}")


            weights = {
                'resume_score': 0.4,
                'skill_score': 0.3,
                'college_score': 0.2,
                'experience_score': 0.1
            }

            total_score = (
                resume_score * weights['resume_score'] +
                skill_score * weights['skill_score'] +
                college_score * weights['college_score'] +
                experience_score * weights['experience_score']
            )


            final_score = min(max(round(total_score * 100), 0), 100)
            print(f"Final calculated score: {final_score}")
            return final_score

        except Exception as e:
            print(f"Error calculating score: {e}")
            return 50

    def analyze_resume(self, resume):
        try:
            resume_text = "Sample resume text"
            result = self.analyzer(resume_text)[0] if self.analyzer else {'score': 0}
            return float(result['score'])
        except Exception as e:
            print(f"Error analyzing resume: {e}")
            return 0

    def evaluate_skills(self, skills):
        try:
            skill_weights = {
                'AI_ML': 0.9,
                'WEB_DEV': 0.8,
                'ANDROID': 0.8
            }
            if not skills:
                return 0.5

            total_weight = sum(skill_weights.get(skill, 0.5) for skill in skills)
            return min(total_weight / len(skills), 1.0)
        except Exception as e:
            print(f"Error evaluating skills: {e}")
            return 0.5

    def evaluate_college(self, department):
        department_weights = {
            'CSE': 0.9,
            'IT': 0.85,
            'ECE': 0.8,
            'ME': 0.75,
            'Other': 0.7
        }
        return department_weights.get(department, 0.7)