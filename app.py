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


def serialize_ast(node):

    if node is None:
        return None

    if isinstance(node, (str, int, float, bool)):
        return node

    if isinstance(node, list):
        return [
            serialize_ast(item)
            for item in node
        ]

    if isinstance(node, tuple):
        return [
            serialize_ast(item)
            for item in node
        ]

    # Handle token objects
    if hasattr(node, "token_type") and hasattr(node, "token_value"):
        return {
            "type": "Token",
            "value": str(node.token_value),
            "token_type": str(node.token_type)
        }

    if hasattr(node, "__dict__"):

        return {
            "type": type(node).__name__,
            "children": {
                key: serialize_ast(value)
                for key, value in vars(node).items()
            }
        }

    return str(node)


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
    max-width: 1200px;
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

    min-height: 40px;
}

#ast-container {

    background: #111c32;

    border: 1px solid #334155;
    border-radius: 10px;

    width: 100%;
    height: 600px;

    overflow: hidden;

    position: relative;
}

#ast-container svg {
    width: 100%;
    height: 100%;
}

.node rect {
    stroke-width: 1.5px;
    rx: 8;
}

.node text {
    font-size: 13px;
    fill: white;
    text-anchor: middle;
    pointer-events: none;
}

.link {
    fill: none;
    stroke: #64748b;
    stroke-width: 2px;
}

.node {
    cursor: pointer;
}

.node:hover rect {
    stroke: white;
    stroke-width: 2.5px;
}

#node-info {

    margin-top: 15px;

    padding: 15px;

    background: #1e293b;

    border: 1px solid #334155;
    border-radius: 10px;

    font-family: monospace;
    font-size: 14px;

    min-height: 50px;
    overflow-wrap: anywhere;
}

.controls {
    margin: 10px 0;
}

</style>

</head>


<body>

<h1>San Playground</h1>

<p>Write and execute San programs.</p>


<textarea id="code">
//Please keep the numbers small since this is executing on a browser.

func fib(n){

    if (n <= 1){
        return n
    }

    return fib(n-1)+fib(n-2)
}

stdout(fib(10))

</textarea>


<br>

<button onclick="runCode()">
Run - CTRL + ENTER
</button>


<h2>Output</h2>

<pre id="output"></pre>


<h2>Tokens</h2>

<pre id="tokens"></pre>


<h2>Abstract Syntax Tree</h2>

<div class="controls">

    <button onclick="zoomIn()">Zoom In</button>

    <button onclick="zoomOut()">Zoom Out</button>

    <button onclick="resetZoom()">Reset View</button>

</div>


<div id="ast-container"></div>


<h2>Node Inspector</h2>

<div id="node-info">

Click an AST node to inspect its properties.

</div>


<script>

let currentTransform = d3.zoomIdentity;


async function runCode() {

    const code =
        document.getElementById("code").value;

    const output =
        document.getElementById("output");

    const tokens =
        document.getElementById("tokens");

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

        tokens.innerText = data.tokens;

        if (data.ast) {
            renderAST(data.ast);
        } else {
            document.getElementById(
                "ast-container"
            ).innerHTML = "";
        }

    }

    catch (error) {

        output.innerText =
            "Request Error: " + error;

    }

}


// AST RENDERER

function renderAST(ast) {

    const container =
        document.getElementById("ast-container");

    container.innerHTML = "";

    if (!ast) {
        return;
    }

    const width = container.clientWidth;
    const height = container.clientHeight;


    // Convert serialized AST into D3 hierarchy

    function convert(node, name = "Root") {

        if (node === null || node === undefined) {

            return {
                name: name + ": null",
                data: node
            };

        }

        if (Array.isArray(node)) {

            return {
                name: name,
                data: node,
                children: node.map(
                    (item, index) =>
                        convert(item, "[" + index + "]")
                )
            };

        }

        if (typeof node === "object") {

            if (node.type === "Token") {

                return {
                    name: "Token: " + node.value,
                    data: node
                };

            }

            const children = [];

            if (node.type) {

                Object.entries(node.children || {})
                    .forEach(([key, value]) => {

                        children.push(
                            convert(value, key)
                        );

                    });

                return {

                    name: node.type,

                    data: node,

                    children: children

                };

            }

            Object.entries(node).forEach(
                ([key, value]) => {

                    children.push(
                        convert(value, key)
                    );

                }
            );

            return {
                name: name,
                data: node,
                children: children
            };

        }

        return {

            name: name + ": " + String(node),

            data: node

        };

    }


    const hierarchy = d3.hierarchy(
        convert(ast)
    );


    // Tree layout

    const tree = d3.tree()
        .nodeSize([180, 110]);

    tree(hierarchy);


    const nodes = hierarchy.descendants();

    const links = hierarchy.links();


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


    const svg = d3.select(container)
        .append("svg")
        .attr("width", svgWidth)
        .attr("height", svgHeight);


    const zoomLayer = svg.append("g");


    const zoom = d3.zoom()
        .scaleExtent([0.2, 3])
        .on("zoom", event => {

            zoomLayer.attr(
                "transform",
                event.transform
            );

            currentTransform = event.transform;

        });


    svg.call(zoom);


    // Center tree

    zoomLayer.attr(
        "transform",
        "translate(" + (svgWidth / 2) + ",60)"
    );


    // Connectors

    zoomLayer.selectAll(".link")

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


    // Nodes

    const node = zoomLayer.selectAll(".node")

        .data(nodes)

        .enter()

        .append("g")

        .attr("class", "node")

        .attr(
            "transform",
            d => `translate(${d.x},${d.y})`
        );


    function nodeColor(d) {

        const name = d.data.name;

        if (name.includes("Number")) return "#2563eb";

        if (name.includes("Binary")) return "#7c3aed";

        if (name.includes("Func")) return "#0891b2";

        if (name.includes("If")) return "#b45309";

        if (name.includes("While")) return "#047857";

        if (name.includes("Program")) return "#be185d";

        return "#334155";

    }


    node.append("rect")

        .attr("x", -70)

        .attr("y", -25)

        .attr("width", 140)

        .attr("height", 50)

        .attr("fill", d => nodeColor(d))

        .attr("stroke", "#94a3b8");


    node.append("text")

        .attr("dy", 5)

        .text(d => {

            const name = d.data.name;

            return name.length > 20
                ? name.substring(0, 18) + "..."
                : name;

        });


    // Node inspector

    node.on("click", function(event, d) {

        const info =
            document.getElementById("node-info");

        info.innerText = JSON.stringify(
            d.data,
            null,
            4
        );

    });


    // Fit tree initially

    const initialScale = Math.min(
        1,
        width / (svgWidth + 100)
    );

    const initialTransform = d3.zoomIdentity

        .translate(
            width / 2,
            60
        )

        .scale(initialScale);


    svg.call(
        zoom.transform,
        initialTransform
    );

}


function zoomIn() {

    d3.select("#ast-container svg")
        .transition()
        .call(
            d3.zoom().scaleBy,
            1.2
        );

}


function zoomOut() {

    d3.select("#ast-container svg")
        .transition()
        .call(
            d3.zoom().scaleBy,
            0.8
        );

}


function resetZoom() {

    runCode();

}


// Keyboard shortcuts

const editor =
    document.getElementById("code");


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


window.onload = runCode;

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

            "tokens": "\n".join(
                map(str, tokens)
            ),

            "ast": serialize_ast(ast)

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

            "ast": None

        })


    except Exception as e:

        return jsonify({

            "output": "Internal Error:\\n" + str(e),

            "tokens": "",

            "ast": None

        })


if __name__ == "__main__":

    app.run(debug=True)
