import sqlite3
from datetime import datetime

def create_long_img_vid_challenges(db_path='/Users/byunmingyu/Desktop/해커톤/2508Hackathon/run.db'):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        long_content_image = """Create a breathtaking fantasy landscape. In the foreground, a crystal-clear river flows from a waterfall cascading down a moss-covered cliff. The river is lined with glowing flora that illuminates the water in shades of blue and purple. On the riverbank, a majestic, ancient tree with silver leaves and a trunk that twists into intricate patterns stands tall. Its branches are home to small, bioluminescent creatures that flit about like fairies. In the background, a magnificent castle with towering spires and elegant bridges is carved into the side of a mountain. The castle is made of a white, marble-like material that seems to glow from within. The sky is a deep twilight, with two moons, one large and one small, and a sky full of vibrant, colorful nebulae. The overall mood should be one of wonder, magic, and tranquility. The style should be highly detailed and realistic, with a touch of the ethereal. Pay close attention to the lighting, with the glowing plants, creatures, and castle being the primary light sources. The reflection of the moons and nebulae on the water should also be visible."""

        long_content_video = """Create a short, one-minute sci-fi film script. The scene is the cockpit of a small, one-person scout ship, the 'Stardust Drifter'. The pilot, Kaelen, is in his late 20s, with a look of weary determination on his face. The cockpit is filled with holographic displays showing star charts, ship diagnostics, and a flashing red alert.

[SCENE START]

**INT. STARDUST DRIFTER - COCKPIT - CONTINUOUS**

The cockpit is dark, illuminated only by the glow of the holographic displays. KAELEN's face is tense as he frantically taps at the controls.

COMPUTER (V.O.)
(A calm, female voice)
Warning. Hull integrity at 15 percent. Life support failing.

Kaelen ignores the warning, his eyes fixed on the main viewscreen, which shows a swirling, chaotic nebula.

KAELEN
(To himself)
Almost there... just a little further.

A sudden jolt shakes the cockpit. Sparks fly from a console.

COMPUTER (V.O.)
Warning. Engine failure imminent.

Kaelen slams his fist on the console in frustration. He takes a deep breath and closes his eyes for a moment. He opens them again, a new resolve in his eyes.

KAELEN
(To the computer)
Override safety protocols. Reroute all remaining power to the main thrusters.

COMPUTER (V.O.)
That action is not recommended. The probability of catastrophic failure is 97.3 percent.

KAELEN
Just do it!

A moment of silence, then the hum of the engines intensifies. The ship lurches forward, deeper into the nebula. The viewscreen is filled with a blinding white light.

COMPUTER (V.O.)
(Calmly)
Thrusters at maximum capacity. Hull integrity at 5 percent.

Kaelen shields his eyes from the light. A small smile plays on his lips.

KAELEN
(Whispering)
I see it...

The white light on the viewscreen fades, revealing a breathtaking view of a pristine, Earth-like planet. It is lush and green, with blue oceans and white clouds.

COMPUTER (V.O.)
Life support has failed. Hull integrity critical.

Kaelen doesn't seem to hear. He stares at the planet, a single tear rolling down his cheek.

KAELEN
(Awe-struck)
It's beautiful...

The ship's engines sputter and die. The cockpit goes dark, except for the faint glow of the planet on the viewscreen. Kaelen's silhouette is visible against the backdrop of his new home.

[SCENE END]
"""

        challenges = [
            (
                'image',
                'hard',
                'The Most Detailed Fantasy Landscape',
                long_content_image,
                206,
                206,
                1,
                datetime.now(),
                datetime.now(),
            ),
            (
                'video',
                'hard',
                'A Sci-Fi Short Film',
                long_content_video,
                207,
                207,
                1,
                datetime.now(),
                datetime.now(),
            ),
        ]

        insert_sql = """INSERT INTO challenge (tag, level, title, content, challenge_number, id, user_id, created_at, modified_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        cursor.executemany(insert_sql, challenges)
        conn.commit()

        print(f"Successfully added {cursor.rowcount} long challenges (image and video).")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_long_img_vid_challenges()
