from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from alembic import op
import sqlalchemy as sa
import io
import contextlib
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('submission', sa.Column('question', sa.String(length=200), nullable=False, server_default=''))
    op.alter_column('submission', 'question', server_default=None)
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate
# Define your database models
# Define your database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    batch = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'
    submissions = db.relationship('Submission', backref='user', lazy=True)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.String(200), nullable=False)
    selected_option = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    @property
    def score(self):
        return sum(answer.is_correct for answer in self.answers)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    question = db.Column(db.String(200), nullable=False)
    selected_option = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer)
    answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    output = db.Column(db.Text)  # Add this line to include code execution output

    user = db.relationship('User', backref='results')
    # Here you would also set up a relationship to the Question model, if you have one.


# Hardcoded password for demonstration
TEACHER_PASSWORD = "123"

batch_names = [
    "SunTues_8.10PM", "MonThurs_7Pm", "MonThur_8.10PM",
    "FriSat_10AM", "Frisat_11AM", "FriSat_2.50PM",
    "FriSat_8.10PM", "FriSat_7.00pm", "SatSun_5.50pm",
    "SunTues_7.00pm", "FriMon_5.50pm", "TuesThurs5.50pm",
    "SunTues_4.30pm", "Fri-sat_4.30PM", "Mon-Thus_4.30PM"
]
@app.route('/start')
def start():
    # Pass the batch names to the template
    return render_template('start.html', batches=batch_names)
