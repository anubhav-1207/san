from flask import Flask, render_template_string, request, jsonify
from contextlib import redirect_stdout
import io

from src.scanner import Lexer
from src.parser import Parser
from src.evaluator import Evaluator


app = Flask(__name__)


# ============================================================
# AST SERIALIZER
# ============================================================

def serialize_ast(node):

    if node is None:
        return None

    if isinstance(node, (str, int, float, bool)):
        return node

    if isinstance(node, (list, tuple)):
        return [serialize_ast(item) for item in node]

    if hasattr(node, "__dict__"):

        result = {
            "name": node.__class__.__name__,
            "children": []
        }

        for key, value in node.__dict__.items():

            if hasattr(value, "__dict__"):

                result["children"].append({
                    "name": key,
                    "children": [serialize_ast(value)]
                })

            elif isinstance(value, (list, tuple)):

                children = []

                for index, item in enumerate(value):
                    if hasattr(item, "__dict__"):
                        children.append({
                            "name": f"[{index}]",
                            "children": [serialize_ast(item)]
                        })
                    else:
                        children.append({
                            "name": f"{key}[{index}]",
                            "value": str(item),
                            "children": []
                        })

                result["children"].extend(children)

            else:
                result["children"].append({
                    "name": key,
                    "value": str(value),
                    "children": []
                })

        return result

    return str(node)


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>San Playground</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 25px;
    background: #101114;
    color: #e5e5e5;
    font-family: Arial, sans-serif;
}

h1 {
    margin-bottom: 5px;
}

.subtitle {
    color: #888;
    margin-bottom: 25px;
}

.container {
    max-width: 1100px;
    margin: auto;
}

.panel {
    background: #181a20;
    border: 1px solid #292c35;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 20px;
}

.panel h2 {
    margin-top: 0;
    font-size: 17px;
}

#editor {
    border: 1px solid #343844;
    border-radius: 7px;
    overflow: hidden;
}

.cm-editor {
    min-height: 350px;
}

.cm-editor.cm-focused {
    outline: none;
}

.cm-scroller {
    overflow: auto;
    font-family: "JetBrains Mono", "Fira Code", monospace;
}

button {
    background: #6574e8;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    margin-top: 12px;
    cursor: pointer;
}

button:hover {
    background: #7887ff;
}

pre {
    background: #111318;
    border: 1px solid #292c35;
    padding: 14px;
    border-radius: 6px;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
}

#output {
    color: #a6e3a1;
}

#error {
    color: #f38ba8;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

th, td {
    padding: 10px;
    border-bottom: 1px solid #292c35;
    text-align: left;
}

th {
    color: #a6adc8;
}

td {
    color: #cdd6f4;
}

.token-type {
    color: #89b4fa;
}

#ast-tree {
    overflow-x: auto;
}

.ast-node {
    margin-left: 20px;
    border-left: 1px solid #454957;
    padding-left: 12px;
}

.ast-label {
    display: inline-block;
    margin: 4px 0;
    padding: 5px 9px;
    background: #252936;
    border-radius: 5px;
    color: #89b4fa;
    font-family: monospace;
    font-size: 13px;
}

.ast-value {
    color: #a6e3a1;
    margin-left: 8px;
    font-family: monospace;
    font-size: 12px;
}

details > summary {
    cursor: pointer;
    list-style: none;
}

details > summary::-webkit-details-marker {
    display: none;
}

details > summary::before {
    content: "▸ ";
    color: #888;
}

details[open] > summary::before {
    content: "▾ ";
}

</style>

</head>

<body>

<div class="container">

    <h1>San Playground</h1>
    <div class="subtitle">Write, execute and inspect San code.</div>


    <!-- EDITOR -->

    <div class="panel">

        <h2>Code Editor</h2>

        <div id="editor"></div>

        <button onclick="runCode()">Run Code</button>

    </div>


    <!-- OUTPUT -->

    <div class="panel">

        <h2>Output</h2>

        <pre id="output">Waiting for execution...</pre>

        <pre id="error" style="display:none"></pre>

    </div>


    <!-- TOKENS -->

    <div class="panel">

        <h2>Tokens</h2>

        <div id="tokens-container">
            <p style="color:#888">Run your code to see tokens.</p>
        </div>

    </div>


    <!-- AST -->

    <div class="panel">

        <h2>Abstract Syntax Tree</h2>

        <div id="ast-tree">
            <p style="color:#888">Run your code to see the AST.</p>
        </div>

    </div>

