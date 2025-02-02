
import PyPDF2
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from transformers import pipeline
import re
from collections import Counter
import torch
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
logger = logging.getLogger(__name__)
class ResumeOptimizer:
    def __init__(self):

        try:
            nltk.data.path.append('/path/to/custom/nltk_data')
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('averaged_perceptron_tagger')
        except Exception as e:
            logger.error(f"Error downloading NLTK data: {e}")
            raise


        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        try:

            self.analyzer = pipeline(
                'text-classification',
                model='distilbert-base-uncased',  # Smaller model
                device=self.device
            )
            self.summarizer = pipeline(
                'summarization',
                model='facebook/bart-base',  # Smaller model
                device=self.device
            )
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
            raise


        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        self.linkedin_pattern = re.compile(r'linkedin\.com/\S+')
        self.bullet_patterns = [re.compile(f'^{pattern}') for pattern in [r'•', r'-', r'\*', r'\d+\.']]

    async def process_resume(self, pdf_file):

        try:

            text = await self._async_extract_text(pdf_file)


            with ThreadPoolExecutor() as executor:
                metrics_future = executor.submit(self.analyze_resume, text)


                metrics = metrics_future.result()


                current_score = self.calculate_score(metrics)


                optimization_results = await self._async_optimize(text, metrics)


                optimized_metrics = self.analyze_resume(optimization_results['optimized_text'])
                optimized_score = self.calculate_score(optimized_metrics)

            return {
                'current_score': round(current_score),
                'optimized_score': round(optimized_score),
                'suggestions': optimization_results['suggestions'],
                'optimized_text': optimization_results['optimized_text']
            }

        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            raise

    async def _async_extract_text(self, pdf_file):

        try:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise

    def analyze_resume(self, text):

        words = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))


        metrics = {
            'total_words': len(words),
            'unique_words': len(set(words)),
            'action_verbs': self._count_action_verbs(text),
            'skills_mentioned': self._extract_skills(text),
            'contact_info_present': self._check_contact_info(text),
            'bullets_ratio': self._count_bullet_points(text) / len(text.split('\n')) if text.split('\n') else 0
        }

        return metrics

    def calculate_score(self, metrics):

        score = 0
        weights = {
            'action_verbs': 20,
            'skills_present': 25,
            'contact_info': 15,
            'bullets_ratio': 20,
            'content_quality': 20
        }


        score += min(metrics['action_verbs'] / 10 * weights['action_verbs'], weights['action_verbs'])


        score += min(len(metrics['skills_mentioned']) / 8 * weights['skills_present'], weights['skills_present'])

        # Score contact info (0-15)
        score += weights['contact_info'] if metrics['contact_info_present'] else 0

        # Score bullet points ratio (0-20)
        optimal_ratio = 0.4
        bullets_score = (1 - abs(metrics['bullets_ratio'] - optimal_ratio)) * weights['bullets_ratio']
        score += max(0, bullets_score)


        quality_score = self._analyze_content_quality(metrics)
        score += quality_score * weights['content_quality'] / 100

        return round(score, 2)

    async def _async_optimize(self, text, metrics):

        suggestions = []
        optimized_text = text


        with ThreadPoolExecutor() as executor:
            if metrics['action_verbs'] < 10:
                suggestions.append("Increase use of action verbs to better describe achievements")
                future = executor.submit(self._enhance_action_verbs, optimized_text)
                optimized_text = future.result()

            if len(metrics['skills_mentioned']) < 8:
                suggestions.append("Add more relevant technical and soft skills")
                future = executor.submit(self._enhance_skills, optimized_text)
                optimized_text = future.result()

        return {
            'suggestions': suggestions,
            'optimized_text': optimized_text
        }

    def _count_action_verbs(self, text):

        words = word_tokenize(text)
        tagged = nltk.pos_tag(words)
        action_verbs = [word for word, pos in tagged if pos.startswith('VB')]
        return len(action_verbs)

    def _extract_skills(self, text):


        skill_keywords = {
            'python', 'java', 'javascript', 'sql', 'aws', 'docker',
            'leadership', 'communication', 'teamwork', 'problem-solving'
        }
        words = word_tokenize(text.lower())
        return list(set(words) & skill_keywords)

    def _check_contact_info(self, text):

        patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'linkedin\.com/\S+'
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    def _count_bullet_points(self, text):

        bullet_patterns = [r'•', r'-', r'\*', r'\d+\.']
        count = 0
        for pattern in bullet_patterns:
            count += len(re.findall(f'^{pattern}', text, re.MULTILINE))
        return count

    def _analyze_content_quality(self, metrics):

        # Simplified scoring based on metrics
        quality_score = 0
        if metrics['total_words'] > 300:
            quality_score += 30
        if metrics['unique_words'] / metrics['total_words'] > 0.4:
            quality_score += 40
        if metrics['action_verbs'] > 15:
            quality_score += 30
        return min(quality_score, 100)

    def _enhance_action_verbs(self, text):

        weak_to_strong = {
            'worked': 'spearheaded',
            'did': 'executed',
            'made': 'developed',
            'helped': 'facilitated',
            'responsible for': 'managed'
        }
        enhanced = text
        for weak, strong in weak_to_strong.items():
            enhanced = re.sub(r'\b' + weak + r'\b', strong, enhanced, flags=re.IGNORECASE)
        return enhanced

    def _enhance_skills(self, text):


        return text

    def _convert_to_bullets(self, text):

        sentences = nltk.sent_tokenize(text)
        return '\n'.join(f'• {sent}' for sent in sentences if len(sent.split()) > 5)

    def _enhance_achievements(self, text):


        chunks = [text[i:i + 500] for i in range(0, len(text), 500)]
        enhanced = []
        for chunk in chunks:
            try:
                summary = self.summarizer(chunk, max_length=100, min_length=30)[0]['summary_text']
                enhanced.append(summary)
            except:
                enhanced.append(chunk)
        return ' '.join(enhanced)