# Questions
questions = [
    {"text": "How do you start a for loop in Python?", "choices": ["for i in range(10):", "for i < 10:", "for i to 10:", "for 10 times:"], "answer": "for i in range(10):"},
    {"text": "What function is used to print something in Python?", "choices": ["echo()", "console.log()", "print()", "out()"], "answer": "print()"},
    {"text": "How can you draw a circle in Python?", "choices": ["circle()", "drawCircle()", "turtle.circle()", "Canvas.circle()"], "answer": "turtle.circle()"},
    {"text": "How to change a variable's value in Python?", "choices": ["var = 1", "variable change to 1", "var == 1", "set var = 1"], "answer": "var = 1"},
    {"text": "Which operator is used to check equality in Python?", "choices": ["=", "==", "===", "equals"], "answer": "=="},
    {"text": "What does the 'if' statement do in Python?", "choices": ["Loops through a block of code", "Checks a condition and executes a block of code if the condition is true", "Declares a variable", "Prints a message"], "answer": "Checks a condition and executes a block of code if the condition is true"},
    {"text": "How do you take user input in Python?", "choices": ["input()", "console.read()", "read()", "getInput()"], "answer": "input()"},
    {"text": "What is the correct way to declare a list in Python?", "choices": ["list = [1, 2, 3]", "[1, 2, 3]", "array(1, 2, 3)", "list(1, 2, 3)"], "answer": "list = [1, 2, 3]"},
    {"text": "How do you add an element to a list in Python?", "choices": ["list.append(4)", "list.add(4)", "list.push(4)", "list.insert(4)"], "answer": "list.append(4)"},
    {"text": "What is the output of print(8 == 8)?", "choices": ["True", "False", "8", "Error"], "answer": "True"},
    {"text": "How to print a number in Python?", "choices": ["printNumber()", "echo()", "console.log()", "print()"], "answer": "print()"},
    {"text": "Which of the following is used to create a variable in Python?", "choices": ["var variableName", "variableName = value", "int variableName", "create variableName"], "answer": "variableName = value"},
    {"text": "What are the rules for naming a variable in Python?", "choices": ["Must start with a letter or underscore", "Can start with a number", "Special characters (!, @, #) are allowed at the start", "No rules"], "answer": "Must start with a letter or underscore"},
    {"text": "How to draw a square using loops in Python?", "choices": ["Use a for loop with range(4)", "Use a while loop with a counter", "Draw four lines manually", "Squares cannot be drawn using loops"], "answer": "Use a for loop with range(4)"},
    {"text": "Which function allows you to take user input in Python?", "choices": ["getUserInput()", "input()", "scanf()", "readLine()"], "answer": "input()"},
    {"text": "How to check if an item exists in a list in Python?", "choices": ["list.contains(item)", "item in list", "list.exists(item)", "list.hasItem(item)"], "answer": "item in list"},
    {"text": "What is the correct way to use an if-else statement in Python?", "choices": ["if condition: ... else: ...", "if (condition) {...} else {...}", "if condition then ... else ...", "if condition do ... otherwise ..."], "answer": "if condition: ... else: ..."},
    {"text": "How to find the length of a list in Python?", "choices": ["length(list)", "list.length()", "len(list)", "list.size()"], "answer": "len(list)"},
    {"text": "What is the output of 'FizzBuzz' program when the input is 15?", "choices": ["Fizz", "Buzz", "FizzBuzz", "15"], "answer": "FizzBuzz"},
    {"text": "How to find the maximum value in a list?", "choices": ["max(list)", "list.max()", "maximum(list)", "list.getMaximum()"], "answer": "max(list)"},
    {"text": "What is used to create a tuple in Python?", "choices": ["()", "[]", "{}", "<>"], "answer": "()"},
    {"text": "What method is used to add an item to a set in Python?", "choices": ["add()", "insert()", "append()", "push()"], "answer": "add()"},
    {"text": "How to convert a string to lower case in Python?", "choices": ["toLowerCase()", "lower()", "toLower()", "makeLower()"], "answer": "lower()"},
    {"text": "How do you reverse a string in Python?", "choices": ["reverse()", "string.reverse()", "[::-1]", "str.reverse()"], "answer": "[::-1]"},
    {"text": "Which function in Python is used to generate a random number?", "choices": ["random()", "rand()", "generateRandom()", "math.random()"], "answer": "random()"},
    {"text": "How to concatenate two strings in Python?", "choices": ["+", "concat()", "append()", "join()"], "answer": "+"},
    {"text": "What is the correct way to declare a set in Python?", "choices": ["set = {1, 2, 3}", "{1, 2, 3}", "set(1, 2, 3)", "[1, 2, 3]"], "answer": "set = {1, 2, 3}"},
    {"text": "How to remove duplicates from a list in Python?", "choices": ["list(set(list))", "removeDuplicates(list)", "list.unique()", "unique(list)"], "answer": "list(set(list))"},
    {"text": "What is the correct syntax to print the type of a variable in Python?", "choices": ["print(type(var))", "print(var.type())", "type(print(var))", "print(typeof var)"], "answer": "print(type(var))"},
    {"text": "What is the output of len([1, 2, 3]) in Python?", "choices": ["3", "2", "1", "0"], "answer": "3"},
    {"text": "How to check if a number is even in Python?", "choices": ["if num % 2 == 0:", "if num / 2 == 0:", "if num == even:", "if isEven(num):"], "answer": "if num % 2 == 0:"},
    {"text": "What does the 'break' statement do in Python?", "choices": ["Pauses a loop", "Stops the loop and exits it", "Breaks the program", "Continues to the next iteration"], "answer": "Stops the loop and exits it"},
    {"text": "How to find the length of a string in Python?", "choices": ["str.length()", "len(str)", "string.len()", "length(str)"], "answer": "len(str)"},
    {"text": "How to create a list with numbers ranging from 1 to 10 in Python?", "choices": ["range(1, 11)", "list(1, 10)", "[1, 2, ..., 10]", "[1..10]"], "answer": "range(1, 11)"},
    {"text": "How to check if 'Python' is in the list ['Java', 'Python', 'C#']?", "choices": ["'Python' in ['Java', 'Python', 'C#']", "['Java', 'Python', 'C#'].contains('Python')", "['Java', 'Python', 'C#'].has('Python')", "'Python'.exists(['Java', 'Python', 'C#'])"], "answer": "'Python' in ['Java','C#']", "answer": "'Python' in ['Java', 'Python', 'C#']"},
    {"text": "How can you generate a list of numbers from 1 to 5 in Python?", "choices": ["list(1, 5)", "range(1, 6)", "[1, 2, 3, 4, 5]", "range(1, 5)"], "answer": "range(1, 6)"},
    {"text": "What is the correct way to import a module in Python?", "choices": ["#include <module>", "import module", "using module", "@import 'module'"], "answer": "import module"},
    {"text": "What does the 'continue' statement do in a loop in Python?", "choices": ["Stops the loop", "Skips the rest of the code inside the loop for the current iteration", "Terminates the program", "None of the above"], "answer": "Skips the rest of the code inside the loop for the current iteration"},
    {"text": "How do you define a block of code in Python?", "choices": ["Curly braces {}", "Indentation", "Parentheses ()", "Begin/End keywords"], "answer": "Indentation"},
    {"text": "Which loop is used to iterate over a sequence (like a list, tuple, set, or dictionary) in Python?", "choices": ["for loop", "while loop", "do-while loop", "loop through"], "answer": "for loop"},
    {"text": "How to create an empty set in Python?", "choices": ["set()", "{}", "[]", "()"], "answer": "set()"},
    {"text": "What is the output of print(2 ** 3) in Python?", "choices": ["8", "6", "9", "5"], "answer": "8"},
    {"text": "What is the result of 'Hello' + 'World' in Python?", "choices": ["HelloWorld","HelloWorld", "Hello World", "Hello-World", "None of the above"], "answer": "HelloWorld"},
    {"text": "Which method is used to replace parts of a string in Python?", "choices": ["replace()", "substitute()", "change()", "swap()"], "answer": "replace()"},
    {"text": "What is the correct way to handle multiple conditions in an if statement in Python?", "choices": ["if condition1 and condition2:", "if condition1 & condition2:", "if condition1 + condition2:", "if condition1 then condition2:"], "answer": "if condition1 and condition2:"},
    {"text": "What is the output of print('Python'[1])?", "choices": ["P", "y", "t", "h"], "answer": "y"},
    {"text": "What is the output of print(10 / 2)?", "choices": ["5", "5.0", "10", "Error"], "answer": "5.0"},
    {"text": "How to convert a list into a tuple in Python?", "choices": ["tuple(list)", "list.toTuple()", "(list)", "convert(list, 'tuple')"], "answer": "tuple(list)"},
    {"text": "What does 'continue' do in a loop?", "choices": ["Stops the loop immediately", "Skips the current iteration and continues with the next one", "Pauses the execution of the loop", "Terminates the program"], "answer": "Skips the current iteration and continues with the next one"},
    {"text": "What is the correct way to write a comment in Python?", "choices": ["// This is a comment", "<!-- This is a comment -->", "# This is a comment", "/* This is a comment */"], "answer": "# This is a comment"},
]