</div>


<!-- ========================================================
     CODEMIRROR
======================================================== -->

<script type="module">

import { basicSetup } from
    "https://esm.sh/codemirror@6.0.1";

import { EditorView, keymap } from
    "https://esm.sh/@codemirror/view@6.36.5";

import {
    StreamLanguage,
    HighlightStyle,
    syntaxHighlighting
} from
    "https://esm.sh/@codemirror/language@6.10.8";

import { tags } from
    "https://esm.sh/@lezer/highlight@1.2.1";

import { oneDark } from
    "https://esm.sh/@codemirror/theme-one-dark@6.1.2";


// ========================================================
// SAN KEYWORDS
// ========================================================

const sanKeywords = new Set([
    "dec",
    "const",
    "flux",
    "arr",

    "func",
    "return",

    "if",
    "else",
    "elif",

    "loop",
    "for",
    "in",

    "break",
    "skip",

    "Null",
    "use",

    "scantry",

    "int",
    "float",
    "str",
    "bool"
]);


// ========================================================
// SAN LANGUAGE MODE
// ========================================================

const sanMode = StreamLanguage.define({

    startState() {
        return {
            inBlockComment: false
        };
    },

    token(stream, state) {

        if (stream.eatSpace()) {
            return null;
        }


        // Block comments

        if (state.inBlockComment) {

            if (stream.match("*/")) {
                state.inBlockComment = false;
            } else {
                stream.next();
            }

            return "comment";
        }

        if (stream.match("/*")) {
            state.inBlockComment = true;
            return "comment";
        }


        // Single-line comments

        if (stream.match("//")) {
            stream.skipToEnd();
            return "comment";
        }


        // Strings

        if (stream.match(/"(?:\\.|[^"\\])*"?/)) {
            return "string";
        }

        if (stream.match(/'(?:\\.|[^'\\])*'?/)) {
            return "string";
        }


        // Numbers

        if (stream.match(/\d+(\.\d+)?/)) {
            return "number";
        }


        // Identifiers and keywords

        if (stream.match(/[a-zA-Z_][a-zA-Z0-9_]*/)) {

            const word = stream.current();

            if (word === "True" || word === "False") {
                return "bool";
            }

            if (sanKeywords.has(word)) {
                return "keyword";
            }

            return "variableName";
        }


        // Operators

        if (stream.match(
            /(\+\+|--|\*\*|>=|<=|==|!=|&&|\|\||[+\-*\/%=<>!])/
        )) {
            return "operator";
        }


        // Punctuation

        if (stream.match(/[(){}\[\],;:.]/)) {
            return "punctuation";
        }


        stream.next();

        return null;
    }

});


// ========================================================
// SYNTAX COLORS
// ========================================================

const sanHighlight = HighlightStyle.define([

    {
        tag: tags.keyword,
        color: "#c792ea"
    },

    {
        tag: tags.bool,
        color: "#ff9e64"
    },

    {
        tag: tags.number,
        color: "#f78c6c"
    },

    {
        tag: tags.string,
        color: "#c3e88d"
    },

    {
        tag: tags.comment,
        color: "#697098",
        fontStyle: "italic"
    },

    {
        tag: tags.operator,
        color: "#89ddff"
    },

    {
        tag: tags.punctuation,
        color: "#89ddff"
    },

    {
        tag: tags.variableName,
        color: "#f0f0f0"
    }

]);


// ========================================================
// EDITOR INITIALIZATION
// ========================================================

const editor = new EditorView({

    doc: `// Welcome to San

func fibonacci(n) {

    if (n <= 1) {
        return n;
    }

    return fibonacci(n - 1) + fibonacci(n - 2);
}

print(fibonacci(10));
`,

    extensions: [

        basicSetup,

        oneDark,

        sanMode,

        syntaxHighlighting(sanHighlight),

        EditorView.theme({

            "&": {
                fontSize: "14px"
            },

            ".cm-content": {
                fontFamily: "'JetBrains Mono', monospace"
            }

        }),

        keymap.of([

            {
                key: "Ctrl-Enter",

                run: () => {
                    runCode();
                    return true;
                }
            }

        ])

    ],

    parent: document.getElementById("editor")

});


