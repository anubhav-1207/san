## The San Programming Language: The Official Beginner's Guide

### Preface
Welcome to the official manual for San, a programming language designed to be readable, concise, and expressive.

Programming is the process of giving precise instructions to a computer to solve problems, automate tasks, or build applications. San provides an approachable syntax that allows you to translate human logic into executable computer code without unnecessary complexity.

Whether you have never written a single line of code or are looking for a clean reference, this book will take you from absolute zero to writing complete, functional San programs.

---
### Chapter 1: Running Your First Program
San source code files are saved with the .san file extension. Any plain text editor can be used to write San programs.

**1.1 Creating a `.san` File**

To write a program:
 * Open a text editor such as VS Code.
 * Type your San code.
 * Save the file with a `.san` extension (for example, `main.san`).

**1.2 Executing a `.san` File**

To run a San file through the San interpreter, open your system terminal or command prompt and execute the interpreter alongside your file name:
```bash
python main.py main.san
```

**1.3 Your First Program**
By convention, every programmer's first step is writing a program that displays a greeting. In San, the `stdout` command outputs information to the terminal screen.
```c
// File: main.san
stdout("Hello, World!");
```
When executed, the interpreter processes `main.san` and outputs:
```
Hello, World!
```
---
**Chapter 2: Variables & Constants**
Programs require a mechanism to store and recall data during execution. San provides three primary keywords for managing memory: `dec`, `const`, and `flux`.

**2.1 Declaring Variables (dec)**

Use `dec` (short for declare) to create a variable whose value can be altered later.

```c
dec playerScore = 0;
dec playerName = "Alice";
```
**2.2 Reassigning Variables (flux)**
In San, once a variable is created with `dec`, you cannot re-declare it with `dec.` To modify its contents later, you must explicitly use the `flux` keyword.
```c
dec currentLevel = 1;
// Update variable value
flux currentLevel = 2;
```

**2.3 Constants (const)**
When a value must remain fixed throughout the program execution, declare it with `const`. Attempting to modify a constant using `flux` will trigger a `runtime error`.

```c
const MAX_PLAYERS = 4;
const PI = 3.14159;
```

> Note: San does not allow arrays to be declared as constants; arrays must always be declared using `dec`.
> 
**Chapter 3: Data Types**

Data in San is categorized into distinct primitive types:
| Data Type | Keyword | Description | Example |
|---|---|---|---|
| Integer | `int` | Whole numbers (positive, negative, or zero) | 42, -10 |
| Float | `float` | Fractional numbers containing a decimal point | 3.1415, -0.5 |
| String | `str` | Text enclosed in double or single quotes | "San Language", 'Hello' |
| Boolean | `bool` | Logical truth values | True, False |
| Null | `Null` | Represents the deliberate absence of a value | Null |

```c
dec age = 21;             // int
dec rating = 4.8;         // float
dec title = "Developer";  // str
dec isOnline = True;      // bool
dec extraData = Null;     // Null
```

---
### Chapter 4: Operators & Expressions

Operators allow you to manipulate variables and values to evaluate new data.

**4.1 Arithmetic Operators**
San supports core mathematical operations:
```c
dec a = 10;
dec b = 3;

dec sum = a + b;       // 13 (Addition)
dec diff = a - b;      // 7  (Subtraction)
dec product = a * b;   // 30 (Multiplication)
dec quotient = a / b;  // 3  (Division)
dec power = a ** b;    // 1000 (Exponentiation)
```
**4.2 Comparison Operators**

Comparison operators evaluate expressions and return a boolean result (True or False):
 * `==` Equal to
 * `!=` Not equal to
 * `>` Greater than
 * `<` Less than
 * `>=` Greater than or equal to
 * `<=` Less than or equal to
```c
dec result = (10 > 5); // True
```

**4.3 Logical Operators**

Combine multiple boolean evaluations using logical operators:
 * && Logical AND (Returns True if both sides are true)
 * || Logical OR (Returns True if at least one side is true)
 * ! Logical NOT (Inverts boolean truth value)
dec hasKey = True;
dec doorUnlocked = False;

dec canEnter = hasKey && !doorUnlocked; // True

Chapter 5: Input & Output (I/O)
Interactive programs require communicating with the user by writing text to the screen or accepting data from the keyboard.
5.1 Standard Output (stdout)
The stdout() built-in command accepts expressions or variables and outputs their evaluated result.
dec username = "Alex";
stdout("Current User:");
stdout(username);

5.2 Reading User Input (scan)
The scan() command pauses program execution and waits for the user to type input. You must specify the destination variable and the data type to convert the input into (int, float, str, bool).
stdout("Please enter your target score:");

dec targetScore = 0;
scan(targetScore: int);

stdout("Target set to:");
stdout(targetScore);

Chapter 6: Control Structures
Control structures enable conditional logic, allowing your program to execute specific code blocks depending on runtime evaluations.
6.1 Conditional Statements (if, elif, else)
In San, conditions must be wrapped in parentheses (), and code blocks must be enclosed in curly braces {}.
dec userAge = 18;

if (userAge >= 21) {
    stdout("Access Granted: Full");
} elif (userAge >= 18) {
    stdout("Access Granted: Restricted");
} else {
    stdout("Access Denied");
}

Chapter 7: Repetition & Loops
Loops repeat execution of code blocks automatically as long as specified conditions remain valid.
7.1 while Loops
A while loop continues executing as long as its condition evaluates to True.
dec iteration = 1;

while (iteration <= 3) {
    stdout(iteration);
    flux iteration = iteration + 1;
}

