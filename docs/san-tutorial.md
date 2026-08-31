## The Book Of Wonders For San
This tutorial teaches you how to write programs in San step by step.

San is a dynamically typed, strongly typed programming language designed for beginners to just get started into programming 

---
### Prerequisites
- You must know how to open a file 
- You must know how to open a terminal 
- You must have Python or San installed in your system
----
### How to run code
Your programs must end with a `.san` file extension. You can run the program in two ways:
#### Using Python (recommended)
Navigate to the San folder using commands for your respective operating systems. Then:
```bash
python main.py example.san
```

#### Using San Binary
> Binaries are still in alpha stage and maybe unstable.
```bash
san example.san
```
---
### Our First San Program
Create a file named `hello.san`, then type the following code and run it. Worry not about what it means right now!
```c
stdout("Hello World")
```
```c
Output: Hello World
```

In San, we use `stdout()` to output something to the terminal. Here `stdout()` is a function that takes "hello world" as input. We will talk about functions later.
Think of it as a machine that takes in energy and gives out a product. 

---

### Variables
Variables can be defined as containers that store something. In a more advanced view, a variable is a name bound to a storage location or value, rather than just an alias for a memory address.

In San, we can store two types of variables, one we can change according to our needs (mutable), or the ones we can't (immutable).

To declare mutable variables, we use the `dec` keyword.
```c
dec name = "San"
```
To declare immutable variables, we use the `const` keyword.
```c
const PI = 3.14159
```
Here, `name` and `PI` are the variable names, while `San` and `3.14159` are their values respectively.

We can see the value of a variable using:
```c
stdout(name)
stdout(PI)
```
This should output:
```
San
3.14159
```

### Data Types
San supports 5 data types. 
1. **Integers:** Numbers ranging from positive infinity to negative infinity. Example: `-19273`, `8`, `0`, `-2`, `8273`
2. **Floats:** Numbers with a floating point. Example: `10.0`, `10.9`, `100.9`, `76.3`, `-72.5`
3. **Strings**: Data types enclosed within " or '. Example: `"San"`,`"0.29"`,`"72"`
4. **Booleans**: This can either be `True` or `False`
5. **Arrays**: A sequence of the above four data types. Example: `[1,2,3,"apple",True,2.71]`

San also has a 6th data type that we will talk about in the Standard Libraries chapter.

### Comments
Comments in a programming language can be defined as a sequence that is ignored. Example:
```c
stdout("Hello San") //this part of text is ignored
```
```
output: Hello San
```
It can be used to document code details. San also supports multiline comments.
```c
stdout("I Like Turtles")
/*This whole part 
Will be ignored 
even though it spans three lines*/
```
```
output: I Like Turtles
```




FRAME THIS BETTER WAY and make corrections or add things needed to be added

Here’s a cleaner, more correct version of your intro, with a few fixes and additions.

## The Book of Wonders for San

This tutorial teaches you how to write programs in **San**, step by step.

San is a **dynamically typed** and **strongly typed** programming language designed to help beginners get started with programming.

***

### Prerequisites

Before you begin, you should:

- Know how to create and open files.
- Know how to open and use a terminal.
- Have **Python** or **San** installed on your system.

***

### How to Run Code

San programs must be saved with the `.san` file extension.

You can run a San program in two ways:

#### Using Python
Navigate to the San folder in your terminal, then run:

```bash
python main.py example.san
```

#### Using the San Binary
> The binary is still in alpha and may be unstable.

```bash
san example.san
```

***

### Our First San Program

Create a file named `hello.san`, then type:

```c
stdout("Hello, World!")
```

Expected output:

```c
Hello, World!
```

This can also be written as:
```c
stdout("Hello World");
```
Or even 
```c
stdout("Hello World");;;;;;;;;;;
```
You decide the number of semi-colons, or entirely skip them.


In San, `stdout()` is used to print output to the terminal. It takes a value as input and displays it. We will learn more about functions later.

Think of it like a machine that takes input and produces output.

***

### Variables

Variables can be thought of as names that refer to values.

In a more advanced view, a variable is a **name bound to a value or storage location**, rather than simply an alias for a memory address.

San supports two kinds of variables:

- **Mutable variables**, which can be changed.
- **Immutable variables**, which cannot be changed after assignment.

To declare a mutable variable, use the `dec` keyword:

```c
dec name = "San"
```

To declare an immutable variable, use the `const` keyword:

```c
const PI = 3.14159
```

Here, `name` and `PI` are variable names, while `"San"` and `3.14159` are their values.

You can print the value of a variable using:

```c
stdout(name)
stdout(PI)
```

Expected output:

```c
San
3.14159
```

***

### Data Types

San supports the following data types:

1. **Integers**: Whole numbers, such as `-19273`, `8`, `0`, `8273`.
2. **Floats**: Numbers with a decimal point, such as `10.0`, `10.9`, `100.9`, `-72.5`.
3. **Strings**: Text enclosed in single or double quotes, such as `"San"` or `'hello'`.
4. **Booleans**: Logical values, either `True` or `False`.
5. **Arrays**: Ordered collections of values, such as `[1, 2, 3, "apple", True, 2.71]`.

San also has a sixth data type, which we will discuss in the **Standard Library** chapter.

***

### Comments

Comments are parts of code that are ignored by the interpreter. They are used to explain code or leave notes for yourself and others.

Single-line comment:

```c
stdout("Hello, San") // this part is ignored
```

Output:

```c
Hello, San
```

Multi-line comment:

```c
stdout("I like turtles")
/* This whole part
will be ignored
even if it spans multiple lines */
```

Output:

```c
I like turtles
```

***
