import pandas as pd

DATASET_PATH = 'dataset.csv'

def check_dataset_integrity():
    """
    Analyzes the quiz dataset for common issues like duplicate IDs or questions.
    """
    print(f"--- Analyzing '{DATASET_PATH}' for issues ---")
    
    try:
        df = pd.read_csv(DATASET_PATH)
        print(f"✅ Dataset loaded successfully with {len(df)} rows.")
    except FileNotFoundError:
        print(f"❌ ERROR: '{DATASET_PATH}' not found. Please make sure it's in the correct directory.")
        return
    except Exception as e:
        print(f"❌ ERROR: Could not read the CSV file. Error: {e}")
        return

    # --- Check 1: Ensure 'id' column exists ---
    if 'id' not in df.columns:
        print("❌ CRITICAL ERROR: The dataset is missing the required 'id' column.")
        return
    else:
        print("✅ 'id' column is present.")

    # --- Check 2: Find duplicate IDs ---
    id_duplicates = df[df.duplicated(subset=['id'], keep=False)]
    if not id_duplicates.empty:
        print("\n❌ ISSUE FOUND: Duplicate IDs detected! This is a critical issue.")
        print("   The system cannot distinguish between these questions, causing repeats.")
        print("   Please ensure every question has a unique 'id'.")
        print("   Duplicate rows based on 'id':")
        print(id_duplicates[['id', 'question']].sort_values(by='id'))
    else:
        print("✅ No duplicate 'id' values found. Good!")

    # --- Check 3: Find duplicate question text ---
    # This is not a critical error, but it leads to a bad user experience.
    question_duplicates = df[df.duplicated(subset=['question'], keep=False)]
    if not question_duplicates.empty:
        print("\n⚠️ WARNING: Duplicate question text detected!")
        print("   While these may have different IDs, users will see them as repeated questions.")
        print("   Consider removing or rephrasing these duplicates.")
        print("   Duplicate rows based on 'question' text:")
        print(question_duplicates[['id', 'question']].sort_values(by='question'))
    else:
        print("✅ No duplicate 'question' text found. Good!")
        
    print("\n--- Analysis Complete ---")


if __name__ == "__main__":
    check_dataset_integrity()