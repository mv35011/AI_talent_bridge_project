# members/llm_service.py

import torch
from transformers import pipeline
import json
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Stage:
    title: str
    description: str
    skills: List[str]


@dataclass
class Roadmap:
    stages: List[Stage]


class LLMService:
    _instance = None
    _generator = None

    CAREER_CONTEXTS = {
        'web_dev': {
            'title': 'Web Development',
            'context': 'modern web development focusing on frontend (HTML, CSS, JavaScript) and backend (APIs, databases)',
            'example_skills': ['React', 'Node.js', 'SQL', 'API Design', 'Cloud Services']
        },
        'ai_ml': {
            'title': 'AI/ML Development',
            'context': 'artificial intelligence and machine learning with focus on model development and deployment',
            'example_skills': ['PyTorch', 'TensorFlow', 'Data Analysis', 'MLOps', 'Algorithm Design']
        },
        'android_dev': {
            'title': 'Android Development',
            'context': 'mobile app development focusing on Android platform and modern architecture',
            'example_skills': ['Kotlin', 'Android SDK', 'Material Design', 'App Architecture', 'Testing']
        }
    }

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._generator is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Using device: {device}")

            self._generator = pipeline(
                "text-generation",
                model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                device=device,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )

    def generate_roadmap(self, resume_text: str, career_path: str) -> Dict:
        prompt = self._create_prompt(resume_text, career_path)

        try:
            response = self._generator(
                prompt,
                max_length=2048,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                do_sample=True
            )

            roadmap_dict = self._parse_response(response[0]['generated_text'])
            self._validate_roadmap(roadmap_dict)
            return roadmap_dict

        except Exception as e:
            print(f"Generation error: {str(e)}")
            return self._get_fallback_roadmap(career_path)

    def _create_prompt(self, resume_text: str, career_path: str) -> str:
        career_info = self.CAREER_CONTEXTS.get(career_path, self.CAREER_CONTEXTS['web_dev'])

        return f"""<s>[INST] You are a career development expert. Create a detailed career roadmap for a {career_info['title']} professional based on this resume:

{resume_text[:1000]}

Create a progression with exactly 3 stages focused on {career_info['context']}.

For each stage, provide:
1. A specific title that reflects the seniority level (e.g., "Junior Developer", "Senior Engineer")
2. A clear 2-3 sentence description of responsibilities and focus areas
3. Exactly 4 specific technical skills to develop (similar to: {', '.join(career_info['example_skills'])})

Format your response as a JSON object like this:
{{
    "stages": [
        {{
            "title": "clear role title",
            "description": "specific 2-3 sentence description",
            "skills": ["specific skill 1", "specific skill 2", "specific skill 3", "specific skill 4"]
        }}
    ]
}}

Ensure your response contains only the JSON object, no other text. [/INST]</s>"""

    def _parse_response(self, response_text: str) -> Dict:
        try:
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON structure found in response")

            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)

        except Exception as e:
            print(f"Parsing error: {str(e)}")
            raise

    def _validate_roadmap(self, roadmap: Dict) -> None:
        if not isinstance(roadmap, dict) or 'stages' not in roadmap:
            raise ValueError("Invalid roadmap structure")

        stages = roadmap['stages']
        if not isinstance(stages, list) or len(stages) != 3:
            raise ValueError("Roadmap must have exactly 3 stages")

        for stage in stages:
            if not all(key in stage for key in ['title', 'description', 'skills']):
                raise ValueError("Stage missing required fields")
            if not isinstance(stage['skills'], list) or len(stage['skills']) != 4:
                raise ValueError("Each stage must have exactly 4 skills")

    def _get_fallback_roadmap(self, career_path: str) -> Dict:
        career_info = self.CAREER_CONTEXTS.get(career_path, self.CAREER_CONTEXTS['web_dev'])

        return {
            "stages": [
                {
                    "title": f"Junior {career_info['title']} Developer",
                    "description": "Focus on building fundamental skills and understanding best practices. Work on small to medium features under guidance.",
                    "skills": career_info['example_skills'][:4]
                },
                {
                    "title": f"Mid-Level {career_info['title']} Developer",
                    "description": "Take ownership of larger features and mentor junior developers. Focus on architecture and system design.",
                    "skills": ["System Design", "Code Review", "Performance Optimization", "Technical Leadership"]
                },
                {
                    "title": f"Senior {career_info['title']} Developer",
                    "description": "Lead major technical initiatives and make architectural decisions. Focus on team growth and technical strategy.",
                    "skills": ["Architecture Design", "Team Leadership", "Strategic Planning", "Technical Innovation"]
                }
            ]
        }