coding_questions = [
    {
        "id": 1,
        "text": "The Magic Number Garden grows numbers instead of flowers. Every day, a new number blooms! Write a Python program to show the blooming numbers from 1 to 5.",
        "starter_code": """
for i in range(1, ____):
    print(i)
""",
        "output": "1\n2\n3\n4\n5",
        "hint": "Remember, range starts from the first number and goes up to, but does not include, the second number."
    },
    {
        "id": 2,
        "text": "Penny the Penguin loves to count her fish before eating them. Today, she has 5 fish. Help Penny count her fish by writing a program.",
        "starter_code": """
fish_count = ____
print(fish_count)
""",
        "output": "5",
        "hint": "Just set the variable fish_count to how many fish Penny has and print it."
    },
    {
        "id": 3,
        "text": "In the world of wizards, spells are numbers. The spell for turning day into night is '3'. Write a program that casts this spell by printing the spell number.",
        "starter_code": """
spell_number = ____
print(spell_number)
""",
        "output": "3",
        "hint": "Set the variable spell_number to the magic number and print it."
    },
    {
        "id": 4,
        "text": "Charlie the Cheetah is playing hide and seek. He needs to count to 5 before searching. Help Charlie count by writing a counting program.",
        "starter_code": """
for i in range(1, ____):
    print(i)
""",
        "output": "1\n2\n3\n4\n5",
        "hint": "Use a for loop with range starting from 1 up to but not including 6."
    },
    {
        "id": 5,
        "text": "Oliver the Owl is wise and knows many things. He knows the secret number of the forest is '4'. Write a program to reveal this secret number.",
        "starter_code": """
secret_number = ____
print(secret_number)
""",
        "output": "4",
        "hint": "Assign the secret number to the variable and then print it."
    },
    {
        "id": 6,
        "text": "The magical fruit basket gets double fruits every day. If it starts with 1 apple on Monday, how many apples are there on Tuesday? Write a program to calculate this.",
        "starter_code": """
apples_on_monday = 1
apples_on_tuesday = apples_on_monday * ____
print(apples_on_tuesday)
""",
        "output": "2",
        "hint": "Multiply the number of apples on Monday by 2 to find out how many are there on Tuesday."
    },
    {
        "id": 7,
        "text": "Fiona the Frog jumps 2 lily pads at a time. If there are 5 lily pads, on which pad does she land last? Write a program to find out.",
        "starter_code": """
total_pads = 5
last_pad = total_pads % ____
print(last_pad)
""",
        "output": "1",
        "hint": "Use the modulo operator (%) to find out the remainder when total pads are divided by Fiona's jump length."
    },
    {
        "id": 8,
        "text": "Daisy the Dinosaur is learning to roar. She roars 'Roar!' 3 times every morning. Can you write a program that helps Daisy practice her roar?",
        "starter_code": """
for i in range(1, ____):
    print("Roar!")
""",
        "output": "Roar!\nRoar!\nRoar!",
        "hint": "Use a loop that repeats the print statement 3 times."
    },
    {
        "id": 11,
        "text": "Imagine you're creating a magical spell with Python that shows 'Magic!' 7 times. Can you write a loop that prints 'Magic!' exactly 7 times?",
        "starter_code": """
for i in range(____):
    print("____")
""",
        "output": "Magic!\nMagic!\nMagic!\nMagic!\nMagic!\nMagic!\nMagic!",
        "hint": "Use a range function inside the for loop to repeat something 7 times."
    },
    {
        "id": 12,
        "text": "There's a box of crystals, each with a number. If the number is 3, the crystal grants wishes. Print numbers 1 through 5, but for 3, print 'Wish granted!' instead.",
"starter_code": """
for i in range(1, ____):
if i == :
print("")
else:
print(i)
""",
"output": "1\n2\nWish granted!\n4\n5",
"hint": "Remember, if a special condition is met, something different should happen."
},
{
"id": 13,
"text": "Help Timmy the Turtle draw a square. Each side of the square is 100 steps. Can you write a loop that makes Timmy move forward and turn right 4 times?",
"starter_code": """
import turtle

timmy = turtle.Turtle()

for i in range(4):
timmy.forward()
timmy.right()
""",
"output": "This question requires visual output that represents a square. The output will be the actions performed by Timmy the Turtle, not text.",
"hint": "Timmy turns right by 90 degrees to draw a square. This question's validation would need to be adjusted for a visual or simulated output."
},
{
"id": 14,
"text": "A sorcerer needs help counting his potions from 1 to 10 backward for a spell. Can you write a loop that counts backward for the sorcerer?",
"starter_code": """
for i in range(, 0, ):
print(i)
""",
"output": "10\n9\n8\n7\n6\n5\n4\n3\n2\n1",
"hint": "Use the range function with a negative step to count backward."
},
{
"id": 15,
"text": "The enchanted forest lights up at night with glowing flowers. Write a program that prints 'Glow' for numbers 1 to 4, and 'Super Glow!' for number 5.",
"starter_code": """
for i in range(1, ):
if i < 5:
print("")
else:
print("")
""",
"output": "Glow\nGlow\nGlow\nGlow\nSuper Glow!",
"hint": "Remember, 'Super Glow!' is only for the special number 5."
},
{
"id": 16,
"text": "In a game, collecting a star doubles your points. Starting at 1 point, how many points will you have after collecting 5 stars?",
"starter_code": """
points = 1
for star in range():
points = points * ____
print("Total points:", points)
""",
"output": "Total points: 32",
"hint": "Each star doubles the points. So, multiply the points by 2 for every star collected."
},
{
"id": 17,
"text": "Write a function called 'greet' that says hello to someone. The function takes a name as input and prints 'Hello, [name]!'",
"starter_code": """
def greet(name):
print("Hello, " + ____ + "!")

greet("Alice")
""",
"output": "Hello, Alice!",
"hint": "Use the plus (+) operator to join strings in the print function."
},
]

