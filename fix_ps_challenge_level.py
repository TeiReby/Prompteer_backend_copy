import sqlite3

def fix_ps_challenge_level(db_path='/Users/byunmingyu/Desktop/해커톤/2508Hackathon/run.db'):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE challenge SET level = ? WHERE id = ?", ('hard', 205))

        conn.commit()
        print(f"Successfully updated the level of challenge 205 to 'hard'.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    fix_ps_challenge_level()
