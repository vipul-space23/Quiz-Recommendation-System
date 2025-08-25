# 🧠 AI-Powered Adaptive Quiz System

![Quiz App Demo](https://placehold.co/800x400/1f77b4/ffffff?text=AI+Quiz+App+Screenshot)

An intelligent, adaptive quiz application built with Python and Streamlit that provides a personalized learning path for users. The system uses machine learning to analyze user performance, recommend suitable quizzes, and ensure a unique and effective learning experience by never repeating questions. The entire application is containerized with Docker for easy setup and deployment.

---

## ✨ Core Features

-   **🤖 Smart Recommendations:** The system analyzes your quiz history to recommend the most suitable next quiz, dynamically adjusting the topic, difficulty, and number of questions based on your performance.
-   **🔄 No-Repeat Questions:** Guarantees that a user will not see the same question twice until the entire question pool for a category has been exhausted.
-   **📊 Detailed Analytics:** A comprehensive dashboard to track your progress, view overall accuracy, and see performance breakdowns by topic and difficulty.
-   **📜 Interactive History:** Users can view their complete quiz history and click on any past quiz to review the exact questions, their answers, and the correct solutions.
-   **🐳 Dockerized for Portability:** The entire application is containerized with Docker, allowing anyone to run it with just two commands, without worrying about installing Python or any dependencies.
-   **👤 AI Learner Profiling:** A pre-trained ML model provides insights into your learning style (e.g., 'Advanced', 'Struggling') for a more personalized experience.

---

## 🛠️ Tech Stack

-   **Backend:** Python
-   **Web Framework:** Streamlit
-   **Data Manipulation:** Pandas, NumPy
-   **Machine Learning:** Scikit-learn
-   **Containerization:** Docker

---

## 📂 Project Structure

The project is organized into a modular structure for clarity and maintainability:


/Quiz-Recommendation-System/
|
|-- models/               # Stores the pre-trained ML model files (.joblib)
|-- app.py                # Main Streamlit application entry point
|-- quiz_logic.py         # Core recommendation and ML logic class
|-- ui_pages.py           # Functions for rendering each Streamlit page
|-- train_model.py        # Standalone script to pre-train the ML models
|-- dataset.csv           # The quiz questions dataset
|-- requirements.txt      # Python dependencies
|-- Dockerfile            # Instructions for building the Docker image
|-- .dockerignore         # Specifies files to ignore in the Docker build
|-- README.md             # This file


---

## 🚀 Getting Started

You can run this application in two ways: using Docker (recommended for ease of use) or setting it up locally for development.

### Method 1: Running with Docker (Recommended)

This is the simplest way to run the application.

**Prerequisites:**
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

**Instructions:**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/vipul-space23/Quiz-Recommendation-System.git](https://github.com/vipul-space23/Quiz-Recommendation-System.git)
    cd Quiz-Recommendation-System
    ```

2.  **Build the Docker image:** This command will install all dependencies and train the AI models inside the container. This step can take a few minutes on the first run.
    ```bash
    docker build -t quiz-app .
    ```

3.  **Run the Docker container:**
    ```bash
    docker run -p 8501:8501 quiz-app
    ```

4.  **Open the app:** Open your web browser and navigate to `http://localhost:8501`.

### Method 2: Local Development Setup (Without Docker)

Use this method if you want to modify the code.

**Prerequisites:**
-   Python 3.9+
-   A virtual environment tool (like `venv`)

**Instructions:**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/vipul-space23/Quiz-Recommendation-System.git](https://github.com/vipul-space23/Quiz-Recommendation-System.git)
    cd Quiz-Recommendation-System
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Train the AI Models (One-Time Step):** Before running the app for the first time, you must train the models.
    ```bash
    python train_model.py
    ```
    This will create the `models/` directory and save the trained model files.

5.  **Run the Streamlit App:**
    ```bash
    streamlit run app.py
    ```

6.  **Open the app:** Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).

---

## ⚙️ How the Recommendation Engine Works

The core of the application is the adaptive recommendation logic found in `quiz_logic.py`. It follows a rule-based system based on the user's performance in their most recent quiz:

1.  **Low Score (<40%):** The system identifies the user is struggling. It recommends an **easy** quiz on the **same topic** with **fewer questions** to help build confidence. If the user is on a struggling streak, the quiz size is reduced even further.
2.  **Moderate Score (40%-70%):** The user is making steady progress. The system recommends a **medium** difficulty quiz and **increases the number of questions** to solidify their knowledge.
3.  **High Score (>70%):** The user is proficient. The system **increases the difficulty level** (from easy to medium, or medium to hard) and **increases the number of questions**. If the user masters a `hard` quiz, the system recommends a **new, related topic** to broaden their horizons.
