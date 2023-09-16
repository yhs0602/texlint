import argparse
import json
from typing import List, Union

from pylatexenc.latexwalker import (
    LatexWalker,
    LatexNode,
    LatexMacroNode,
    LatexGroupNode,
    LatexCharsNode,
    LatexCommentNode,
    LatexEnvironmentNode,
    LatexSpecialsNode,
    LatexMathNode,
)


def lint_table(table_data):
    warnings = []

    # 1. Check for table environment
    if table_data.get("type") != "GroupNode" or table_data.get("delimiters") != (
        "\\begin{table}",
        "\\end{table}",
    ):
        warnings.append("Table environment not detected.")
        return warnings

    # 2. Check for positioning directive [H]
    # Assuming you have captured the optional argument in 'args'
    if table_data.get("args", [{}])[0].get(
        "type"
    ) == "CharsNode" and "[H]" not in table_data["args"][0].get("content", ""):
        warnings.append("Table does not have a [H] positioning directive.")

    # 3. Check for centering
    centering_found = False
    for child in table_data.get("children", []):
        if child.get("type") == "GroupNode" and child.get("delimiters") == (
            "\\begin{center}",
            "\\end{center}",
        ):
            centering_found = True
    if not centering_found:
        warnings.append(
            "Table is not centered using \\begin{center} and \\end{center}."
        )

    # 4. Check for table caption
    caption_found = False
    for child in table_data.get("children", []):
        if child.get("type") == "MacroNode" and child.get("macroname") == "caption":
            caption_found = True
            # Further checks for caption content can be added here
    if not caption_found:
        warnings.append("Table does not have a caption using \\caption.")

    # Further checks like table numbering can be added here

    return warnings


def convert_node_to_dict(node: LatexNode, depth: int = 0) -> Union[str, dict]:
    if node is None:
        return None
    if isinstance(node, LatexMacroNode):
        return {
            "type": "MacroNode",
            "macroname": node.macroname,
            "args": [
                convert_node_to_dict(arg, depth + 1) for arg in node.nodeargd.argnlist
            ],
        }
    if isinstance(node, LatexGroupNode):
        return {
            "type": "GroupNode",
            "delimiters": str(node.delimiters),
            "children": [
                convert_node_to_dict(child_node, depth + 1)
                for child_node in node.nodelist
            ],
        }
    if isinstance(node, LatexCharsNode):
        escaped_string = repr(node.chars)[1:-1]  # Remove surrounding quotes
        return escaped_string
    if isinstance(node, LatexCommentNode):
        return {"type": "CommentNode", "comment": node.comment}
    if isinstance(node, LatexEnvironmentNode):
        return {
            "type": "EnvironmentNode",
            "environmentname": node.environmentname,
            "args": [
                convert_node_to_dict(arg, depth + 1) for arg in node.nodeargd.argnlist
            ],
            "children": [
                convert_node_to_dict(child_node, depth + 1)
                for child_node in node.nodelist
            ],
        }
    if isinstance(node, LatexSpecialsNode):
        if node.nodeargd is None:
            return {"type": "SpecialsNode", "specials": node.specials_chars, "args": []}
        return {
            "type": "SpecialsNode",
            "specials": node.specials_chars,
            "args": [
                convert_node_to_dict(arg, depth + 1) for arg in node.nodeargd.argnlist
            ],
        }
    if isinstance(node, LatexMathNode):
        return {
            "type": "MathNode",
            "nodelist": [
                convert_node_to_dict(child_node, depth + 1)
                for child_node in node.nodelist
            ],
        }
    # Catch-all for any other nodes (just to be safe)
    return {"type": f"Unknown;{type(node)}"}


def print_node(node: LatexNode, depth: int = 0):
    indent = "--" * depth  # 2 spaces per depth level
    if isinstance(node, LatexMacroNode):
        print(indent + node.macroname)
        for arg in node.nodeargd.argnlist:
            print_node(arg, depth + 1)
    if isinstance(node, LatexGroupNode):
        print(indent + str(node.delimiters))
        for child_node in node.nodelist:
            print_node(child_node, depth + 1)  # Increase depth for child nodes
    if isinstance(node, LatexCharsNode):
        escaped_string = repr(node.chars)[1:-1]  # Remove surrounding quotes
        print(indent + escaped_string)


def main():
    parser = argparse.ArgumentParser(
        description="Process a LaTeX file and output its structure as JSON."
    )
    parser.add_argument("input_file", help="Name of the input LaTeX file to process")
    args = parser.parse_args()

    with open(args.input_file, "r") as f:
        latex_content = f.read()

    walker = LatexWalker(latex_content)

    # Walk through the LaTeX nodes
    pos = 0
    parsed, pos, l = walker.get_latex_nodes(pos)
    parsed: List[LatexNode]
    structured_data = [convert_node_to_dict(node) for node in parsed]

    # Write to JSON file named based on input
    output_file = args.input_file.replace(".tex", ".json")
    with open(output_file, "w") as f:
        json.dump(structured_data, f, indent=4)

    print(f"Processed {args.input_file} and saved result to {output_file}")


if __name__ == "__main__":
    main()