7.2 Terminating Loops Early (break)
You can exit a loop immediately using the break keyword.
dec counter = 0;

while (counter < 10) {
    if (counter == 4) {
        break; // Exit loop when counter hits 4
    }
    stdout(counter);
    flux counter = counter + 1;
}

7.3 for Loops
Use a for loop to iterate sequentially through elements in a sequence.
dec numbers = [10, 20, 30];

for val in numbers {
    stdout(val);
}

Chapter 8: Arrays, Indexing & Slicing
Arrays store ordered lists of data elements wrapped in square brackets [].
8.1 Indexing
Array elements are zero-indexed, meaning the first element is accessed at index 0.
dec inventory = ["Sword", "Shield", "Potion"];

stdout(inventory[0]); // Prints "Sword"
stdout(inventory[2]); // Prints "Potion"

8.2 Array Slicing
San supports extracting sub-sections of arrays using standard slice syntax [start:end:step].
dec values = [10, 20, 30, 40, 50, 60];

// Extract from index 1 up to index 4 with a step of 1
dec subArray = values[1:4:1];

stdout(subArray); // Prints [20, 30, 40]

Chapter 9: Functions
Functions allow you to group reusable code into logical blocks that perform specific sub-tasks.
9.1 Defining and Calling Functions
Define functions with the func keyword. Pass parameters inside parentheses (), and use return to pass back a final result.
// Function definition
func calculateArea(width, height) {
    dec area = width * height;
    return area;
}

// Function call
dec totalArea = calculateArea(5, 10);
stdout(totalArea); // Prints 50

Chapter 10: Standard Libraries
San includes built-in library modules to handle specialized math operations, random value generation, and timing functions. Modules are loaded into your script using the use keyword.
10.1 Importing Libraries (use)
use math;
use random;
use time;

Once imported, library functions become immediately accessible within your script's execution environment.
Complete Example Program
To finish our guide, here is a complete San program that combines variables, loops, arrays, conditional statements, and functions into a single executable script:
// File: demo.san

// Import required built-in modules
use math;

// Define a helper function
func calculateAverage(scores) {
    dec sum = 0;
    for score in scores {
        flux sum = sum + score;
    }
    return sum / 3;
}

// Main execution code
dec studentName = "Sam";
dec examScores = [85, 90, 95];

stdout("Processing report for:");
stdout(studentName);

dec finalAverage = calculateAverage(examScores);

stdout("Final Average:");
stdout(finalAverage);

if (finalAverage >= 90) {
    stdout("Status: Passed with Distinction");
} else {
    stdout("Status: Passed");
}

Chapter 11: Recursion
11.1 What is Recursion?
In Chapter 9, you learned how to define and call functions to execute reusable blocks of code. Recursion is a programming technique where a function calls itself to solve a problem by breaking it down into smaller, simpler sub-problems.
Think of recursion like a set of Russian nesting dolls:
 * To reach the tiny doll in the center, you open a large doll.
 * Inside is a slightly smaller doll.
 * You keep opening smaller dolls until you reach the smallest doll that cannot be opened anymore.
In San, when a function calls itself, the interpreter creates a new execution scope (environment) for that specific call. Once the inner function finishes and returns a value, the answer passes back up through each caller.
11.2 The Two Rules of Recursion
Every recursive function must have two essential parts:
 * The Base Case (The Stopping Condition): A conditional if check that stops the function from calling itself again. Without a base case, the function will call itself infinitely until the program runs out of memory.
 * The Recursive Case: The part of the function where it calls itself, passing a smaller or simpler input so it eventually reaches the base case.
11.3 A Step-by-Step Example: Countdown
Let's look at a simple recursive program that counts down from a given number to 1.
// File: recursion_demo.san

func countdown(number) {
    // 1. Base Case: Stop when number reaches 0
    if (number <= 0) {
        stdout("Blastoff!");
        return Null;
    }
    
    // Output current number
    stdout(number);
    
    // 2. Recursive Case: Call countdown with a smaller number
    return countdown(number - 1);
}

// Call the function starting at 3
countdown(3);

How San Executes This Code:
 * countdown(3) runs, prints 3, and calls countdown(2).
 * countdown(2) runs in its own new scope, prints 2, and calls countdown(1).
 * countdown(1) runs, prints 1, and calls countdown(0).
 * countdown(0) hits the Base Case (number <= 0), prints "Blastoff!", and returns Null.
Output:
3
2
1
Blastoff!

11.4 Calculating Mathematical Factorials
A classic use of recursion in mathematics is calculating the factorial of a number (written as n!).
The factorial of 5 (5!) is 5 \times 4 \times 3 \times 2 \times 1 = 120.
 * Base Case: The factorial of 1 (or 0) is 1.
 * Recursive Case: n! = n \times (n - 1)!
Here is how to write a factorial calculator in San:
// File: factorial.san

func factorial(n) {
    // Base Case
    if (n <= 1) {
        return 1;
    }
    
    // Recursive Case
    return n * factorial(n - 1);
}

// Compute 5!
dec result = factorial(5);

stdout("Factorial of 5 is:");
stdout(result);

When executed with python main.py factorial.san, the output is:
Factorial of 5 is:
120

11.5 Recursion vs. Loops
In San, both loops (while/for) and recursion allow you to repeat actions.
 * Use loops when you need to perform a simple sequence of steps a known number of times.
 * Use recursion when dealing with problems that naturally divide into sub-problems (like searching through nested arrays, tree structures, or calculating mathematical sequences).