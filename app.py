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


# ==========================================================
# AST SERIALIZER
# ==========================================================

def serialize_ast(node):

    if node is None:
        return {
            "name": "None",
            "value": None,
            "children": []
        }

    # Lists
    if isinstance(node, (list, tuple)):

        return {
            "name": "Sequence",
            "children": [
                {
                    "name": f"[{index}]",
                    **serialize_ast(item)
                }
                for index, item in enumerate(node)
            ]
        }

    # Token objects
    if hasattr(node, "type_") and hasattr(node, "token_value"):

        return {
            "name": "Token: " + str(node.type_),
            "value": node.token_value,
            "attributes": {
                "line": node.line,
                "column": node.col
            },
            "children": []
        }

    # Primitive values
    if isinstance(node, (str, int, float, bool)):

        return {
            "name": str(node),
            "value": node,
            "children": []
        }

    # AST nodes
    if hasattr(node, "__dict__"):

        children = []

        for key, value in vars(node).items():

            # Nested AST nodes or tokens
            if hasattr(value, "__dict__"):

                children.append({
                    "name": key,
                    **serialize_ast(value)
                })

            # Lists and tuples
            elif isinstance(value, (list, tuple)):

                children.append({
                    "name": key,
                    **serialize_ast(value)
                })

            # Dictionaries
            elif isinstance(value, dict):

                children.append({
                    "name": key,
                    "children": [
                        {
                            "name": str(k),
                            **serialize_ast(v)
                        }
                        for k, v in value.items()
                    ]
                })

            # Primitive attributes
            else:

                children.append({
                    "name": key,
                    "value": value,
                    "children": []
                })

        return {
            "name": type(node).__name__,
            "children": children
        }

    return {
        "name": str(node),
        "children": []
    }


# ==========================================================
# HTML
# ==========================================================

