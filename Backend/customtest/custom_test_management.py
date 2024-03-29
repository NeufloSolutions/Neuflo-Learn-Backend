import random
from Backend.dbconfig.db_connection import create_pg_connection, release_pg_connection, pg_connection_pool
from Backend.dbconfig.cache_management import get_cached_questions, cache_questions


def generate_custom_test(chapter_ids: list, total_questions: int):
    conn = create_pg_connection(pg_connection_pool)
    if not conn:
        return {"error": "Database connection failed"}, None
    
    try:
        with conn.cursor() as cur:
            # Fetch questions from the specified chapters
            questions = fetch_questions(cur, chapter_ids, total_questions)
            
            # Format and return the questions
            formatted_questions = format_questions(cur, questions)
            
            return {"questions": formatted_questions}, None
    except Exception as e:
        return None, str(e)
    finally:
        release_pg_connection(pg_connection_pool, conn)


def fetch_questions(cur, chapter_ids: list, total_questions: int):
    valid_chapter_questions = {}  # Dictionary to hold chapter_id: available_questions pairs
    
    # First, validate chapters and count available questions for each
    for chapter_id in chapter_ids:
        cur.execute("""
            SELECT q.QuestionID FROM Questions q
            JOIN Chapters c ON q.ChapterID = c.ChapterID
            WHERE q.ChapterID = %s AND c.IsActive = TRUE
        """, (chapter_id,))
        available_questions = [row[0] for row in cur.fetchall()]
        if available_questions:  # If there are any questions available, consider the chapter valid
            valid_chapter_questions[chapter_id] = available_questions
    
    if not valid_chapter_questions:
        raise ValueError("None of the provided chapter IDs have enough questions or are active.")
    
    # Determine how many questions to attempt to fetch from each valid chapter
    total_valid_chapters = len(valid_chapter_questions)
    questions_per_chapter_base = total_questions // total_valid_chapters
    remainder = total_questions % total_valid_chapters
    
    question_ids = []

    for index, (chapter_id, available_questions) in enumerate(valid_chapter_questions.items()):
        questions_to_fetch = questions_per_chapter_base + (1 if index < remainder else 0)
        if len(available_questions) < questions_to_fetch:
            # If a chapter does not have enough questions, adjust expectations and continue
            continue
        
        # Randomly select questions for this chapter
        selected_questions = random.sample(available_questions, questions_to_fetch)
        question_ids.extend(selected_questions)
    
    # If after attempting to gather questions we have less than requested, notify caller
    if len(question_ids) < total_questions:
        raise ValueError("After filtering out invalid or insufficient chapters, not enough questions could be gathered to fulfill the total request.")
    
    return question_ids



def format_questions(cur, question_ids: list):
    formatted_questions = []
    
    question_placeholders = ','.join(['%s'] * len(question_ids))
    cur.execute(f"""
        SELECT q.QuestionID, q.Question, q.OptionA, q.OptionB, q.OptionC, q.OptionD, q.Answer, q.Explanation, i.ImageURL 
        FROM Questions q
        LEFT JOIN Images i ON q.QuestionID = i.QuestionID
        WHERE q.QuestionID IN ({question_placeholders})
    """, tuple(question_ids))
    
    for row in cur.fetchall():
        formatted_questions.append({
            "question_id": row[0],
            "question": row[1],
            "options": {"A": row[2], "B": row[3], "C": row[4], "D": row[5]},
            "answer": row[6],
            "explanation": row[7],
            "image_url": row[8]  # This could be None if no image is associated
        })
    
    return formatted_questions