quiz_submissions = []


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        batch = request.form.get('batch')
        role = request.form.get('role')
        test_type = request.form.get('testType')
        password = request.form.get('password')

        # For simplicity, creating a new user every time. Adjust according to your needs.
        user = User(name=name, batch=batch, role=role)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        session['test_type'] = request.form['testType']
        if role == 'teacher' and password == TEACHER_PASSWORD:
            # Redirect to teacher's results page if the role is teacher and password is correct
            return redirect(url_for('view_results'))
        elif role == 'student':
            if test_type == 'mcq':
                # Redirect to MCQ test page if the test type is MCQ
                return render_template('quiz.html', questions=questions, name=name, batch=batch)
            elif test_type == 'coding':
                # Redirect to coding test page if the test type is coding
                # This assumes you have a separate HTML template for the coding test
                return redirect(url_for('coding_test'))
            else:
                flash('Invalid test type selected.', 'error')
                return redirect(url_for('index'))
        else:
            flash('Unauthorized access or incorrect password. Please try again.', 'error')
            return redirect(url_for('index'))
    return render_template('index.html')
@app.route('/coding_test')
def coding_test():
    # Debug: Print the session and user role to the console
    print("Session:", session)
    print("User ID:", session.get('user_id'))

    # ... existing checks ...

    # Debug: Print the questions to the console
    print("Questions:", coding_questions)

    return render_template('coding_test.html', questions=coding_questions)




