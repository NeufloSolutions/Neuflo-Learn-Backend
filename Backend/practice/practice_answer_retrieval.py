from Backend.dbconfig.db_connection import create_pg_connection, release_pg_connection, pg_connection_pool

def get_practice_test_answers_only(test_instance_id, student_id, subject_id):
    """
    Retrieve only the answers for a given subject within a test, specific to a student.
    If the subject is Biology (subject_id = 3), retrieve answers for both Botany and Zoology.
    The function now takes in TestInstanceID and retrieves the corresponding PracticeTestID.
    """
    conn = create_pg_connection(pg_connection_pool)
    if not conn:
        return None, "Database connection failed"

    try:
        with conn.cursor() as cur:
            if subject_id == 3:  # Biology
                subject_ids = [3, 4]  # Assuming 3 for Botany and 4 for Zoology, adjust as per your schema
            else:
                subject_ids = [subject_id]

            # Updated query to include join with TestInstances
            cur.execute("""
                SELECT Q.QuestionID, Q.Answer
                FROM Questions Q
                JOIN PracticeTestQuestions PTQ ON Q.QuestionID = PTQ.QuestionID
                JOIN PracticeTestSubjects PTS ON PTQ.PracticeTestSubjectID = PTS.PracticeTestSubjectID
                JOIN PracticeTests PT ON PTS.PracticeTestID = PT.PracticeTestID
                JOIN TestInstances TI ON PT.PracticeTestID = TI.TestID
                JOIN Chapters C ON Q.ChapterID = C.ChapterID
                WHERE TI.TestInstanceID = %s AND C.SubjectID = ANY(%s) AND PT.StudentID = %s
            """, (test_instance_id, subject_ids, student_id))
            
            results = cur.fetchall()
            if results:
                # Extracting the question IDs and their respective answers
                answers = {result[0]: result[1] for result in results}
                return list(answers.values()), None
            else:
                return None, "No answers found for the given test instance ID, subject ID, and student ID"
    except Exception as e:
        return None, str(e)
    finally:
        release_pg_connection(pg_connection_pool, conn)
