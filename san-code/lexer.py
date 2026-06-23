from pygments.lexer import RegexLexer
from pygments.token import Keyword, String, Number, Comment, Name
from pygments.lexers import get_lexer_by_name
from pygments.lexers import _mapping

# doc: Lexer for Sans!
class SANLexer(RegexLexer):
    name = "SAN"
    aliases = ["san"]

    tokens = {
        "root": [
            (r"//.*", Comment),
            (r'"[^"]*"', String),
            (r"\b(dec|const|flux|func|if|else|while|return)\b", Keyword),
            (r"\b[0-9]+\b", Number),
            (r"[a-zA-Z_]\w*", Name),
        ]
    }