@app.route('/submit', methods=['POST'])
def submit():
    user_id = session.get('user_id')
    if not user_id:
        flash('Session expired or user not found.', 'error')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    if user.role != 'student':
        flash('Unauthorized access. Only students can submit quizzes.', 'error')
        return redirect(url_for('index'))

    # Process each question
    for i, question in enumerate(questions, start=1):
        selected_option = request.form.get(f'question{i}')

        # Check if an option was selected
        if selected_option is None:
            # Handle unanswered question; skip, flash a message, or default action
            flash(f'Question {i} was not answered. It will be marked as incorrect.', 'warning')
            selected_option = ""  # Set a default value or handle accordingly

        is_correct = selected_option == question['answer']
        submission = Submission(user_id=user_id,
                                question=question['text'],
                                selected_option=selected_option,
                                correct_option=question['answer'],
                                is_correct=is_correct)
        db.session.add(submission)
    db.session.commit()

    flash('Quiz submitted successfully!', 'success')
    return redirect(url_for('index'))


def execute_code(code):
    # Capture the output of the executed code
    output_capture = io.StringIO()
    with contextlib.redirect_stdout(output_capture):
        try:
            exec(code)
            return {'output': output_capture.getvalue(), 'error': None}
        except Exception as e:
            return {'output': None, 'error': str(e)}


@app.route('/submit_coding_test', methods=['POST'])
def submit_coding_test():
    user_id = session.get('user_id')

    # Ensure that only students who started a coding test can submit
    if not user_id or session.get('test_type') != 'coding':
        flash('Unauthorized submission or session expired.', 'error')
        return redirect(url_for('index'))

    # Retrieve the user and ensure they are a student
    user = User.query.get(user_id)
    if user.role != 'student':
        flash('Unauthorized access. Only students can submit coding tests.', 'error')
        return redirect(url_for('index'))

    # Process each coding question
    for question in coding_questions:
        answer = request.form.get(f'answer{question["id"]}')
        execution_result = execute_code(answer)
        
        # Check if execution_result is None or if 'output' key doesn't exist or is None
        if execution_result is None or 'output' not in execution_result or execution_result['output'] is None:
            is_correct = False  # Consider the answer incorrect if code execution fails
            output = "Code execution failed or produced no output"
        else:
            output = execution_result['output'].strip()
            is_correct = output == question['output'].strip()
        
        result = Result(user_id=user_id, question_id=question["id"], answer=answer, is_correct=is_correct, output=execution_result['output'])
        db.session.add(result)

    db.session.commit()
    flash('Coding test submitted successfully!', 'success')
    return redirect(url_for('view_results') if user.role == 'teacher' else url_for('thank_you'))


@app.route('/thank_you')
def thank_you():
    # A simple thank you page
    return render_template('thank_you.html')

@app.route('/coding_results')
def coding_results():
    user_id = session.get('user_id')

    if not user_id:
        flash('Unauthorized access. Please log in.', 'error')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    # Ensure only teachers can view the results
    if user.role != 'teacher':
        flash('Unauthorized access. Only teachers can view coding results.', 'error')
        return redirect(url_for('index'))

    # You can add a password check here if you store the teacher's session info or pass it securely
    # For demonstration, we are skipping password check here. Implement secure authentication methods for production

    # Fetch all results from the database
    results = Result.query.all()
    # Map the question texts to their IDs for display
    question_text_map = {q['id']: q['text'] for q in coding_questions}
    # Format results for the template
    formatted_results = [{'user': result.user, 'question_text': question_text_map[result.question_id], 'answer': result.answer, 'is_correct': result.is_correct} for result in results]

    return render_template('coding_results.html', results=formatted_results)


