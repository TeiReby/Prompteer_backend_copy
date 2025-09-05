import sqlite3
from datetime import datetime

def create_long_ps_challenge(db_path='/Users/byunmingyu/Desktop/해커톤/2508Hackathon/run.db'):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        long_content = """The history of programming is a fascinating journey that spans over a century, marked by brilliant minds, groundbreaking innovations, and a relentless drive to make machines smarter and more capable. It all began long before the first electronic computers were built.\n\n### The 19th Century: The Dawn of an Idea\n
The conceptual foundations of programming were laid in the 19th century. In 1804, Joseph Marie Jacquard invented the Jacquard loom, a machine that used punched cards to automate the process of weaving intricate patterns into fabric. This was the first machine to use stored, sequential instructions to control its operation, a fundamental concept in programming.\n\nHowever, it was Ada Lovelace, a gifted mathematician, who is widely regarded as the first computer programmer. In the 1840s, she worked with Charles Babbage on his Analytical Engine, a mechanical general-purpose computer that was never fully built. Lovelace went beyond simply seeing the machine as a calculator. She envisioned that it could be programmed to create music, art, and manipulate symbols, not just numbers. She wrote the world's first algorithm intended to be processed by a machine, an algorithm to compute Bernoulli numbers.\n### The Early 20th Century: The Rise of Electronic Computing\n
The first half of the 20th century saw the transition from mechanical to electronic computing. The theoretical groundwork was laid by Alan Turing, who in 1936 proposed the concept of a universal machine, now known as a Turing machine. This abstract model of a computer could simulate any computer algorithm, no matter how complex. Turing's work was instrumental in the development of theoretical computer science and artificial intelligence.\nDuring World War II, the need for complex calculations for military purposes, such as code-breaking and ballistics, spurred the development of the first electronic computers. Colossus, developed by the British at Bletchley Park, was the world's first programmable, electronic, digital computer, used to break German ciphers. In the United States, the ENIAC (Electronic Numerical Integrator and Computer) was completed in 1945. It was a massive machine that had to be physically rewired to change its program, a tedious and error-prone process.\n### The 1940s and 1950s: The First Programming Languages\n
The difficulty of programming machines like ENIAC led to the development of the first programming languages. Initially, programmers wrote in machine code, a series of binary digits that the computer could directly understand. This was incredibly difficult and time-consuming. The next step was assembly language, which used mnemonics (short, human-readable abbreviations) to represent machine instructions. An assembler would then translate these mnemonics into machine code.\nIn the 1950s, the first high-level programming languages emerged. These languages were more abstract and closer to human language, making programming more accessible. FORTRAN (Formula Translation), developed by a team at IBM led by John Backus in 1957, was one of the first. It was designed for scientific and engineering calculations. In 1959, COBOL (Common Business-Oriented Language) was created, designed for business data processing. These languages introduced key programming concepts like variables, loops, and conditional statements.\n### The 1960s and 1970s: The Software Crisis and Structured Programming\n
The 1960s saw a rapid growth in the complexity of software, leading to what was termed the "software crisis." Projects were often over budget, late, and unreliable. This led to the development of software engineering as a discipline and the rise of structured programming. Structured programming, championed by Edsger W. Dijkstra, emphasized breaking down programs into smaller, more manageable sub-programs (functions or procedures) and using control structures like if-then-else, for, and while loops. This made programs easier to read, understand, and maintain.\nThis era also saw the birth of many influential programming languages. ALGOL (Algorithmic Language) introduced concepts like block structure and recursion. LISP (List Processing) was designed for artificial intelligence research and introduced the concept of garbage collection. BASIC (Beginner's All-purpose Symbolic Instruction Code) was developed at Dartmouth College to make programming accessible to students. And in 1972, Dennis Ritchie at Bell Labs created the C programming language. C was a powerful and efficient language that gave programmers low-level control over the hardware, and it would go on to become one of the most influential programming languages of all time.\n### The 1980s: The Personal Computer Revolution and Object-Oriented Programming\n
The 1980s was the decade of the personal computer. The rise of machines like the Apple II, IBM PC, and Commodore 64 brought computing into homes and small businesses. This created a huge demand for software, and new programming paradigms emerged to manage the increasing complexity.\nObject-oriented programming (OOP) became popular during this time. OOP is a paradigm that organizes software design around data, or objects, rather than functions and logic. An object is a self-contained entity that consists of both data and the procedures to manipulate that data. Key OOP concepts include encapsulation, inheritance, and polymorphism. Smalltalk, developed at Xerox PARC, was one of the first purely object-oriented languages. C++, developed by Bjarne Stroustrup as an extension of C, added object-oriented features to C and became a dominant language for application development. Other object-oriented languages from this era include Objective-C and Eiffel.\n### The 1990s: The World Wide Web and the Rise of the Internet\n
The 1990s was dominated by the rise of the World Wide Web. This created a whole new platform for software, and new languages were created to build web applications. HTML (HyperText Markup Language) was created to structure web pages. JavaScript, created by Brendan Eich at Netscape, was a scripting language that could be embedded in web pages to make them interactive. On the server-side, languages like Perl, PHP, and Python became popular for processing web forms and interacting with databases.\nIn 1995, Sun Microsystems released Java, a language designed with the mantra "write once, run anywhere." Java programs are compiled into bytecode, which can be run on any machine with a Java Virtual Machine (JVM). This made it ideal for web applications and it quickly became one of the most popular programming languages in the world.\n### The 21st Century: The Age of the Web, Mobile, and AI\n
The 21st century has seen an explosion in the diversity of programming languages and platforms. The web has become more dynamic and interactive with the rise of frameworks like Ruby on Rails, Django, and Node.js. The rise of smartphones has created a huge market for mobile apps, with languages like Swift (for iOS) and Kotlin (for Android) becoming popular.\n
The field of data science and machine learning has also driven the development of new tools and languages. Python, with its rich ecosystem of libraries like NumPy, Pandas, and TensorFlow, has become the dominant language for data science. R is another popular language for statistical computing and graphics.\nIn recent years, there has been a trend towards languages that are more expressive, safer, and more concurrent. Languages like Go, Rust, and Scala are gaining popularity for their modern features and performance.\n
The history of programming is a testament to human ingenuity and our desire to create tools that extend our intellectual reach. From the mechanical looms of the 19th century to the artificial intelligence of the 21st, programming has transformed every aspect of our lives, and it will continue to do so in the years to come."""

        challenge = (
            'ps',
            'Hard',
            'The Longest Challenge Ever',
            long_content,
            205,
            205,
            1,
            datetime.now(),
            datetime.now(),
        )

        insert_sql = """INSERT INTO challenge (tag, level, title, content, challenge_number, id, user_id, created_at, modified_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        cursor.execute(insert_sql, challenge)
        conn.commit()

        print(f"Successfully added the long ps challenge.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_long_ps_challenge()
