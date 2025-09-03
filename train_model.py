import pandas as pd
import numpy as np
import random
from datetime import datetime
import os
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score

# --- Configuration ---
DATASET_PATH = 'dataset.csv'
MODELS_DIR = 'models'
N_SYNTHETIC_USERS = 2000  # Increased for better training

class ModelTrainer:
    """
    Enhanced model trainer with more realistic synthetic data generation
    and better ML models for the quiz recommendation system.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.topics = sorted(df['topic'].unique())
        self.difficulties = ['easy', 'medium', 'hard']
        
        # Encoders
        self.topic_encoder = LabelEncoder().fit(self.topics)
        self.difficulty_encoder = LabelEncoder().fit(self.difficulties)
        self.learner_type_encoder = LabelEncoder()
        self.engagement_level_encoder = LabelEncoder()
        
        print(f"📊 Dataset loaded: {len(df)} questions across {len(self.topics)} topics")
        print(f"📚 Topics: {', '.join(self.topics)}")

    def generate_synthetic_user_data(self, n_users: int) -> pd.DataFrame:
        """
        Generates more realistic synthetic user interaction data for ML training.
        Creates diverse user profiles with different learning patterns.
        """
        print(f"🤖 Generating synthetic data for {n_users} users...")
        np.random.seed(42)
        random.seed(42)
        user_data = []

        for user_id in range(n_users):
            # Create diverse user profiles
            user_type = random.choice(['beginner', 'intermediate', 'advanced', 'inconsistent'])
            
            # Define user characteristics based on type
            if user_type == 'beginner':
                base_skill_range = (0.2, 0.5)
                consistency_range = (0.6, 0.9)
                sessions_range = (5, 12)
            elif user_type == 'intermediate':
                base_skill_range = (0.4, 0.7)
                consistency_range = (0.5, 0.8)
                sessions_range = (8, 18)
            elif user_type == 'advanced':
                base_skill_range = (0.7, 0.95)
                consistency_range = (0.7, 0.95)
                sessions_range = (10, 20)
            else:  # inconsistent
                base_skill_range = (0.3, 0.8)
                consistency_range = (0.2, 0.6)
                sessions_range = (3, 15)
            
            user_base_skill = np.random.uniform(*base_skill_range)
            user_consistency = np.random.uniform(*consistency_range)
            
            # Generate sessions for this user
            num_sessions = random.randint(*sessions_range)
            
            for session in range(num_sessions):
                topic = random.choice(self.topics)
                difficulty = random.choice(self.difficulties)
                
                # Topic affinity (some users are better at certain topics)
                topic_affinities = {t: np.random.normal(0, 0.15) for t in self.topics}
                topic_bonus = topic_affinities[topic]
                
                # Difficulty adjustment
                difficulty_adjustments = {
                    'easy': 0.15,
                    'medium': 0.0,
                    'hard': -0.20
                }
                difficulty_adjustment = difficulty_adjustments[difficulty]
                
                # Learning progression (users get better over time)
                progression_bonus = (session / num_sessions) * 0.1 if user_type != 'inconsistent' else 0
                
                # Calculate expected accuracy with some randomness
                expected_accuracy = np.clip(
                    user_base_skill + topic_bonus + difficulty_adjustment + progression_bonus +
                    np.random.normal(0, 0.1), 0.05, 0.98
                )
                
                # Add consistency factor
                if random.random() > user_consistency:
                    expected_accuracy *= random.uniform(0.5, 0.8)  # Bad day
                
                # Generate quiz results
                num_questions = random.randint(5, 20)
                correct_answers = np.random.binomial(num_questions, expected_accuracy)
                accuracy = correct_answers / num_questions
                
                # Time modeling (struggling users take longer)
                base_time_per_question = {
                    'easy': random.uniform(20, 40),
                    'medium': random.uniform(30, 50), 
                    'hard': random.uniform(40, 70)
                }[difficulty]
                
                # Adjust time based on performance
                time_multiplier = 2.0 - accuracy  # Lower accuracy = more time
                avg_time = base_time_per_question * time_multiplier * random.uniform(0.8, 1.2)
                
                # Attempts modeling
                avg_attempts = 1.0 + (1 - accuracy) * random.uniform(0.2, 0.8)
                
                # Session consistency (how consistent this session was with user's typical performance)
                session_consistency = user_consistency * random.uniform(0.7, 1.0)
                
                # Determine learner type based on performance patterns
                if accuracy >= 0.8 and avg_time < base_time_per_question * 1.2:
                    learner_type = 'Advanced'
                elif accuracy >= 0.65 and session_consistency > 0.7:
                    learner_type = 'Moderate'
                elif accuracy < 0.45 or avg_attempts > 1.4:
                    learner_type = 'Struggling'
                else:
                    learner_type = 'Balanced'
                
                # Engagement level calculation
                engagement_score = (
                    accuracy * 0.4 +  # Performance weight
                    (1 / (avg_time / base_time_per_question)) * 0.3 +  # Speed weight
                    session_consistency * 0.2 +  # Consistency weight
                    (1 / avg_attempts) * 0.1  # Attempts weight
                )
                engagement_score = np.clip(engagement_score, 0, 1)
                
                if engagement_score > 0.7:
                    engagement_level = 'High'
                elif engagement_score > 0.45:
                    engagement_level = 'Medium'
                else:
                    engagement_level = 'Low'

                user_data.append({
                    'user_id': user_id,
                    'session': session,
                    'accuracy': accuracy,
                    'total_questions': num_questions,
                    'avg_time_seconds': avg_time,
                    'avg_attempts': avg_attempts,
                    'consistency': session_consistency,
                    'learner_type': learner_type,
                    'engagement_level': engagement_level,
                    'topic': topic,
                    'difficulty': difficulty,
                    'user_type': user_type  # For analysis
                })
        
        df = pd.DataFrame(user_data)
        print(f"✅ Generated {len(df)} training samples")
        print(f"📊 Learner type distribution: {df['learner_type'].value_counts().to_dict()}")
        print(f"🔥 Engagement distribution: {df['engagement_level'].value_counts().to_dict()}")
        return df

    def train_and_save_models(self):
        """
        Trains enhanced ML models with cross-validation and saves them.
        """
        if not os.path.exists(MODELS_DIR):
            os.makedirs(MODELS_DIR)
            print(f"📁 Created directory: {MODELS_DIR}")

        training_data = self.generate_synthetic_user_data(N_SYNTHETIC_USERS)
        
        # Features for training
        feature_columns = ['accuracy', 'total_questions', 'avg_time_seconds', 'avg_attempts', 'consistency']
        X = training_data[feature_columns]
        
        print(f"\n📊 Feature statistics:")
        print(X.describe())
        
        # --- 1. Enhanced Learner Type Classifier ---
        print("\n🧠 Training Learner Type Classifier...")
        y_learner = self.learner_type_encoder.fit_transform(training_data['learner_type'])
        
        # Use Random Forest with better hyperparameters
        learner_classifier = RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'  # Handle imbalanced classes
        )
        
        # Cross-validation for learner classifier
        cv_scores_learner = cross_val_score(learner_classifier, X, y_learner, cv=5, scoring='accuracy')
        print(f"📈 Learner Classifier CV Accuracy: {cv_scores_learner.mean():.3f} ± {cv_scores_learner.std():.3f}")
        
        # Train final model
        learner_classifier.fit(X, y_learner)
        
        # --- 2. Enhanced Engagement Level Analyzer ---
        print("\n🔥 Training Engagement Level Analyzer...")
        y_engagement = self.engagement_level_encoder.fit_transform(training_data['engagement_level'])
        
        # Use Gradient Boosting for engagement prediction
        engagement_analyzer = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        # Cross-validation for engagement analyzer
        cv_scores_engagement = cross_val_score(engagement_analyzer, X, y_engagement, cv=5, scoring='accuracy')
        print(f"📈 Engagement Analyzer CV Accuracy: {cv_scores_engagement.mean():.3f} ± {cv_scores_engagement.std():.3f}")
        
        # Train final model
        engagement_analyzer.fit(X, y_engagement)
        
        # --- Feature Importance Analysis ---
        print("\n🔍 Feature Importance Analysis:")
        learner_importance = learner_classifier.feature_importances_
        engagement_importance = engagement_analyzer.feature_importances_
        
        print("Learner Type Classifier:")
        for feature, importance in zip(feature_columns, learner_importance):
            print(f"  • {feature}: {importance:.3f}")
            
        print("Engagement Analyzer:")
        for feature, importance in zip(feature_columns, engagement_importance):
            print(f"  • {feature}: {importance:.3f}")
        
        # --- Save Models and Encoders ---
        print("\n💾 Saving models and encoders...")
        joblib.dump(learner_classifier, os.path.join(MODELS_DIR, 'learner_classifier.joblib'))
        joblib.dump(engagement_analyzer, os.path.join(MODELS_DIR, 'engagement_analyzer.joblib'))
        joblib.dump(self.learner_type_encoder, os.path.join(MODELS_DIR, 'learner_type_encoder.joblib'))
        joblib.dump(self.engagement_level_encoder, os.path.join(MODELS_DIR, 'engagement_level_encoder.joblib'))
        
        # --- Final Performance Report ---
        learner_pred = learner_classifier.predict(X)
        engagement_pred = engagement_analyzer.predict(X)
        
        learner_acc = accuracy_score(y_learner, learner_pred)
        engagement_acc = accuracy_score(y_engagement, engagement_pred)
        
        print("\n" + "="*50)
        print("🎉 TRAINING COMPLETE!")
        print("="*50)
        print(f"✅ Learner Classifier Training Accuracy: {learner_acc:.3f}")
        print(f"✅ Learner Classifier CV Accuracy: {cv_scores_learner.mean():.3f}")
        print(f"✅ Engagement Analyzer Training Accuracy: {engagement_acc:.3f}")
        print(f"✅ Engagement Analyzer CV Accuracy: {cv_scores_engagement.mean():.3f}")
        print(f"📁 Models saved to '{MODELS_DIR}/' directory")
        
        # Detailed classification reports
        print(f"\n📊 Learner Type Classification Report:")
        print(classification_report(y_learner, learner_pred, 
                                  target_names=self.learner_type_encoder.classes_))
        
        print(f"\n📊 Engagement Level Classification Report:")
        print(classification_report(y_engagement, engagement_pred, 
                                  target_names=self.engagement_level_encoder.classes_))
        
        return {
            'learner_accuracy': learner_acc,
            'learner_cv_accuracy': cv_scores_learner.mean(),
            'engagement_accuracy': engagement_acc,
            'engagement_cv_accuracy': cv_scores_engagement.mean()
        }

def main():
    """Main function to run the training process."""
    print("🚀 Starting ML Model Training...")
    print("="*50)
    
    try:
        # Load dataset
        print(f"📂 Loading dataset from '{DATASET_PATH}'...")
        quiz_df = pd.read_csv(DATASET_PATH)
        
        # Validate dataset
        required_columns = ['id', 'topic', 'difficulty', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'answer', 'explanation']
        missing_columns = [col for col in required_columns if col not in quiz_df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        print(f"✅ Dataset validation passed!")
        
        # Initialize trainer and train models
        trainer = ModelTrainer(quiz_df)
        results = trainer.train_and_save_models()
        
        print("\n🎯 Training Summary:")
        print(f"  • Dataset size: {len(quiz_df)} questions")
        print(f"  • Synthetic users: {N_SYNTHETIC_USERS}")
        print(f"  • Topics covered: {len(trainer.topics)}")
        print(f"  • Model accuracy: {results['learner_cv_accuracy']:.1%} (Learner), {results['engagement_cv_accuracy']:.1%} (Engagement)")
        
        print(f"\n✅ Training completed successfully!")
        print(f"🚀 You can now run your quiz application!")
        
    except FileNotFoundError:
        print(f"❌ Error: Dataset '{DATASET_PATH}' not found!")
        print("📁 Please ensure your CSV file is in the same directory as this script.")
        print("\n📋 Expected CSV format:")
        print("  - id: unique question identifier")
        print("  - topic: question topic/category") 
        print("  - difficulty: easy/medium/hard")
        print("  - question: the question text")
        print("  - option_a, option_b, option_c, option_d: answer choices")
        print("  - answer: correct answer (a/b/c/d)")
        print("  - explanation: explanation of correct answer")
        
    except Exception as e:
        print(f"❌ An error occurred during training: {e}")
        print("🔧 Please check your dataset format and try again.")
        raise

if __name__ == "__main__":
    main()