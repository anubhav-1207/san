from flask import Flask, render_template_string, request, jsonify
from contextlib import redirect_stdout
import io

from src.scanner import (
    Lexer,
    InvalidTokenError,
    UnterminatedStringLiteral,
    InvalidIdentifier,
    InvalidFloatLiteral,
    UnintialisedStringLiteral
)


from src.parser import Parser
from src.interpreter import Evaluator

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>San Playground</title>

<style>

body{
    max-width:1000px;
    margin:auto;
    padding:20px;

    background:#0f172a;
    color:#e2e8f0;

    font-family:sans-serif;
    font-size:18px;
}

h1{
    color:#60a5fa;
    font-size:42px;
}

h2{
    color:#93c5fd;
    font-size:28px;
}

textarea{
    width:100%;
    height:300px;

    background:#1e293b;
    color:#f8fafc;

    border:1px solid #334155;
    border-radius:10px;

    padding:15px;
    box-sizing:border-box;

    font-family:monospace;
    font-size:18px;

    tab-size:4;
}

textarea:focus{
    outline:none;
    border-color:#60a5fa;
}

button{
    background:#2563eb;
    color:white;

    border:none;
    border-radius:8px;

    padding:10px 20px;

    cursor:pointer;

    margin-right:10px;

    font-size:16px;
}

button:hover{
    background:#3b82f6;
}

pre{
    background:#1e293b;

    border:1px solid #334155;
    border-radius:10px;

    padding:15px;

    white-space:pre-wrap;
    overflow-x:auto;

    font-family:monospace;
    font-size:17px;
}

</style>

</head>

<body>

<h1>San Playground - Type Your Code</h1>

<textarea id="code">
//Please keep the numbers small since this is executing on a browser, it might be very slow for large numbers, recommended - n < 20

func fib(n){
    if (n <= 1){
        return n
    }

    return fib(n-1)+fib(n-2)
}

stdout(fib(10))


</textarea>

<br><br>

<button onclick="runCode()">
Run - CTRL + ENTER
</button>

<h2>Output</h2>
<pre id="output"></pre>

<h2>Tokens</h2>
<pre id="tokens"></pre>

<h2>AST</h2>
<pre id="ast"></pre>

<script>

async function runCode(){

    let code =
        document.getElementById("code").value;

    let response =
        await fetch("/run",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                code:code
            })
        });

    let data = await response.json();

    document.getElementById("output").innerText =
        data.output;

    document.getElementById("tokens").innerText =
        data.tokens;

    document.getElementById("ast").innerText =
        data.ast;
}

const editor = document.getElementById("code");

editor.addEventListener("keydown", function(e){

    if (e.key === "Tab"){

        e.preventDefault();

        const start = this.selectionStart;
        const end = this.selectionEnd;

        this.value =
            this.value.substring(0,start)
            + "    "
            + this.value.substring(end);

        this.selectionStart =
            this.selectionEnd =
            start + 4;
    }

    if (e.ctrlKey && e.key === "Enter"){

        e.preventDefault();

        runCode();
    }

});

window.onload = function(){
    runCode();
}

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/run", methods=["POST"])
def run():

    code = request.json["code"]

    try:

        lexer = Lexer(code)
        tokens = lexer.tokenise()

        parser = Parser(tokens)
        ast = parser.parse()

        evaluator = Evaluator()

        buffer = io.StringIO()

        with redirect_stdout(buffer):
            evaluator.evaluate(ast)

        output = buffer.getvalue()

        return jsonify({
            "output": output,
            "tokens": "\n".join(map(str, tokens)),
            "ast": repr(ast)
        })

    except (
        InvalidTokenError,
        UnterminatedStringLiteral,
        InvalidIdentifier,
        InvalidFloatLiteral,
        UnintialisedStringLiteral
    ) as e:

        return jsonify({
            "output": str(e),
            "tokens": "",
            "ast": ""
        })

    except Exception as e:

        return jsonify({
            "output": "Internal Error:\\n" + str(e),
            "tokens": "",
            "ast": ""
        })


if __name__ == "__main__":
    app.run(debug=True)