HTML = """

<!DOCTYPE html>
<html>

<head>

<title>San Playground</title>

<script src="https://d3js.org/d3.v7.min.js"></script>

<style>

* {
    box-sizing: border-box;
}

body {

    max-width: 1100px;
    margin: auto;
    padding: 20px;

    background: #0f172a;
    color: #e2e8f0;

    font-family: sans-serif;
    font-size: 17px;

}

h1 {
    color: #60a5fa;
    font-size: 38px;
}

h2 {
    color: #93c5fd;
    margin-top: 35px;
}

textarea {

    width: 100%;
    height: 300px;

    background: #1e293b;
    color: #f8fafc;

    border: 1px solid #334155;
    border-radius: 10px;

    padding: 15px;

    font-family: monospace;
    font-size: 16px;

    resize: vertical;

}

textarea:focus {
    outline: none;
    border-color: #60a5fa;
}

button {

    background: #2563eb;
    color: white;

    border: none;
    border-radius: 8px;

    padding: 10px 20px;

    cursor: pointer;
    margin: 5px;

    font-size: 15px;

}

button:hover {
    background: #3b82f6;
}

pre {

    background: #1e293b;

    border: 1px solid #334155;
    border-radius: 10px;

    padding: 15px;

    white-space: pre-wrap;
    overflow-x: auto;

    font-family: monospace;
    font-size: 14px;

}


/* TOKEN TABLE */

#tokens-container {

    overflow-x: auto;

    background: #1e293b;

    border: 1px solid #334155;
    border-radius: 10px;

}

.token-table {

    width: 100%;
    border-collapse: collapse;

    font-family: monospace;
    font-size: 14px;

}

.token-table th,
.token-table td {

    padding: 11px;

    border-bottom: 1px solid #334155;

    text-align: left;

}

.token-table th {

    color: #93c5fd;
    background: #172554;

}

.token-table tr:hover {
    background: #334155;
}


/* AST */

#ast-container {

    width: 100%;
    height: 650px;

    background: #111c32;

    border: 1px solid #334155;
    border-radius: 10px;

    overflow: hidden;

}

#ast-container svg {
    display: block;
}

.link {

    fill: none;

    stroke: #64748b;
    stroke-width: 2px;

}

.node {
    cursor: pointer;
}

.node rect {

    stroke: #94a3b8;
    stroke-width: 1.5px;

    rx: 8;

}

.node text {

    fill: white;

    font-size: 12px;

    text-anchor: middle;

    pointer-events: none;

}

.node:hover rect {

    stroke: white;
    stroke-width: 2.5px;

}


/* INSPECTOR */

#node-info {

    background: #1e293b;

    border: 1px solid #334155;
    border-radius: 10px;

    padding: 15px;

    font-family: monospace;
    font-size: 14px;

    white-space: pre-wrap;
    overflow-wrap: anywhere;

    min-height: 60px;

}

</style>

</head>


<body>


<h1>San Playground</h1>

<p>Write and execute San programs.</p>


<textarea id="code">
// Please keep the numbers small.

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

<div id="tokens-container"></div>


<h2>Abstract Syntax Tree</h2>


<div>

<button onclick="zoomIn()">Zoom In</button>

<button onclick="zoomOut()">Zoom Out</button>

<button onclick="resetZoom()">Reset View</button>

</div>


<div id="ast-container"></div>


<h2>Node Inspector</h2>

<div id="node-info">

Click an AST node to inspect it.

</div>



<script>


// ==========================================================
// RUN CODE
// ==========================================================

async function runCode() {

    const code = document.getElementById("code").value;

    const output = document.getElementById("output");

    output.innerText = "Running...";

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

        output.innerText = data.output;

        renderTokens(data.tokens);

        renderAST(data.ast);

    }

    catch (error) {

        output.innerText = "Request Error: " + error;

    }

}



// ==========================================================
// TOKEN RENDERER
// ==========================================================

function renderTokens(tokens) {

    const container =
        document.getElementById("tokens-container");

    container.innerHTML = "";

    if (!tokens || tokens.length === 0) {
        container.innerText = "No tokens.";
        return;
    }

    const table = document.createElement("table");

    table.className = "token-table";

    const thead = document.createElement("thead");

    thead.innerHTML = `
        <tr>
            <th>#</th>
            <th>Type</th>
            <th>Value</th>
            <th>Line</th>
            <th>Column</th>
        </tr>
    `;

    const tbody = document.createElement("tbody");

    tokens.forEach((token, index) => {

        const row = document.createElement("tr");

        const values = [
            index,
            token.type,
            token.value ?? "—",
            token.line,
            token.col ?? "—"
        ];

        values.forEach(value => {

            const cell = document.createElement("td");

            cell.textContent = value;

            row.appendChild(cell);

        });

        tbody.appendChild(row);

    });

    table.appendChild(thead);

    table.appendChild(tbody);

    container.appendChild(table);

}



// ==========================================================
// AST RENDERER
// ==========================================================

let svg;
let zoom;

function renderAST(ast) {

    const container =
        document.getElementById("ast-container");

    container.innerHTML = "";

    document.getElementById("node-info").innerText =
        "Click an AST node to inspect it.";

    if (!ast) {
        return;
    }

    const width = container.clientWidth;
    const height = container.clientHeight;


    // Create hierarchy

    const root = d3.hierarchy(ast);


    // Tree layout

    const tree = d3.tree()
        .nodeSize([190, 115]);

    tree(root);


    const nodes = root.descendants();
    const links = root.links();


    // Calculate dimensions

    const minX = d3.min(nodes, d => d.x);
    const maxX = d3.max(nodes, d => d.x);
    const maxY = d3.max(nodes, d => d.y);

    const svgWidth = Math.max(
        width,
        maxX - minX + 250
    );

    const svgHeight = Math.max(
        height,
        maxY + 150
    );


    // SVG

    svg = d3.select(container)
        .append("svg")
        .attr("width", svgWidth)
        .attr("height", svgHeight);


    const layer = svg.append("g");


    // Zoom behaviour

    zoom = d3.zoom()
        .scaleExtent([0.15, 3])
        .on("zoom", event => {

            layer.attr(
                "transform",
                event.transform
            );

        });

    svg.call(zoom);


    // Position tree

    layer.attr(
        "transform",
        `translate(${svgWidth / 2}, 60)`
    );


    // Connectors

    layer.selectAll(".link")

        .data(links)

        .enter()

        .append("path")

        .attr("class", "link")

        .attr("d", d => {

            return `
                M ${d.source.x} ${d.source.y}
                C ${d.source.x} ${(d.source.y + d.target.y) / 2},
                  ${d.target.x} ${(d.source.y + d.target.y) / 2},
                  ${d.target.x} ${d.target.y}
            `;

        });


    // Node colours

    function getColor(name) {

        if (name.includes("Program"))
            return "#be185d";

        if (name.includes("Number"))
            return "#2563eb";

        if (name.includes("Binary"))
            return "#7c3aed";

        if (name.includes("Func"))
            return "#0891b2";

        if (name.includes("If"))
            return "#b45309";

        if (name.includes("While"))
            return "#047857";

        if (name.includes("Token"))
            return "#475569";

        return "#334155";

    }


    // Nodes

    const node = layer.selectAll(".node")

        .data(nodes)

        .enter()

        .append("g")

        .attr("class", "node")

        .attr(
            "transform",
            d => `translate(${d.x},${d.y})`
        );


    node.append("rect")

        .attr("x", -75)

        .attr("y", -25)

        .attr("width", 150)

        .attr("height", 50)

        .attr("fill", d => getColor(d.data.name));


    // Node labels

    node.append("text")

        .attr("dy", 5)

        .text(d => {

            let name = d.data.name;

            if (d.data.value !== undefined &&
                d.data.value !== null) {

                name += ": " + d.data.value;

            }

            return name.length > 23
                ? name.substring(0, 20) + "..."
                : name;

        });


    // Inspector

    node.on("click", function(event, d) {

        document.getElementById("node-info").innerText =
            JSON.stringify(d.data, null, 4);

    });


    // Initial positioning

    const scale = Math.min(
        1,
        width / svgWidth
    );

    const initialTransform = d3.zoomIdentity

        .translate(
            width / 2,
            60
        )

        .scale(scale);

    svg.call(
        zoom.transform,
        initialTransform
    );

}



// ==========================================================
// ZOOM CONTROLS
// ==========================================================

function zoomIn() {

    if (!svg || !zoom) return;

    svg.transition()
        .call(zoom.scaleBy, 1.3);

}


function zoomOut() {

    if (!svg || !zoom) return;

    svg.transition()
        .call(zoom.scaleBy, 0.7);

}


function resetZoom() {

    if (!svg || !zoom) return;

    svg.transition()
        .call(
            zoom.transform,
            d3.zoomIdentity.translate(
                document.getElementById(
                    "ast-container"
                ).clientWidth / 2,
                60
            )
        );

}



// ==========================================================
// KEYBOARD SHORTCUTS
// ==========================================================

const editor = document.getElementById("code");


editor.addEventListener("keydown", function(e) {

    if (e.key === "Tab") {

        e.preventDefault();

        const start = this.selectionStart;
        const end = this.selectionEnd;

        this.value =
            this.value.substring(0, start)
            + "    "
            + this.value.substring(end);

        this.selectionStart =
            this.selectionEnd =
            start + 4;

    }


    if (e.ctrlKey && e.key === "Enter") {

        e.preventDefault();

        runCode();

    }

});


// ==========================================================
// INITIAL EXECUTION
// ==========================================================

window.onload = runCode;


</script>

</body>

</html>

"""


# ==========================================================
# ROUTES
# ==========================================================

@app.route("/")
def home():

    return render_template_string(HTML)


@app.route("/run", methods=["POST"])
def run():

    code = request.json["code"]

    try:

        # Lexer

        lexer = Lexer(code)

        tokens = lexer.tokenise()


        # Parser

        parser = Parser(tokens)

        ast = parser.parse()


        # Evaluator

        evaluator = Evaluator()

        buffer = io.StringIO()

        with redirect_stdout(buffer):

            evaluator.evaluate(ast)

        output = buffer.getvalue()


        # Token serialization

        token_data = [

            {
                "type": str(token.type_),
                "value": token.token_value,
                "line": token.line,
                "col": token.col
            }

            for token in tokens

        ]


        # AST serialization

        ast_data = serialize_ast(ast)


        return jsonify({

            "output": output,

            "tokens": token_data,

            "ast": ast_data

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

            "tokens": [],

            "ast": None

        })


    except Exception as e:

        return jsonify({

            "output": "Internal Error:\\n" + str(e),

            "tokens": [],

            "ast": None

        })


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    app.run(debug=True)
