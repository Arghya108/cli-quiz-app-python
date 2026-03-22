"""
==============================================
  Quiz App (CLI) - Python Portfolio Project
  Author: Built with Python Standard Library
  Features: Timer, Difficulty Levels, Scoring
==============================================
"""

import json
import random
import threading
import os
import sys
import time


# ─────────────────────────────────────────────
#   ANSI COLOR CODES (no external libraries)
# ─────────────────────────────────────────────

class Color:
    """ANSI escape codes for terminal colors."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    MAGENTA = "\033[95m"
    BLUE    = "\033[94m"
    DIM     = "\033[2m"

def colorize(text, color):
    """Wrap text with a color code and reset."""
    return f"{color}{text}{Color.RESET}"


# ─────────────────────────────────────────────
#   QUESTION LOADER
# ─────────────────────────────────────────────

def load_questions(filepath):
    """
    Load questions from a JSON file.
    Returns a list of question dictionaries.
    Raises clear errors if the file is missing or corrupted.
    """
    # Check if the file exists before trying to open it
    if not os.path.exists(filepath):
        print(colorize(f"\n[ERROR] File not found: '{filepath}'", Color.RED))
        print(colorize("Make sure 'questions.json' is in the same folder as quiz_app.py", Color.YELLOW))
        sys.exit(1)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except json.JSONDecodeError as e:
        print(colorize(f"\n[ERROR] Invalid JSON format: {e}", Color.RED))
        print(colorize("Check your questions.json file for syntax errors.", Color.YELLOW))
        sys.exit(1)

    # Basic validation — each question must have these fields
    required_fields = {"question", "options", "answer", "difficulty"}
    for i, q in enumerate(questions):
        missing = required_fields - q.keys()
        if missing:
            print(colorize(f"\n[ERROR] Question #{i+1} is missing fields: {missing}", Color.RED))
            sys.exit(1)

    return questions


def filter_by_difficulty(questions, difficulty):
    """
    Filter the question list based on the selected difficulty.
    'all' returns every question.
    """
    if difficulty == "all":
        return questions
    return [q for q in questions if q["difficulty"].lower() == difficulty]


# ─────────────────────────────────────────────
#   TIMER SYSTEM
# ─────────────────────────────────────────────

def timed_input(prompt, timeout):
    """
    Show a prompt and wait for user input with a timeout.
    Returns the user's answer (string) or None if time runs out.

    How it works:
    - A background daemon thread calls input() and stores the result.
    - The main thread waits for that thread to finish (join with timeout).
    - If time runs out before input is given, we return None.
    - Daemon=True means the thread is killed automatically when main exits.
    """
    print(prompt, end="", flush=True)

    answer_container = [None]  # Use a list so the thread can write to it

    def collect_input():
        try:
            answer_container[0] = input().strip().upper()
        except EOFError:
            # Handles piped input or closed stdin
            answer_container[0] = None

    input_thread = threading.Thread(target=collect_input, daemon=True)
    input_thread.start()
    input_thread.join(timeout=timeout)  # Wait at most 'timeout' seconds

    return answer_container[0]


# ─────────────────────────────────────────────
#   SCORING SYSTEM
# ─────────────────────────────────────────────

def calculate_score(results):
    """
    Given a list of result dicts, calculate totals and percentage.
    Each result dict has: 'correct' (bool), 'timed_out' (bool)

    Returns a summary dict.
    """
    total      = len(results)
    correct    = sum(1 for r in results if r["correct"])
    wrong      = sum(1 for r in results if not r["correct"] and not r["timed_out"])
    timed_out  = sum(1 for r in results if r["timed_out"])
    percentage = (correct / total * 100) if total > 0 else 0

    return {
        "total":      total,
        "correct":    correct,
        "wrong":      wrong,
        "timed_out":  timed_out,
        "percentage": round(percentage, 1)
    }


def get_grade(percentage):
    """Return a letter grade and message based on score percentage."""
    if percentage >= 90:
        return colorize("A+  Excellent! You really know your stuff.", Color.GREEN)
    elif percentage >= 75:
        return colorize("B   Good job. A little more practice won't hurt.", Color.CYAN)
    elif percentage >= 50:
        return colorize("C   Average. You need to study more.", Color.YELLOW)
    else:
        return colorize("F   Poor. Go back to basics.", Color.RED)


# ─────────────────────────────────────────────
#   DISPLAY HELPERS
# ─────────────────────────────────────────────

def clear_screen():
    """Clear the terminal screen (works on Windows and Unix)."""
    os.system("cls" if os.name == "nt" else "clear")


def print_separator(char="─", length=50):
    """Print a horizontal separator line."""
    print(colorize(char * length, Color.DIM))


def print_header():
    """Print the quiz app banner."""
    clear_screen()
    print_separator("═")
    print(colorize("          🧠  PYTHON QUIZ APP (CLI)  🧠", Color.CYAN + Color.BOLD))
    print(colorize("       Test your Python knowledge!", Color.DIM))
    print_separator("═")
    print()


def show_instructions(time_limit, total_questions):
    """Display the rules and instructions before the quiz starts."""
    print(colorize("📋  HOW TO PLAY:", Color.YELLOW + Color.BOLD))
    print_separator()
    print(f"  ▸ You will answer {colorize(str(total_questions), Color.CYAN)} questions.")
    print(f"  ▸ Each question has {colorize(str(time_limit) + ' seconds', Color.CYAN)} time limit.")
    print(f"  ▸ Type {colorize('A', Color.GREEN)}, {colorize('B', Color.GREEN)}, {colorize('C', Color.GREEN)}, or {colorize('D', Color.GREEN)} then press Enter.")
    print(f"  ▸ If you don't answer in time, it's marked {colorize('WRONG', Color.RED)}.")
    print(f"  ▸ Your score is shown at the end.")
    print_separator()
    print()


def display_question(q_number, total, question_data, time_limit):
    """
    Display a single question with its options.
    Returns the user's raw input (or None on timeout).
    """
    print()
    print_separator()

    # Question header with progress
    progress = f"Question {q_number}/{total}"
    difficulty_tag = question_data["difficulty"].upper()

    # Color code the difficulty
    diff_colors = {
        "EASY":   Color.GREEN,
        "MEDIUM": Color.YELLOW,
        "HARD":   Color.RED
    }
    diff_color = diff_colors.get(difficulty_tag, Color.WHITE)

    print(f"  {colorize(progress, Color.BOLD)}  [{colorize(difficulty_tag, diff_color)}]")
    print()

    # Print the question text
    print(f"  {colorize(question_data['question'], Color.WHITE + Color.BOLD)}")
    print()

    # Print each option
    option_colors = {"A": Color.CYAN, "B": Color.CYAN, "C": Color.CYAN, "D": Color.CYAN}
    for key, value in question_data["options"].items():
        print(f"    {colorize(f'[{key}]', option_colors[key])}  {value}")

    print()
    print_separator()

    # Countdown hint and input prompt
    print(colorize(f"  ⏱  You have {time_limit} seconds to answer.", Color.MAGENTA))
    user_answer = timed_input(
        colorize("  ➤  Your answer (A/B/C/D): ", Color.YELLOW),
        timeout=time_limit
    )

    return user_answer


def show_feedback(user_answer, correct_answer, timed_out):
    """
    Show immediate feedback after each question:
    correct/wrong, and what the right answer was.
    """
    print()

    if timed_out:
        print(colorize("  ⏰  TIME'S UP! You didn't answer in time.", Color.RED + Color.BOLD))
    elif user_answer == correct_answer:
        print(colorize("  ✅  CORRECT! Well done.", Color.GREEN + Color.BOLD))
    else:
        print(colorize(f"  ❌  WRONG! You answered: {user_answer}", Color.RED + Color.BOLD))

    # Always show the correct answer
    print(colorize(f"  📌  Correct answer was: {correct_answer}", Color.CYAN))
    print()


def show_final_score(score_summary):
    """Display the final score summary at the end of the quiz."""
    print()
    print_separator("═")
    print(colorize("              🏁  QUIZ COMPLETE! 🏁", Color.CYAN + Color.BOLD))
    print_separator("═")
    print()
    print(f"  {colorize('Total Questions :', Color.WHITE)}  {score_summary['total']}")
    print(f"  {colorize('Correct         :', Color.GREEN)}  {score_summary['correct']}")
    print(f"  {colorize('Wrong           :', Color.RED)}  {score_summary['wrong']}")
    print(f"  {colorize('Timed Out       :', Color.YELLOW)}  {score_summary['timed_out']}")
    print()
    print(f"  {colorize('Your Score      :', Color.BOLD)}  {score_summary['correct']}/{score_summary['total']}")
    print(f"  {colorize('Percentage      :', Color.BOLD)}  {score_summary['percentage']}%")
    print()
    print_separator()
    grade_message = get_grade(score_summary["percentage"])
    print(f"  {colorize('Grade:', Color.BOLD)} {grade_message}")
    print_separator("═")
    print()


# ─────────────────────────────────────────────
#   DIFFICULTY SELECTOR
# ─────────────────────────────────────────────

def select_difficulty():
    """
    Prompt the user to choose a difficulty level.
    Keeps asking until a valid option is entered.
    Returns a lowercase string like 'easy', 'medium', 'hard', 'all'.
    """
    valid_choices = {"1": "easy", "2": "medium", "3": "hard", "4": "all"}

    print(colorize("🎯  SELECT DIFFICULTY:", Color.YELLOW + Color.BOLD))
    print_separator()
    print(f"  {colorize('[1]', Color.GREEN)}  Easy")
    print(f"  {colorize('[2]', Color.YELLOW)}  Medium")
    print(f"  {colorize('[3]', Color.RED)}  Hard")
    print(f"  {colorize('[4]', Color.CYAN)}  All Levels")
    print_separator()

    while True:
        choice = input(colorize("  ➤  Enter your choice (1-4): ", Color.YELLOW)).strip()
        if choice in valid_choices:
            difficulty = valid_choices[choice]
            print(f"\n  {colorize(f'Difficulty set to: {difficulty.upper()}', Color.CYAN)}")
            time.sleep(1)
            return difficulty
        else:
            print(colorize("  ⚠  Invalid choice. Please enter 1, 2, 3, or 4.", Color.RED))


# ─────────────────────────────────────────────
#   QUIZ ENGINE
# ─────────────────────────────────────────────

def run_quiz(questions, time_limit=10):
    """
    Core quiz engine: loops through questions,
    displays each one, collects input, evaluates answers,
    and builds a results list.

    Parameters:
        questions  -- list of question dicts (already filtered)
        time_limit -- seconds per question (default 10)

    Returns:
        results -- list of dicts with answer details per question
    """
    results = []

    # Randomize question order every time
    random.shuffle(questions)

    total = len(questions)

    for index, question in enumerate(questions, start=1):
        # Display the question and get the user's answer
        user_answer = display_question(index, total, question, time_limit)

        correct_answer = question["answer"].upper()

        # Determine if user timed out
        timed_out = user_answer is None

        # Check correctness
        is_correct = (not timed_out) and (user_answer == correct_answer)

        # Show feedback right after the answer
        show_feedback(user_answer, correct_answer, timed_out)

        # Save result for this question
        results.append({
            "question":   question["question"],
            "user_answer": user_answer,
            "correct":    is_correct,
            "timed_out":  timed_out
        })

        # Small pause so the user can read feedback
        if index < total:
            input(colorize("  Press Enter for next question...", Color.DIM))

    return results


# ─────────────────────────────────────────────
#   MAIN ENTRY POINT
# ─────────────────────────────────────────────

def main():
    """
    Main function that ties everything together:
    1. Load questions from JSON
    2. Show header + instructions
    3. Get difficulty from user
    4. Filter questions by difficulty
    5. Run the quiz engine
    6. Calculate and display final score
    """
    # --- Config ---
    QUESTIONS_FILE = "questions.json"
    TIME_LIMIT     = 10  # seconds per question (change this to adjust)

    # Step 1: Load all questions from JSON
    all_questions = load_questions(QUESTIONS_FILE)

    # Step 2: Show header
    print_header()

    # Step 3: Select difficulty
    difficulty = select_difficulty()

    # Step 4: Filter questions
    filtered_questions = filter_by_difficulty(all_questions, difficulty)

    # Handle the case where no questions match the chosen difficulty
    if len(filtered_questions) == 0:
        print(colorize(f"\n  [!] No questions found for difficulty: '{difficulty}'.", Color.RED))
        print(colorize("      Check your questions.json file.\n", Color.YELLOW))
        sys.exit(1)

    # Step 5: Show instructions
    clear_screen()
    print_header()
    show_instructions(TIME_LIMIT, len(filtered_questions))

    input(colorize("  Press Enter to START the quiz...", Color.GREEN + Color.BOLD))

    # Step 6: Run the quiz
    results = run_quiz(filtered_questions, time_limit=TIME_LIMIT)

    # Step 7: Calculate and show final score
    score_summary = calculate_score(results)
    clear_screen()
    print_header()
    show_final_score(score_summary)


# ─────────────────────────────────────────────
#   PROGRAM ENTRY
# ─────────────────────────────────────────────

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully — no ugly stack trace
        print(colorize("\n\n  [!] Quiz interrupted. Goodbye!\n", Color.YELLOW))
        sys.exit(0)
