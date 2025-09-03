import pandas as pd
import numpy as np
from typing import Dict, List, Set
import os
import joblib

class MLQuizRecommendationSystem:
    def __init__(self, df: pd.DataFrame, models_dir='models'):
        self.df = df
        if 'id' not in self.df.columns:
            raise ValueError("Dataset must have a unique 'id' column for each question.")
        self.df['question_id'] = self.df['id']
        self.topics = sorted(df['topic'].unique())
        self.difficulties = ['easy', 'medium', 'hard']
        
        # Enhanced topic relations for progressive learning
        self.topic_relations = {
            'Python': ['Data Structures', 'Algorithms'],
            'Data Structures': ['Algorithms', 'Machine Learning'],
            'SQL': ['Database Management', 'Data Structures'],
            'Machine Learning': ['Artificial Intelligence', 'Deep Learning'],
            'Artificial Intelligence': ['Deep Learning', 'Computer Networks'],
            'Computer Networks': ['Cybersecurity', 'Database Management'],
            'Algorithms': ['Machine Learning', 'Artificial Intelligence'],
            'Database Management': ['Machine Learning', 'SQL'],
            'Cybersecurity': ['Computer Networks', 'Python'],
            'Deep Learning': ['Machine Learning', 'Artificial Intelligence']
        }
        
        try:
            self.learner_classifier = joblib.load(os.path.join(models_dir, 'learner_classifier.joblib'))
            self.engagement_analyzer = joblib.load(os.path.join(models_dir, 'engagement_analyzer.joblib'))
            self.learner_type_encoder = joblib.load(os.path.join(models_dir, 'learner_type_encoder.joblib'))
            self.engagement_level_encoder = joblib.load(os.path.join(models_dir, 'engagement_level_encoder.joblib'))
            print("AI models loaded successfully.")
        except FileNotFoundError as e:
            print(f"Warning: Model files not found in '{models_dir}'. Using rule-based recommendations only.")
            self.learner_classifier = None
            self.engagement_analyzer = None

    def get_questions(self, topic: str, difficulty: str, num_questions: int, seen_ids: Set[int]) -> pd.DataFrame:
        """
        Gets unique questions, ensuring no repetition by filtering out seen IDs.
        """
        # Filter by topic and difficulty
        filtered_df = self.df[(self.df['topic'] == topic) & (self.df['difficulty'] == difficulty)]
        
        # Remove questions that have already been seen
        available_questions = filtered_df[~filtered_df['question_id'].isin(seen_ids)]
        
        if available_questions.empty:
            print(f"No new questions available for {topic} - {difficulty}")
            return pd.DataFrame()
        
        # Sample the requested number of questions (or all available if less)
        num_to_sample = min(num_questions, len(available_questions))
        selected_questions = available_questions.sample(n=num_to_sample, random_state=np.random.randint(1000))
        
        return selected_questions.reset_index(drop=True)

    def analyze_learning_pattern(self, history: List[Dict]) -> Dict:
        """
        Analyzes user's learning pattern from their quiz history.
        """
        # --- FIX: Extract summaries first ---
        summaries = [record['summary'] for record in history if 'summary' in record]
        
        if len(summaries) < 2:
            return {'pattern': 'new_learner', 'trend': 'stable', 'struggling_topics': [], 'recent_avg': 0, 'consistency': 0.8}
        
        recent_scores = [quiz['accuracy'] for quiz in summaries[-5:]] # Last 5 quizzes
        
        # Determine learning trend
        if len(recent_scores) >= 3:
            # Ensure there are enough elements for slicing
            if len(recent_scores) > 3:
                recent_trend = np.mean(recent_scores[-3:]) - np.mean(recent_scores[-5:-2])
            else:
                 recent_trend = np.mean(recent_scores) - np.mean([s['accuracy'] for s in summaries[:-len(recent_scores)]] or [0.5])

            if recent_trend > 0.1:
                trend = 'improving'
            elif recent_trend < -0.1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        # Identify struggling topics (accuracy < 0.5)
        topic_performance = {}
        for quiz in summaries:
            topic = quiz['topic']
            if topic not in topic_performance:
                topic_performance[topic] = []
            topic_performance[topic].append(quiz['accuracy'])
        
        struggling_topics = []
        for topic, scores in topic_performance.items():
            if np.mean(scores) < 0.5:
                struggling_topics.append(topic)
        
        # Determine overall pattern
        avg_score = np.mean(recent_scores)
        if avg_score < 0.4:
            pattern = 'struggling'
        elif avg_score > 0.7:
            pattern = 'advanced'
        else:
            pattern = 'developing'
        
        return {
            'pattern': pattern,
            'trend': trend,
            'struggling_topics': struggling_topics,
            'recent_avg': avg_score,
            'consistency': 1 - np.std(recent_scores) if len(recent_scores) > 1 else 0.8
        }

    def recommend_next_quiz(self, history: List[Dict]) -> Dict:
        """
        Enhanced recommendation system that handles multiple learning scenarios.
        """
        # First quiz - start with easy Python
        if not history:
            return {
                'topic': 'Python',
                'difficulty': 'easy',
                'num_questions': 5,
                'message': '👋 Welcome! Let\'s start with a gentle introduction to assess your level.',
                'reason': 'first_quiz'
            }

        # --- FIX: Get the summary of the last quiz ---
        last_quiz_summary = history[-1]['summary']
        learning_analysis = self.analyze_learning_pattern(history)
        
        current_topic = last_quiz_summary['topic']
        current_difficulty = last_quiz_summary['difficulty']
        current_score = last_quiz_summary['accuracy']
        current_num_questions = last_quiz_summary['total']
        
        # SCENARIO 1: STRUGGLING LEARNER (Score < 40%)
        if current_score < 0.4:
            return self._handle_struggling_learner(history, learning_analysis, current_topic, current_num_questions)
        
        # SCENARIO 2: MODERATE PERFORMER (40% <= Score < 70%)
        elif 0.4 <= current_score < 0.7:
            return self._handle_moderate_learner(history, learning_analysis, current_topic, current_difficulty, current_num_questions)
        
        # SCENARIO 3: HIGH PERFORMER (Score >= 70%)
        else:
            return self._handle_advanced_learner(history, learning_analysis, current_topic, current_difficulty, current_num_questions)

    def _handle_struggling_learner(self, history: List[Dict], analysis: Dict, current_topic: str, current_num_questions: int) -> Dict:
        """Handle recommendations for struggling learners."""
        # --- FIX: Extract summaries ---
        summaries = [record['summary'] for record in history if 'summary' in record]
        
        consecutive_struggles = 0
        for quiz in reversed(summaries):
            if quiz['topic'] == current_topic and quiz['difficulty'] == 'easy' and quiz['accuracy'] < 0.4:
                consecutive_struggles += 1
            else:
                break
        
        if consecutive_struggles >= 3:
            new_num_questions = 3
            message = f"🎯 Let's take it step by step with just 3 questions to build your confidence in {current_topic}."
        elif consecutive_struggles >= 2:
            new_num_questions = max(3, current_num_questions - 3)
            message = f"💪 Don't worry! Let's practice {current_topic} with fewer questions to reduce pressure."
        else:
            new_num_questions = max(5, current_num_questions - 2)
            message = f"📚 Let's review the fundamentals of {current_topic}. You're learning!"
        
        if len(analysis['struggling_topics']) > 2 and len(summaries) >= 3:
            topic_scores = {}
            for quiz in summaries:
                topic = quiz['topic']
                if topic not in topic_scores:
                    topic_scores[topic] = []
                topic_scores[topic].append(quiz['accuracy'])
            
            best_topic = max(topic_scores.keys(), key=lambda t: np.mean(topic_scores[t]))
            if best_topic != current_topic:
                return {
                    'topic': best_topic,
                    'difficulty': 'easy',
                    'num_questions': 5,
                    'message': f"🌟 Let's build confidence with {best_topic}, where you've shown good progress!",
                    'reason': 'confidence_building'
                }
        
        return {
            'topic': current_topic,
            'difficulty': 'easy',
            'num_questions': new_num_questions,
            'message': message,
            'reason': 'struggling_support'
        }

    def _handle_moderate_learner(self, history: List[Dict], analysis: Dict, current_topic: str, current_difficulty: str, current_num_questions: int) -> Dict:
        """Handle recommendations for moderate performers."""
        if current_num_questions <= 5:
            new_num_questions = 10
        elif current_num_questions <= 10:
            new_num_questions = 15
        else:
            new_num_questions = min(20, current_num_questions + 2)
        
        if current_difficulty == 'easy':
            return {
                'topic': current_topic,
                'difficulty': 'medium',
                'num_questions': new_num_questions,
                'message': f"📈 Good progress! Ready to tackle medium-level {current_topic} questions?",
                'reason': 'difficulty_progression'
            }
        
        return {
            'topic': current_topic,
            'difficulty': 'medium',
            'num_questions': new_num_questions,
            'message': f"👍 You're doing well! Let's solidify your {current_topic} knowledge with more practice.",
            'reason': 'skill_reinforcement'
        }

    def _handle_advanced_learner(self, history: List[Dict], analysis: Dict, current_topic: str, current_difficulty: str, current_num_questions: int) -> Dict:
        """Handle recommendations for advanced learners."""
        # --- FIX: Extract summaries ---
        summaries = [record['summary'] for record in history if 'summary' in record]
        new_num_questions = min(20, current_num_questions + 3)
        
        if current_difficulty == 'easy':
            return {
                'topic': current_topic,
                'difficulty': 'medium',
                'num_questions': new_num_questions,
                'message': f"🚀 Excellent! Time to challenge yourself with medium {current_topic} questions.",
                'reason': 'difficulty_advancement'
            }
        
        elif current_difficulty == 'medium':
            return {
                'topic': current_topic,
                'difficulty': 'hard',
                'num_questions': new_num_questions,
                'message': f"🔥 Outstanding! Ready for the ultimate {current_topic} challenge?",
                'reason': 'mastery_challenge'
            }
        
        else: # current_difficulty == 'hard'
            next_topics = self.topic_relations.get(current_topic, [])
            if not next_topics:
                mastered_topics = set()
                for quiz in summaries:
                    if quiz['difficulty'] == 'hard' and quiz['accuracy'] >= 0.7:
                        mastered_topics.add(quiz['topic'])
                
                available_topics = [t for t in self.topics if t not in mastered_topics]
                if available_topics:
                    next_topic = np.random.choice(available_topics)
                else:
                    next_topic = np.random.choice(self.topics)
            else:
                next_topic = np.random.choice(next_topics)
            
            return {
                'topic': next_topic,
                'difficulty': 'medium',
                'num_questions': 10,
                'message': f"🎓 Congratulations! You've mastered {current_topic}. Let's explore {next_topic}!",
                'reason': 'topic_mastery'
            }

    def get_available_questions_count(self, topic: str, difficulty: str, seen_ids: Set[int]) -> int:
        """Returns the count of available unseen questions for a topic-difficulty combination."""
        filtered_df = self.df[(self.df['topic'] == topic) & (self.df['difficulty'] == difficulty)]
        available_questions = filtered_df[~filtered_df['question_id'].isin(seen_ids)]
        return len(available_questions)

    def get_learning_stats(self, history: List[Dict]) -> Dict:
        """Generate comprehensive learning statistics."""
        # --- FIX: Extract summaries ---
        summaries = [record['summary'] for record in history if 'summary' in record]

        if not summaries:
            return {}
        
        total_questions = sum(quiz['total'] for quiz in summaries)
        total_correct = sum(quiz['correct'] for quiz in summaries)
        overall_accuracy = total_correct / total_questions if total_questions > 0 else 0
        
        topic_stats = {}
        for quiz in summaries:
            topic = quiz['topic']
            if topic not in topic_stats:
                topic_stats[topic] = {'correct': 0, 'total': 0, 'quizzes': 0}
            topic_stats[topic]['correct'] += quiz['correct']
            topic_stats[topic]['total'] += quiz['total']
            topic_stats[topic]['quizzes'] += 1
        
        for topic in topic_stats:
            topic_stats[topic]['accuracy'] = (
                topic_stats[topic]['correct'] / topic_stats[topic]['total'] 
                if topic_stats[topic]['total'] > 0 else 0
            )
        
        return {
            'total_quizzes': len(summaries),
            'total_questions': total_questions,
            'total_correct': total_correct,
            'overall_accuracy': overall_accuracy,
            'topic_stats': topic_stats,
            'learning_analysis': self.analyze_learning_pattern(history) # This function is now fixed
        }

    def _calculate_session_features(self, history: List[Dict]) -> Dict:
        """Calculates aggregated features from the user's recent quiz history."""
        # --- FIX: Extract summaries ---
        summaries = [record['summary'] for record in history if 'summary' in record]

        if not summaries:
            return {}
        
        recent_sessions = summaries[-3:] # Last 3 sessions
        accuracies = [s['accuracy'] for s in recent_sessions]
        total_questions = sum(s['total'] for s in recent_sessions)
        
        accuracy = np.mean(accuracies) if accuracies else 0.5
        consistency = 1 - np.std(accuracies) if len(accuracies) > 1 else 0.8
        avg_time = 30 + (1 - accuracy) * 20
        avg_attempts = 1.0 + (1 - accuracy) * 0.5
        
        return {
            'accuracy': accuracy,
            'total_questions': total_questions,
            'avg_time_seconds': avg_time,
            'avg_attempts': avg_attempts,
            'consistency': consistency
        }

    def get_ai_predictions(self, history: List[Dict]) -> Dict:
        """Get AI-based predictions if models are available."""
        if not self.learner_classifier or not self.engagement_analyzer:
            return {}
        
        # --- FIX: This function now correctly handles the structure ---
        features = self._calculate_session_features(history)
        if not features:
            return {}
        
        try:
            feature_vector = [features[k] for k in ['accuracy', 'total_questions', 'avg_time_seconds', 'avg_attempts', 'consistency']]
            
            learner_probs = self.learner_classifier.predict_proba([feature_vector])[0]
            learner_type = self.learner_type_encoder.inverse_transform([np.argmax(learner_probs)])[0]
            
            engagement_probs = self.engagement_analyzer.predict_proba([feature_vector])[0]
            engagement_level = self.engagement_level_encoder.inverse_transform([np.argmax(engagement_probs)])[0]
            
            return {
                "learner_type": learner_type,
                "learner_probs": dict(zip(self.learner_type_encoder.classes_, learner_probs)),
                "engagement_level": engagement_level,
                "engagement_probs": dict(zip(self.engagement_level_encoder.classes_, engagement_probs)),
                "features": features
            }
        except Exception as e:
            print(f"Error in AI predictions: {e}")
            return {}