// Make editor accessible to the rest of the page

window.sanEditor = editor;

</script>


<!-- ========================================================
     PLAYGROUND JAVASCRIPT
======================================================== -->

<script>


// ========================================================
// RUN CODE
// ========================================================

async function runCode() {

    const code = window.sanEditor.state.doc.toString();

    document.getElementById("output").textContent =
        "Running...";

    document.getElementById("error").style.display = "none";

    try {

        const response = await fetch("/run", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                code: code
            })

        });

        const data = await response.json();


        // Output

        document.getElementById("output").textContent =
            data.output || "";


        // Errors

        if (data.error) {

            const errorBox = document.getElementById("error");

            errorBox.style.display = "block";
            errorBox.textContent = data.error;

        }


        // Tokens

        renderTokens(data.tokens || []);


        // AST

        renderAST(data.ast);

    }

    catch (error) {

        document.getElementById("error").style.display = "block";

        document.getElementById("error").textContent =
            error.message;

    }

}

window.runCode = runCode;


// ========================================================
// TOKEN TABLE
// ========================================================

function renderTokens(tokens) {

    const container =
        document.getElementById("tokens-container");

    if (!tokens.length) {

        container.innerHTML =
            "<p style='color:#888'>No tokens found.</p>";

        return;
    }


    const table = document.createElement("table");

    const header = document.createElement("tr");

    ["#", "Type", "Value", "Line", "Column"].forEach(name => {

        const th = document.createElement("th");

        th.textContent = name;

        header.appendChild(th);

    });

    table.appendChild(header);


    tokens.forEach((token, index) => {

        const row = document.createElement("tr");

        const values = [

            index,

            token.type,

            token.value ?? "None",

            token.line,

            token.col ?? "None"

        ];

        values.forEach((value, i) => {

            const td = document.createElement("td");

            td.textContent = value;

            if (i === 1) {
                td.className = "token-type";
            }

            row.appendChild(td);

        });

        table.appendChild(row);

    });


    container.replaceChildren(table);

}


// ========================================================
// AST TREE
// ========================================================

function createASTNode(node) {

    if (node === null || node === undefined) {
        return document.createTextNode("None");
    }

    const wrapper = document.createElement("div");

    const details = document.createElement("details");

    details.open = true;

    const summary = document.createElement("summary");


    const label = document.createElement("span");

    label.className = "ast-label";

    label.textContent = node.name || "Node";

    summary.appendChild(label);


    if (node.value !== undefined) {

        const value = document.createElement("span");

        value.className = "ast-value";

        value.textContent = node.value;

        summary.appendChild(value);

    }


    details.appendChild(summary);


    if (node.children && node.children.length) {

        const children = document.createElement("div");

        children.className = "ast-node";

        node.children.forEach(child => {

            children.appendChild(createASTNode(child));

        });

        details.appendChild(children);

    }


    wrapper.appendChild(details);

    return wrapper;

}


function renderAST(ast) {

    const container =
        document.getElementById("ast-tree");

    container.replaceChildren();


    if (!ast) {

        container.textContent = "No AST available.";

        return;
    }


    container.appendChild(createASTNode(ast));

}

</script>

</body>
</html>
"""


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route("/")
def index():

    return render_template_string(HTML)


@app.route("/run", methods=["POST"])
def run():

    code = request.json.get("code", "")

    buffer = io.StringIO()

    try:

        # Lexer

        lexer = Lexer(code)

        tokens, error = lexer.tokenise()

        if error:
            raise Exception(error)


        # Parser

        parser = Parser(tokens)

        ast = parser.parse()


        # Evaluator

        evaluator = Evaluator()

        with redirect_stdout(buffer):
            evaluator.evaluate(ast)


        # Token serialization

        token_data = [

            {
                "type": str(token.type_),

                "value": str(token.token_value),

                "line": token.line,

                "col": token.col

            }

            for token in tokens

        ]


        # AST serialization

        ast_data = serialize_ast(ast)


        return jsonify({

            "output": buffer.getvalue(),

            "tokens": token_data,

            "ast": ast_data,

            "error": None

        })


    except Exception as error:

        return jsonify({

            "output": buffer.getvalue(),

            "tokens": [],

            "ast": None,

            "error": str(error)

        })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
