# 🧠 AI-Powered Adaptive Quiz System

A comprehensive, intelligent quiz platform that adapts to individual learning patterns and **never repeats questions**.

---

## ✨ Key Features

### 🎯 Smart Recommendation Engine

* **Adaptive Difficulty**: Automatically adjusts based on performance
* **Progressive Learning**: Increases question count as skills improve
* **Never Repeats**: Tracks all attempted questions to ensure unique experiences
* **Multiple Scenarios**: Handles struggling, moderate, and advanced learners

### 📊 Comprehensive Analytics

* **Real-time Progress Tracking**: Monitor improvement over time
* **Topic-wise Performance**: Identify strengths and weaknesses
* **AI-powered Insights**: ML models analyze learning patterns
* **Detailed Question Review**: Learn from mistakes with explanations

### 🤖 AI-Powered Features

* **Learner Type Classification**: Advanced, Moderate, Struggling, Balanced
* **Engagement Analysis**: High, Medium, Low engagement levels
* **Pattern Recognition**: Identifies learning trends and consistency
* **Personalized Recommendations**: Suggests optimal next steps

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
pip install streamlit pandas numpy scikit-learn plotly joblib
```

### 2. Prepare Your Dataset

Create a **dataset.csv** file with the following columns:

```csv
id, topic, difficulty, question, option_a, option_b, option_c, option_d, answer, explanation
```

### 3. Train ML Models (Optional)

```bash
python train_model.py
```

This creates AI models for personalized recommendations and analytics.

### 4. Launch the Application

```bash
streamlit run app.py
```

---

## 📋 File Structure

```plaintext
quiz-system/
├── app.py               # Main Streamlit application
├── quiz_logic.py        # Core recommendation engine
├── ui_pages.py          # User interface components
├── train_model.py       # ML model training script
├── dataset.csv          # Your question database
├── models/              # Trained ML models (auto-generated)
│   ├── learner_classifier.joblib
│   ├── engagement_analyzer.joblib
│   └── ...encoders.joblib
└── README.md            # This file
```

---

## 🎯 Learning Scenarios

### 📚 Struggling Learners (< 40% accuracy)

* Reduces question count (5 → 3 → 2)
* Stays on **easy difficulty** until confidence builds
* Switches to best-performing topic for confidence
* Provides encouraging messages

### 📈 Moderate Performers (40–70% accuracy)

* Progressive question increase (5 → 10 → 15 → 20)
* Advances to **medium difficulty** from easy
* Keeps engagement with appropriate challenges
* Builds systematically towards advanced

### 🌟 Advanced Learners (≥ 70% accuracy)

* Increases question count for comprehensive practice
* Progresses through **easy → medium → hard**
* Suggests related topics after mastery
* Provides advanced challenges

### 🔄 Special Situations

* **Question Exhaustion**: Finds alternative topics/difficulties
* **Inconsistent Performance**: Adapts dynamically
* **Topic Mastery**: Suggests related/new topics
* **Confidence Building**: Returns to stronger topics when struggling

---

## 📊 Analytics Dashboard

### Performance Metrics

* Overall accuracy and progress trends
* Topic-wise performance breakdown
* Difficulty level mastery
* Question completion statistics

### AI Insights

* Learner Type: Advanced, Moderate, Struggling, Balanced
* Engagement Level: High, Medium, Low
* Learning Pattern: Improving, Stable, Declining
* Consistency Score

### Progress Tracking

* Interactive charts showing improvement over time
* Heatmaps of available questions by topic/difficulty
* Question-by-question review
* Personalized recommendations

---

## 🛠️ Customization Options

### Adding New Topics

* Add questions with new topics in `dataset.csv`
* Update topic relationships in `quiz_logic.py`
* Retrain models: `python train_model.py`

### Adjusting Difficulty Progression

Modify in `quiz_logic.py`:

```python
STRUGGLING_THRESHOLD = 0.4
CRITICAL_STRUGGLE_THRESHOLD = 0.2

MIN_QUESTIONS = 3
MAX_QUESTIONS = 20
INCREMENT_SIZE = 5

MODERATE_THRESHOLD = 0.7
ADVANCED_THRESHOLD = 0.8
```

### Enhancing AI Models

* Increase synthetic user count in `train_model.py`
* Add new features for analysis
* Experiment with different ML algorithms

---

## 🎨 User Interface Features

### Home Page

* AI-powered quiz recommendations
* Quick performance stats
* Custom quiz setup
* Question bank status

### Quiz Interface

* Progress tracking indicators
* Question navigation
* Immediate feedback
* Clean, distraction-free design

### Results Page

* Detailed performance analysis
* Question review with explanations
* AI insights and recommendations

### Analytics Dashboard

* Interactive charts and breakdowns
* Learning pattern analysis
* Question bank management

### Complete History

* Access all previous quizzes
* Review past attempts
* Performance trend visualization

---

## 🔧 Advanced Configuration

### Recommendation Tuning

Adjust thresholds in `quiz_logic.py`.

### UI Customization

Edit `app.py`:

```python
st.markdown("""
<style>
.main-header {
  color: #your-color;
}
</style>
""", unsafe_allow_html=True)
```

---

## 📈 Performance Optimization

### For Large Question Banks

* Enable DB indexing
* Implement caching
* Use pagination for quiz history

### For Many Users

* Use database backend instead of session state
* Add authentication and persistence
* Handle concurrent users

---

## 🚀 Deployment Options

### Local Development

```bash
streamlit run app.py
```

### Cloud Deployment

* **Streamlit Cloud**: Direct GitHub integration
* **Heroku**: Simple hosting
* **AWS/GCP/Azure**: Scalable solutions

### Docker Deployment

```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
```

---

## 📜 License

MIT License – feel free to use, modify, and distribute.

---

## 💡 Contributing

Pull requests are welcome! For major changes, open an issue first to discuss.

---

## 🙌 Acknowledgements

* [Streamlit](https://streamlit.io/)
* [Scikit-learn](https://scikit-learn.org/)
* [Plotly](https://plotly.com/)
* OpenAI / GPT-based inspiration for adaptive learning