@app.route('/view_results')
def view_results():
    # Check if the user is logged in and is a teacher
    user_id = session.get('user_id')
    if not user_id:
        flash('You are not logged in.', 'error')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    if user.role != 'teacher':
        flash('Unauthorized access. Only teachers can view quiz results.', 'error')
        return redirect(url_for('index'))
    # Fetch all submissions from the database
    submissions = Submission.query.all()

    # Create a data structure to hold student results
    student_results = {}
    for submission in submissions:
        # This assumes 'user' is a backref from Submission to User
        user_id = submission.user_id
        if user_id not in student_results:
            student_results[user_id] = {
                'name': submission.user.name,
                'batch': submission.user.batch,
                'total_score': 0,
                'total_questions': 0,
                'correct_answers': 0,
                'answers': []
            }

        student_results[user_id]['answers'].append({
            'question': submission.question,
            'selected_option': submission.selected_option,
            'correct_option': submission.correct_option,
            'is_correct': submission.is_correct
        })

        # Increment the counters
        student_results[user_id]['total_questions'] += 1
        student_results[user_id]['correct_answers'] += int(submission.is_correct)
        student_results[user_id]['total_score'] = student_results[user_id]['correct_answers']  # Score is the number of correct answers

    # Convert to list to pass to template
    results = list(student_results.values())

    # Pass the results to the template
    return render_template('teacher_results.html', results=results)


@app.route('/select_results', methods=['POST'])
def select_results():
    result_type = request.form.get('resultType')
    print(f"Result type selected: {result_type}")  # Debugging line
    if result_type == 'mcq':
        print("Selected MCQ results")
        return redirect(url_for('view_results'))
    elif result_type == 'coding':
        print("Selected coding results")
        return redirect(url_for('coding_results'))
    else:
        flash('Invalid selection.', 'error')
        return redirect(url_for('index'))

@app.route('/verify_password', methods=['GET', 'POST'])
def verify_password():
    if request.method == 'POST':
        password = request.form['password']
        if password == TEACHER_PASSWORD:
            session['is_authenticated'] = True  # Mark the session as authenticated
            next_page = session.pop('next', '/results?type=mcq')  # Redirect to previously intended page or default to MCQ results
            return redirect(next_page)
        else:
            flash('Incorrect password. Please try again.', 'error')

    # If GET request or incorrect password, show the password form
    return render_template('verify_password.html')

from collections import defaultdict
@app.route('/results')
def results():

    if not session.get('is_authenticated'):
        session['next'] = request.url  # Store the intended URL to redirect after authentication
        return redirect(url_for('verify_password'))
    result_type = request.args.get('type', 'mcq')  # Default to 'mcq' if no type is specified

    if result_type == 'mcq':
        # Fetch MCQ results logic
            # Fetch all submissions from the database
        submissions = Submission.query.all()

        # Create a data structure to hold student results
        student_results = {}
        for submission in submissions:
            # This assumes 'user' is a backref from Submission to User
            user_id = submission.user_id
            if user_id not in student_results:
                student_results[user_id] = {
                    'name': submission.user.name,
                    'batch': submission.user.batch,
                    'total_score': 0,
                    'total_questions': 0,
                    'correct_answers': 0,
                    'answers': []
                }

            student_results[user_id]['answers'].append({
                'question': submission.question,
                'selected_option': submission.selected_option,
                'correct_option': submission.correct_option,
                'is_correct': submission.is_correct
            })

            # Increment the counters
            student_results[user_id]['total_questions'] += 1
            student_results[user_id]['correct_answers'] += int(submission.is_correct)
            student_results[user_id]['total_score'] = student_results[user_id]['correct_answers']  # Score is the number of correct answers

        # Convert to list to pass to template
        results = list(student_results.values())
        return render_template('teacher_results.html', results=results)

    elif result_type == 'coding':
        # Fetch coding results logic
        # Fetch all results from the database
        results = Result.query.all()

        # Map the question texts and correct answers to their IDs for display
        question_details_map = {q['id']: {'text': q['text'], 'correct_answer': q['output'].strip()} for q in coding_questions}

        student_results = defaultdict(lambda: {'user': None, 'results': [], 'total_correct': 0})

        for result in results:
            student_result = student_results[result.user_id]
            student_result['user'] = result.user  # User backref
            student_result['batch'] = result.user.batch  # Batch name
            question_details = question_details_map.get(result.question_id, {'text': "Question not found", 'correct_answer': "Answer not found"})
            student_result['results'].append({
                'question_text': question_details['text'],
                'answer': result.answer,
                'correct_answer': question_details['correct_answer'],
                'is_correct': result.is_correct,
                'student_output': result.output  # Include this line
            })
            if result.is_correct:
                student_result['total_correct'] += 1

        # Convert to list to pass to the template
        student_results_list = list(student_results.values())
        
        return render_template(
            'coding_results.html', 
            student_results=student_results_list, 
            total_questions=len(coding_questions)
        )
    return "Invalid result type specified", 400  # Handle invalid types


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables within an application context
    app.run(debug=True)
