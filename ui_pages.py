import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from quiz_logic import MLQuizRecommendationSystem
from typing import Dict
import numpy as np

def initialize_session_state():
    """Initializes all required session state variables."""
    defaults = {
        'stage': 'setup',
        'quiz_questions': pd.DataFrame(),
        'current_question': 0,
        'user_answers': [],
        'quiz_history': [],
        'seen_question_ids': set(),
        'selected_history_index': None,
        'show_detailed_history': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_setup_page(quiz_system: MLQuizRecommendationSystem):
    """Enhanced setup page with smart recommendations and availability checks."""
    st.title("🧠 AI-Powered Adaptive Quiz System")
    st.markdown("### 🎯 Personalized learning that adapts to your progress!")
    
    # Show learning statistics if user has history
    if st.session_state.quiz_history:
        stats = quiz_system.get_learning_stats(st.session_state.quiz_history)
        
        with st.container(border=True):
            st.subheader("📊 Your Learning Journey")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🎓 Quizzes Taken", stats['total_quizzes'])
            col2.metric("❓ Questions Answered", stats['total_questions'])
            col3.metric("📈 Overall Accuracy", f"{stats['overall_accuracy']:.1%}")
            col4.metric("🏆 Best Topic", max(stats['topic_stats'].keys(), key=lambda t: stats['topic_stats'][t]['accuracy']) if stats['topic_stats'] else "None")
    
    # AI Recommendation Section
    st.markdown("---")
    recommendation = quiz_system.recommend_next_quiz(st.session_state.quiz_history)
    
    with st.container(border=True):
        st.subheader("🤖 Your Personalized Recommendation")
        
        # Check if recommended questions are available
        available_count = quiz_system.get_available_questions_count(
            recommendation['topic'], 
            recommendation['difficulty'], 
            st.session_state.seen_question_ids
        )
        
        if available_count == 0:
            st.warning(f"⚠️ No new {recommendation['difficulty']} questions available for {recommendation['topic']}!")
            # Try to find alternative
            alternative_found = False
            for alt_difficulty in ['easy', 'medium', 'hard']:
                alt_count = quiz_system.get_available_questions_count(
                    recommendation['topic'], alt_difficulty, st.session_state.seen_question_ids
                )
                if alt_count > 0:
                    recommendation['difficulty'] = alt_difficulty
                    recommendation['num_questions'] = min(recommendation['num_questions'], alt_count)
                    recommendation['message'] = f"🔄 Adjusted to {alt_difficulty} level for {recommendation['topic']} (available questions)"
                    available_count = alt_count
                    alternative_found = True
                    break
            
            if not alternative_found:
                # Try different topic
                for alt_topic in quiz_system.topics:
                    for alt_difficulty in ['easy', 'medium', 'hard']:
                        alt_count = quiz_system.get_available_questions_count(
                            alt_topic, alt_difficulty, st.session_state.seen_question_ids
                        )
                        if alt_count >= 5:
                            recommendation = {
                                'topic': alt_topic,
                                'difficulty': alt_difficulty,
                                'num_questions': min(10, alt_count),
                                'message': f"🌟 Let's try {alt_topic} to keep your learning going!",
                                'reason': 'availability_fallback'
                            }
                            available_count = alt_count
                            alternative_found = True
                            break
                    if alternative_found:
                        break
        
        if available_count > 0:
            st.info(f"**🎯 AI Recommendation:** {recommendation['message']}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📚 Topic", recommendation['topic'])
            col2.metric("📊 Level", recommendation['difficulty'].title())
            col3.metric("❓ Questions", f"{recommendation['num_questions']}")
            col4.metric("✅ Available", f"{available_count}")
            
            # Adjust num_questions if more than available
            if recommendation['num_questions'] > available_count:
                recommendation['num_questions'] = available_count
                st.info(f"📝 Adjusted to {available_count} questions (all available for this level)")
            
            if st.button("🚀 Start Recommended Quiz", type="primary", use_container_width=True):
                start_recommended_quiz(quiz_system, recommendation)
        else:
            st.error("😅 You've completed all available questions! Time to reset or add more content.")
            if st.button("🔄 Reset Question History", help="This will allow you to retake all questions"):
                st.session_state.seen_question_ids = set()
                st.rerun()

    # Manual Quiz Setup
    st.markdown("---")
    st.subheader("🛠️ Custom Quiz Setup")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_topic = st.selectbox("🎯 Topic:", options=quiz_system.topics)
    with col2:
        selected_difficulty = st.selectbox("📊 Difficulty:", options=quiz_system.difficulties, index=1)
    with col3:
        max_available = quiz_system.get_available_questions_count(
            selected_topic, selected_difficulty, st.session_state.seen_question_ids
        )
        if max_available > 0:
            num_questions = st.slider(
                "❓ Questions:", 
                min_value=1, 
                max_value=min(20, max_available), 
                value=min(10, max_available)
            )
            st.info(f"✅ {max_available} questions available")
        else:
            st.error(f"❌ No questions available for {selected_topic} - {selected_difficulty}")
            num_questions = 0
    
    if max_available > 0:
        if st.button("📝 Start Custom Quiz", use_container_width=True):
            questions = quiz_system.get_questions(
                selected_topic, selected_difficulty, num_questions, st.session_state.seen_question_ids
            )
            start_quiz(questions, selected_topic, selected_difficulty)
    
    # Quick Stats
    if st.session_state.quiz_history:
        with st.expander("📈 Quick Performance Overview"):
            # --- FIX: Access the 'summary' dictionary ---
            recent_quizzes = [rec['summary'] for rec in st.session_state.quiz_history[-5:]]
            scores = [f"{q['correct']}/{q['total']} ({q['accuracy']:.0%})" for q in recent_quizzes]
            topics = [q['topic'] for q in recent_quizzes]
            st.write("**Recent Performance:**")
            for i, (score, topic) in enumerate(zip(scores, topics)):
                st.write(f"  {len(recent_quizzes)-i}. {topic}: {score}")

def start_recommended_quiz(quiz_system: MLQuizRecommendationSystem, recommendation: Dict):
    """Start a quiz based on AI recommendation."""
    questions = quiz_system.get_questions(
        recommendation['topic'], 
        recommendation['difficulty'], 
        recommendation['num_questions'], 
        st.session_state.seen_question_ids
    )
    
    if questions.empty:
        st.error("❌ Unable to generate quiz. Please try different settings.")
        return
    
    start_quiz(questions, recommendation['topic'], recommendation['difficulty'])

def start_quiz(questions: pd.DataFrame, topic: str, difficulty: str):
    """Initialize quiz session."""
    if questions.empty:
        st.error("❌ No questions available for the selected criteria.")
        return
    
    st.session_state.quiz_questions = questions
    st.session_state.current_question = 0
    st.session_state.user_answers = [None] * len(questions)
    st.session_state.selected_topic = topic
    st.session_state.selected_difficulty = difficulty
    st.session_state.stage = 'quiz'
    st.rerun()

def show_quiz_page():
    """Enhanced quiz page with better navigation and progress tracking."""
    questions = st.session_state.quiz_questions
    idx = st.session_state.current_question
    total = len(questions)
    
    if idx >= total:
        st.session_state.stage = 'results'
        st.rerun()
    
    current_q = questions.iloc[idx]
    
    # Header with progress
    st.title(f"📚 {st.session_state.selected_topic} Quiz")
    st.subheader(f"🎯 Level: {st.session_state.selected_difficulty.title()}")
    
    # Progress bar with detailed info
    progress = (idx + 1) / total
    st.progress(progress, text=f"Question {idx + 1} of {total} ({progress:.0%} complete)")
    
    # Show how many questions answered
    answered_count = sum(1 for ans in st.session_state.user_answers[:idx+1] if ans is not None)
    st.info(f"📝 Answered: {answered_count}/{idx+1} questions so far")
    
    # Question display
    with st.container(border=True):
        st.markdown(f"### ❓ Question {idx + 1}")
        st.markdown(f"**{current_q['question']}**")
        
        # Options
        options = [current_q[f'option_{c}'] for c in ['a', 'b', 'c', 'd']]
        option_labels = [f"**{chr(65+i)}.** {opt}" for i, opt in enumerate(options)]
        
        # Get current answer if already selected
        current_answer = st.session_state.user_answers[idx]
        current_index = None if current_answer is None else ord(current_answer) - ord('a')
        
        user_choice_index = st.radio(
            "Select your answer:",
            range(len(options)),
            index=current_index,
            format_func=lambda x: option_labels[x],
            key=f"question_{idx}"
        )
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⏮️ Previous", disabled=(idx == 0), use_container_width=True):
            st.session_state.current_question -= 1
            st.rerun()
    
    with col2:
        # Show quiz overview
        if st.button("📋 Quiz Overview", use_container_width=True):
            show_quiz_overview()
    
    with col3:
        next_label = "Next ⏭️" if idx < total - 1 else "Finish Quiz 🏁"
        if st.button(next_label, type="primary", use_container_width=True):
            # Save the current answer
            selected_letter = chr(ord('a') + user_choice_index)
            st.session_state.user_answers[idx] = selected_letter
            st.session_state.current_question += 1
            st.rerun()

def show_quiz_overview():
    """Show a popup-style overview of quiz progress."""
    with st.expander("📋 Quiz Progress Overview", expanded=True):
        questions = st.session_state.quiz_questions
        answers = st.session_state.user_answers
        
        for i, (_, question) in enumerate(questions.iterrows()):
            status = "✅" if answers[i] is not None else "⏸️"
            answer_text = f"({answers[i].upper()})" if answers[i] else "(Not answered)"
            st.write(f"{status} **Q{i+1}:** {question['question'][:50]}... {answer_text}")
        
        answered = sum(1 for ans in answers if ans is not None)
        st.metric("Progress", f"{answered}/{len(questions)} questions answered")

def show_results_page(quiz_system: MLQuizRecommendationSystem):
    """Enhanced results page with detailed analysis."""
    questions = st.session_state.quiz_questions
    user_answers = st.session_state.user_answers
    correct_answers = questions['answer'].tolist()
    
    correct_count = sum(1 for ua, ca in zip(user_answers, correct_answers) if ua == ca)
    total = len(questions)
    accuracy = correct_count / total if total > 0 else 0
    
    # Save to history
    performance_summary = {
        'topic': st.session_state.selected_topic,
        'difficulty': st.session_state.selected_difficulty,
        'correct': correct_count,
        'total': total,
        'accuracy': accuracy,
        'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    full_quiz_record = {
        'summary': performance_summary,
        'questions_df': questions.copy(),
        'user_answers_list': user_answers.copy()
    }
    
    st.session_state.quiz_history.append(full_quiz_record)
    
    # Update seen questions
    question_ids = set(questions['question_id'])
    st.session_state.seen_question_ids.update(question_ids)
    
    # Results display
    st.title("🎉 Quiz Results")
    
    # Performance summary
    if accuracy >= 0.8:
        st.balloons()
        performance_color = "green"
        performance_emoji = "🌟"
        performance_msg = "Outstanding!"
    elif accuracy >= 0.6:
        performance_color = "blue" 
        performance_emoji = "👍"
        performance_msg = "Good job!"
    elif accuracy >= 0.4:
        performance_color = "orange"
        performance_emoji = "📚"
        performance_msg = "Keep practicing!"
    else:
        performance_color = "red"
        performance_emoji = "💪"
        performance_msg = "Don't give up!"
    
    st.markdown(f"## {performance_emoji} {performance_msg}")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Correct", correct_count)
    col2.metric("❌ Incorrect", total - correct_count)
    col3.metric("📊 Accuracy", f"{accuracy:.1%}")
    col4.metric("📝 Total Questions", total)
    
    # Get next recommendation
    next_rec = quiz_system.recommend_next_quiz(st.session_state.quiz_history)
    
    with st.container(border=True):
        st.subheader("🤖 What's Next?")
        st.info(f"**AI Recommendation:** {next_rec['message']}")
        
        col_a, col_b, col_c = st.columns(3)
        if col_a.button("🚀 Take Recommended Quiz", type="primary", use_container_width=True):
            st.session_state.stage = 'setup'
            st.rerun()
        if col_b.button("🏠 Choose Different Quiz", use_container_width=True):
            st.session_state.stage = 'setup'
            st.rerun()
        if col_c.button("📊 View Full Analytics", use_container_width=True):
            st.session_state.stage = 'analytics'
            st.rerun()
    
    # Detailed tabs
    tab1, tab2, tab3 = st.tabs(["📋 Question Review", "🤖 AI Analysis", "📈 Performance Trends"])
    
    with tab1:
        st.header("Question-by-Question Review")
        for i, row in questions.iterrows():
            user_ans = user_answers[i]
            correct_ans = row['answer']
            is_correct = user_ans == correct_ans
            
            with st.container(border=True):
                # Color coding
                if is_correct:
                    st.success(f"✅ **Question {i+1}** - Correct!")
                else:
                    st.error(f"❌ **Question {i+1}** - Incorrect")
                
                st.write(f"**{row['question']}**")
                
                # Show all options with indicators
                for opt_letter, opt_text in zip(['a', 'b', 'c', 'd'], [row[f'option_{c}'] for c in ['a', 'b', 'c', 'd']]):
                    if opt_letter == correct_ans:
                        st.write(f"✅ **{opt_letter.upper()}.** {opt_text} *(Correct Answer)*")
                    elif opt_letter == user_ans:
                        st.write(f"❌ **{opt_letter.upper()}.** {opt_text} *(Your Answer)*")
                    else:
                        st.write(f"   {opt_letter.upper()}. {opt_text}")
                
                if not is_correct:
                    st.info(f"💡 **Explanation:** {row['explanation']}")
    
    with tab2:
        st.header("AI Performance Analysis")
        ai_predictions = quiz_system.get_ai_predictions(st.session_state.quiz_history)
        
        if ai_predictions:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🧠 Learner Type", ai_predictions.get('learner_type', 'N/A'))
                if 'learner_probs' in ai_predictions:
                    st.write("**Learner Type Probabilities:**")
                    for lt, prob in ai_predictions['learner_probs'].items():
                        st.write(f"  • {lt}: {prob:.1%}")
            
            with col2:
                st.metric("🔥 Engagement Level", ai_predictions.get('engagement_level', 'N/A'))
                if 'engagement_probs' in ai_predictions:
                    st.write("**Engagement Probabilities:**")
                    for el, prob in ai_predictions['engagement_probs'].items():
                        st.write(f"  • {el}: {prob:.1%}")
        else:
            st.info("🤖 Take more quizzes for detailed AI analysis!")
        
        # Learning pattern analysis
        learning_analysis = quiz_system.analyze_learning_pattern(st.session_state.quiz_history)
        st.subheader("📊 Learning Pattern Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📈 Learning Pattern", learning_analysis['pattern'].title())
            st.metric("🎯 Trend", learning_analysis['trend'].title())
        
        with col2:
            st.metric("📊 Recent Average", f"{learning_analysis['recent_avg']:.1%}")
            st.metric("🎯 Consistency", f"{learning_analysis['consistency']:.1%}")
        
        if learning_analysis['struggling_topics']:
            st.warning(f"🎯 **Focus Areas:** {', '.join(learning_analysis['struggling_topics'])}")
    
    with tab3:
        st.header("Performance Trends")
        if len(st.session_state.quiz_history) >= 2:
            # Create trend chart
            history_df = pd.DataFrame([record['summary'] for record in st.session_state.quiz_history])
            history_df['quiz_number'] = range(1, len(history_df) + 1)
            history_df['accuracy_pct'] = history_df['accuracy'] * 100
            
            fig = px.line(
                history_df, 
                x='quiz_number', 
                y='accuracy_pct',
                title='📈 Your Accuracy Progression',
                markers=True,
                labels={'quiz_number': 'Quiz Number', 'accuracy_pct': 'Accuracy (%)'}
            )
            fig.add_hline(y=70, line_dash="dash", line_color="green", 
                         annotation_text="Good Performance (70%)")
            fig.add_hline(y=40, line_dash="dash", line_color="red", 
                         annotation_text="Needs Improvement (40%)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent performance
            recent_5 = history_df.tail(5)
            avg_recent = recent_5['accuracy_pct'].mean()
            st.metric("📊 Last 5 Quizzes Average", f"{avg_recent:.1%}")
        else:
            st.info("📊 Take more quizzes to see your progress trends!")

def show_history_view_page(quiz_record: Dict):
    """Enhanced detailed view of a single quiz from history."""
    summary = quiz_record['summary']
    questions = quiz_record['questions_df']
    user_answers = quiz_record['user_answers_list']
    
    st.title(f"📋 Quiz Review: {summary['topic']}")
    st.subheader(f"🎯 {summary['difficulty'].title()} Level | 📅 {summary.get('timestamp', 'N/A')}")
    
    # Performance summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Correct", summary['correct'])
    col2.metric("❌ Incorrect", summary['total'] - summary['correct'])
    col3.metric("📊 Score", f"{summary['correct']}/{summary['total']}")
    col4.metric("📈 Accuracy", f"{summary['accuracy']:.1%}")
    
    if st.button("⬅️ Back to Home", type="primary"):
        st.session_state.stage = 'setup'
        st.rerun()
    
    st.divider()
    
    # Question review
    st.header("📝 Detailed Question Review")
    
    correct_questions = []
    incorrect_questions = []
    
    for i, row in questions.iterrows():
        user_ans = user_answers[i]
        correct_ans = row['answer']
        is_correct = user_ans == correct_ans
        
        if is_correct:
            correct_questions.append((i, row, user_ans, correct_ans))
        else:
            incorrect_questions.append((i, row, user_ans, correct_ans))
    
    # Show incorrect questions first (more important for learning)
    if incorrect_questions:
        st.subheader("❌ Questions to Review")
        for i, row, user_ans, correct_ans in incorrect_questions:
            with st.container(border=True):
                st.error(f"**Question {i+1}** - Incorrect")
                st.write(f"**{row['question']}**")
                st.write(f"🔴 **Your answer:** {user_ans.upper()} - {row[f'option_{user_ans}']}")
                st.write(f"✅ **Correct answer:** {correct_ans.upper()} - {row[f'option_{correct_ans}']}")
                st.info(f"💡 **Explanation:** {row['explanation']}")
    
    if correct_questions:
        with st.expander(f"✅ Correct Answers ({len(correct_questions)} questions)", expanded=False):
            for i, row, user_ans, correct_ans in correct_questions:
                st.success(f"**Question {i+1}:** {row['question'][:60]}... ✓")

def show_analytics_page(quiz_system: MLQuizRecommendationSystem):
    """Comprehensive analytics dashboard."""
    st.title("📊 Learning Analytics Dashboard")
    
    history_records = st.session_state.quiz_history
    if not history_records:
        st.info("📈 Take some quizzes to see your detailed analytics here!")
        if st.button("🏠 Start Learning", type="primary"):
            st.session_state.stage = 'setup'
            st.rerun()
        return
    
    # Get comprehensive stats
    stats = quiz_system.get_learning_stats(history_records)
    
    # Overall performance metrics
    st.header("🎯 Overall Performance")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎓 Total Quizzes", stats['total_quizzes'])
    col2.metric("❓ Total Questions", stats['total_questions'])
    col3.metric("✅ Total Correct", stats['total_correct'])
    col4.metric("📈 Overall Accuracy", f"{stats['overall_accuracy']:.1%}")
    
    # Performance trends
    st.header("📈 Progress Over Time")
    history_df = pd.DataFrame([record['summary'] for record in history_records])
    history_df['quiz_number'] = range(1, len(history_df) + 1)
    history_df['accuracy_pct'] = history_df['accuracy'] * 100
    
    # Main trend line
    fig_trend = px.line(
        history_df, x='quiz_number', y='accuracy_pct',
        title="📊 Accuracy Progression", markers=True,
        labels={'quiz_number': 'Quiz Number', 'accuracy_pct': 'Accuracy (%)'}
    )
    
    # Add performance thresholds
    fig_trend.add_hline(y=80, line_dash="dot", line_color="green", 
                       annotation_text="Excellent (80%)")
    fig_trend.add_hline(y=60, line_dash="dot", line_color="blue", 
                       annotation_text="Good (60%)")
    fig_trend.add_hline(y=40, line_dash="dot", line_color="orange", 
                       annotation_text="Needs Work (40%)")
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Topic and difficulty analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Performance by Topic")
        topic_data = []
        for topic, data in stats['topic_stats'].items():
            topic_data.append({
                'topic': topic,
                'accuracy': data['accuracy'] * 100,
                'quizzes': data['quizzes'],
                'questions': data['total']
            })
        
        topic_df = pd.DataFrame(topic_data)
        fig_topic = px.bar(
            topic_df, x='topic', y='accuracy',
            title="Average Accuracy by Topic",
            labels={'accuracy': 'Accuracy (%)', 'topic': 'Topic'},
            color='accuracy',
            color_continuous_scale='RdYlGn'
        )
        fig_topic.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_topic, use_container_width=True)
        
        # Topic details
        st.write("**Detailed Topic Statistics:**")
        for topic, data in stats['topic_stats'].items():
            accuracy = data['accuracy']
            color = "🟢" if accuracy >= 0.7 else "🟡" if accuracy >= 0.4 else "🔴"
            st.write(f"{color} **{topic}**: {accuracy:.1%} ({data['correct']}/{data['total']}) in {data['quizzes']} quiz{'s' if data['quizzes'] != 1 else ''}")
    
    with col2:
        st.subheader("🎯 Performance by Difficulty")
        diff_data = history_df.groupby('difficulty').agg({
            'accuracy_pct': 'mean',
            'total': 'sum'
        }).reset_index()
        diff_data = diff_data.reindex([0,1,2] if len(diff_data) == 3 else range(len(diff_data)))  # Order: easy, medium, hard
        
        fig_diff = px.bar(
            diff_data, x='difficulty', y='accuracy_pct',
            title="Average Accuracy by Difficulty",
            labels={'accuracy_pct': 'Accuracy (%)', 'difficulty': 'Difficulty'},
            color='accuracy_pct',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_diff, use_container_width=True)
        
        # Difficulty progression
        st.write("**Difficulty Progression:**")
        for _, row in diff_data.iterrows():
            difficulty = row['difficulty']
            accuracy = row['accuracy_pct'] / 100
            color = "🟢" if accuracy >= 0.7 else "🟡" if accuracy >= 0.4 else "🔴"
            st.write(f"{color} **{difficulty.title()}**: {accuracy:.1%} average")
    
    # Learning insights
    st.header("🧠 Learning Insights")
    learning_analysis = stats['learning_analysis']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Learning Pattern", learning_analysis['pattern'].title())
    with col2:
        st.metric("📈 Recent Trend", learning_analysis['trend'].title())
    with col3:
        st.metric("🎯 Consistency", f"{learning_analysis['consistency']:.1%}")
    
    # Recommendations and insights
    if learning_analysis['struggling_topics']:
        st.warning(f"🎯 **Topics needing attention:** {', '.join(learning_analysis['struggling_topics'])}")
        st.info("💡 **Tip:** Focus on easier questions in these topics to build confidence!")
    
    if learning_analysis['trend'] == 'improving':
        st.success("🚀 **Great progress!** You're showing consistent improvement!")
    elif learning_analysis['trend'] == 'declining':
        st.warning("📚 **Consider reviewing fundamentals** - take some easier quizzes to rebuild confidence.")
    
    # Question availability status
    st.header("📋 Available Questions")
    availability_data = []
    total_seen = len(st.session_state.seen_question_ids)
    total_available = len(quiz_system.df)
    
    for topic in quiz_system.topics:
        for difficulty in quiz_system.difficulties:
            available = quiz_system.get_available_questions_count(topic, difficulty, st.session_state.seen_question_ids)
            total_for_combo = len(quiz_system.df[(quiz_system.df['topic'] == topic) & (quiz_system.df['difficulty'] == difficulty)])
            availability_data.append({
                'topic': topic,
                'difficulty': difficulty,
                'available': available,
                'total': total_for_combo,
                'percentage': (available / total_for_combo * 100) if total_for_combo > 0 else 0
            })
    
    availability_df = pd.DataFrame(availability_data)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📝 Questions Completed", f"{total_seen}/{total_available}")
        st.metric("📊 Completion Rate", f"{total_seen/total_available:.1%}")
    
    with col2:
        if st.button("🔄 Reset Question History"):
            st.session_state.seen_question_ids = set()
            st.success("✅ Question history reset! You can now retake all questions.")
            st.rerun()
    
    # Show availability heatmap
    pivot_availability = availability_df.pivot(index='topic', columns='difficulty', values='available')
    fig_heatmap = px.imshow(
        pivot_availability,
        title="📊 Available Questions Heatmap",
        labels=dict(x="Difficulty", y="Topic", color="Available Questions"),
        aspect="auto",
        color_continuous_scale="RdYlGn"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    if st.button("🏠 Back to Home", type="primary"):
        st.session_state.stage = 'setup'
        st.rerun()

def show_complete_history_page():
    """Show complete detailed history of all quizzes."""
    st.title("📜 Complete Quiz History")
    
    if not st.session_state.quiz_history:
        st.info("No quizzes taken yet!")
        if st.button("🏠 Start Learning"):
            st.session_state.stage = 'setup'
            st.rerun()
        return
    
    if st.button("🏠 Back to Home"):
        st.session_state.stage = 'setup'
        st.rerun()
    
    st.markdown(f"**Total Quizzes:** {len(st.session_state.quiz_history)}")
    
    # Show all quizzes in reverse chronological order
    for i, record in enumerate(reversed(st.session_state.quiz_history)):
        quiz_num = len(st.session_state.quiz_history) - i
        summary = record['summary']
        
        with st.expander(f"Quiz {quiz_num}: {summary['topic']} - {summary['difficulty'].title()} ({summary['accuracy']:.0%})", expanded=False):
            col1, col2, col3 = st.columns(3)
            col1.metric("Score", f"{summary['correct']}/{summary['total']}")
            col2.metric("Accuracy", f"{summary['accuracy']:.1%}")
            col3.metric("Date", summary.get('timestamp', 'N/A'))
            
            if st.button(f"📋 View Details", key=f"view_details_{quiz_num}"):
                st.session_state.selected_history_index = len(st.session_state.quiz_history) - quiz_num - 1
                st.session_state.stage = 'history_view'
                st.rerun()