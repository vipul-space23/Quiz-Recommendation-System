import streamlit as st
import pandas as pd
from quiz_logic import MLQuizRecommendationSystem
from ui_pages import (
    initialize_session_state, 
    show_setup_page, 
    show_quiz_page, 
    show_results_page, 
    show_analytics_page,
    show_history_view_page,
    show_complete_history_page
)

# --- Page Configuration ---
st.set_page_config(
    page_title="🧠 AI Adaptive Quiz System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for better styling ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #1f77b4;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .quiz-progress {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .sidebar .element-container {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Data and Model Loading ---
@st.cache_resource
def load_system():
    """Loads the quiz data and initializes the recommendation system."""
    try:
        df = pd.read_csv('dataset.csv')
        system = MLQuizRecommendationSystem(df)
        st.success("✅ Quiz system loaded successfully!")
        return system
    except FileNotFoundError:
        st.error("❌ Dataset 'dataset.csv' not found. Please ensure it's in the root directory.")
        st.info("📁 Make sure 'dataset.csv' is in the same folder as this app.")
        return None
    except Exception as e:
        st.error(f"❌ Error loading system: {e}")
        st.info("🔧 This might be because ML models aren't trained. Please run `python train_model.py` first.")
        st.info("💡 The app will work with basic recommendations even without ML models.")
        return None

def get_safe_learning_stats(quiz_history):
    """Get learning stats with proper error handling for the current data structure."""
    if not quiz_history:
        return {}
    
    try:
        # Extract summaries from the nested structure
        summaries = [record['summary'] for record in quiz_history if 'summary' in record]
        
        if not summaries:
            return {}
        
        total_questions = sum(quiz['total'] for quiz in summaries)
        total_correct = sum(quiz['correct'] for quiz in summaries)
        overall_accuracy = total_correct / total_questions if total_questions > 0 else 0
        
        # Topic-wise performance
        topic_stats = {}
        for quiz in summaries:
            topic = quiz['topic']
            if topic not in topic_stats:
                topic_stats[topic] = {'correct': 0, 'total': 0, 'quizzes': 0}
            topic_stats[topic]['correct'] += quiz['correct']
            topic_stats[topic]['total'] += quiz['total']
            topic_stats[topic]['quizzes'] += 1
        
        # Calculate topic accuracies
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
            'topic_stats': topic_stats
        }
    except Exception:
        return {}

def create_sidebar(quiz_system):
    """Creates an enhanced sidebar with navigation and stats."""
    with st.sidebar:
        st.markdown("# 🧠 Navigation")
        st.markdown("---")
        
        # Main navigation buttons
        if st.button("🏠 Home", use_container_width=True, type="primary"):
            st.session_state.stage = "setup"
            st.rerun()
        
        if st.button("📊 Analytics", use_container_width=True, type="secondary"):
            st.session_state.stage = "analytics"
            st.rerun()
            
        if st.button("📜 Full History", use_container_width=True, type="secondary"):
            st.session_state.stage = "complete_history"
            st.rerun()
        
        st.markdown("---")
        
        # Quick stats if user has history
        if st.session_state.quiz_history:
            st.markdown("### 📈 Quick Stats")
            stats = get_safe_learning_stats(st.session_state.quiz_history)
            
            if stats and stats.get('total_quizzes', 0) > 0:
                st.metric("🎓 Quizzes Taken", stats['total_quizzes'])
                st.metric("📊 Overall Accuracy", f"{stats['overall_accuracy']:.1%}")
                st.metric("✅ Questions Answered", stats['total_questions'])
                
                # Show best and worst topics
                if stats.get('topic_stats'):
                    try:
                        best_topic = max(stats['topic_stats'].keys(), 
                                       key=lambda t: stats['topic_stats'][t]['accuracy'])
                        worst_topic = min(stats['topic_stats'].keys(), 
                                        key=lambda t: stats['topic_stats'][t]['accuracy'])
                        
                        st.markdown(f"**🌟 Best Topic:** {best_topic}")
                        st.markdown(f"**🎯 Focus On:** {worst_topic}")
                    except:
                        pass
            else:
                # Simple fallback
                total_quizzes = len(st.session_state.quiz_history)
                st.metric("🎓 Quizzes Taken", total_quizzes)
                if total_quizzes > 0:
                    try:
                        last_quiz = st.session_state.quiz_history[-1]['summary']
                        st.metric("📊 Last Quiz", f"{last_quiz['accuracy']:.1%}")
                        st.metric("📚 Last Topic", last_quiz['topic'])
                    except:
                        st.info("Take a quiz to see stats!")
        
        st.markdown("---")
        
        # Recent quiz history (interactive)
        with st.expander("📋 Recent Quizzes", expanded=len(st.session_state.quiz_history) > 0):
            if not st.session_state.quiz_history:
                st.write("No quizzes yet!")
                st.write("👆 Click 'Home' to start!")
            else:
                # Show last 5 quizzes
                recent_quizzes = st.session_state.quiz_history[-5:]
                
                for i, record in enumerate(reversed(recent_quizzes)):
                    quiz_index = len(st.session_state.quiz_history) - i - 1
                    summary = record['summary']
                    
                    # Create a compact display for each quiz
                    accuracy = summary['accuracy']
                    emoji = "🌟" if accuracy >= 0.8 else "👍" if accuracy >= 0.6 else "📚" if accuracy >= 0.4 else "💪"
                    
                    quiz_label = f"{emoji} {summary['topic'][:10]}... ({accuracy:.0%})"
                    
                    if st.button(
                        quiz_label, 
                        key=f"sidebar_quiz_{quiz_index}",
                        help=f"View details for {summary['topic']} - {summary['difficulty']} quiz",
                        use_container_width=True
                    ):
                        st.session_state.selected_history_index = quiz_index
                        st.session_state.stage = 'history_view'
                        st.rerun()
        
        st.markdown("---")
        
        # System status and controls
        st.markdown("### ⚙️ System")
        
        # Question bank status
        if quiz_system:
            total_questions = len(quiz_system.df)
            seen_questions = len(st.session_state.seen_question_ids)
            remaining = total_questions - seen_questions
            
            progress = seen_questions / total_questions if total_questions > 0 else 0
            st.progress(progress, text=f"Question Bank: {seen_questions}/{total_questions}")
            st.write(f"📝 {remaining} questions remaining")
            
            if seen_questions > 0:
                if st.button("🔄 Reset Progress", help="Reset all question history"):
                    st.session_state.seen_question_ids = set()
                    st.success("✅ Progress reset!")
                    st.rerun()
        
        # App info
        with st.expander("ℹ️ About"):
            st.markdown("""
            **🧠 AI Adaptive Quiz System**
            
            Features:
            - 🤖 AI-powered recommendations
            - 📈 Progress tracking
            - 🎯 Adaptive difficulty
            - 📊 Detailed analytics
            - 🔄 Never repeat questions
            
            Built with Streamlit & ML
            """)

def main():
    """Main function to run the Streamlit app."""
    # Initialize session state first
    initialize_session_state()
    
    # Show loading screen on first run
    if 'system_loaded' not in st.session_state:
        st.markdown("<h1 class='main-header'>🧠 AI Adaptive Quiz System</h1>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("### 🚀 Initializing System...")
            with st.spinner("Loading quiz system..."):
                # Load the quiz system
                quiz_system = load_system()
                
                if quiz_system is None:
                    st.stop()
            
            st.success("✅ System loaded successfully!")
            st.session_state.system_loaded = True
            st.rerun()
        return
    
    # Load the quiz system (already loaded during initialization)
    quiz_system = load_system()
    
    if quiz_system is None:
        st.stop()
    
    # Create sidebar
    create_sidebar(quiz_system)
    
    # Main content area
    try:
        # Page routing with error handling
        if st.session_state.stage == 'setup':
            show_setup_page(quiz_system)
        
        elif st.session_state.stage == 'quiz':
            show_quiz_page()
        
        elif st.session_state.stage == 'results':
            show_results_page(quiz_system)
        
        elif st.session_state.stage == 'analytics':
            show_analytics_page(quiz_system)
        
        elif st.session_state.stage == 'history_view':
            if (st.session_state.selected_history_index is not None and 
                0 <= st.session_state.selected_history_index < len(st.session_state.quiz_history)):
                record_to_view = st.session_state.quiz_history[st.session_state.selected_history_index]
                show_history_view_page(record_to_view)
            else:
                st.error("❌ Invalid quiz selection. Returning to home.")
                st.session_state.stage = 'setup'
                st.rerun()
        
        elif st.session_state.stage == 'complete_history':
            show_complete_history_page()
        
        else:
            st.error("❌ Unknown page. Returning to home.")
            st.session_state.stage = 'setup'
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
        st.error("🔄 Please refresh the page or return to home.")
        if st.button("🏠 Return to Home"):
            st.session_state.stage = 'setup'
            st.rerun()

if __name__ == "__main__":
    main()