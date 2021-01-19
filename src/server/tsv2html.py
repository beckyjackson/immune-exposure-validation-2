#!/usr/bin/env python3

import argparse
import csv
import re

from collections import defaultdict


def a1_to_rowcol(a1):
    m = re.compile(r"([A-Za-z]+)([1-9]\d*)").match(a1)
    if m:
        column_label = m.group(1).upper()
        ridx = int(m.group(2))
        cidx = 0
        for i, c in enumerate(reversed(column_label)):
            cidx += (ord(c) - 64) * (26 ** i)
        return ridx, cidx
    return None


def tsv2html(terminology_input, table_input, messages_input):
    labels = {}
    if isinstance(terminology_input, str):
        with open(terminology_input) as f:
            terminology = list(csv.DictReader(f, delimiter="\t"))
        labels = {}
        for row in terminology:
            labels[row["Label"]] = row["ID"]
    elif isinstance(terminology_input, dict):
        labels = terminology_input

    table = []
    if isinstance(table_input, str):
        delimiter = "\t"
        if table_input.endswith(".csv"):
            delimiter = ","
        with open(table_input) as f:
            table = list(csv.DictReader(f, delimiter=delimiter))
    elif isinstance(table_input, list):
        table = table_input

    messages = defaultdict(dict)
    if isinstance(messages_input, str):
        with open(messages_input) as f:
            for row in csv.DictReader(f, delimiter="\t"):
                if row["table"] == "exposure":
                    r, c = a1_to_rowcol(row["cell"])
                    messages[r][c] = row
    elif isinstance(messages_input, list):
        for row in messages_input:
            if row["table"] == "exposure":
                r, c = a1_to_rowcol(row["cell"])
                messages[r][c] = row
    elif isinstance(messages_input, dict):
        messages = messages_input

    lines = ["<table class='table'>"]
    lines.append("  <thead>")
    lines.append("    <tr>")
    for key, value in table[0].items():
        href = re.sub("\W+", "-", key.lower())
        content = f"<a href='/instructions#{href}'>{key}</a>"
        lines.append(f"      <th>{content}</th>")
    lines.append("    </tr>")
    lines.append("  </thead>")

    lines.append("  <tbody>")
    r = 1
    for row in table:
        r += 1
        lines.append("    <tr>")
        c = 0
        for key, value in row.items():
            c += 1
            if not value:
                value = ""

            attrs = ""
            if value.startswith("required"):
                attrs = " class='table-success'"
            elif value.startswith("optional"):
                attrs = " class='table-warning'"

            if messages and r in messages and c in messages[r]:
                msg = messages[r][c]

                rule_id = msg.get("rule ID", "")
                rule_text = msg.get("rule", "")
                rule_message = msg.get("message", "")
                suggest = msg.get("suggestion", "")
                level = msg.get("level", "error").lower()
                full_msg = ""
                if rule_id and rule_text:
                    full_msg += f"{rule_id}: {rule_text}"
                elif rule_id:
                    full_msg += rule_id
                elif rule_text:
                    full_msg += rule_text

                if rule_message and full_msg != "":
                    full_msg += f"<br>{rule_message}"
                elif rule_message:
                    full_msg += rule_message

                if suggest and full_msg != "":
                    full_msg += f"<br>Suggestion: '{suggest}'"
                elif suggest:
                    full_msg += f"Suggestion: '{suggest}'"
                message = full_msg.replace("\"", "&quot;")
                attrs += f' class="table-danger" data-toggle="tooltip" data-placement="bottom" data-html="true" title="{message}"'

            prefix = ""
            term = value
            if value.startswith("required: "):
                prefix = "required: "
            elif value.startswith("optional: "):
                prefix = "optional: "
            if prefix:
                term = value.replace(prefix, "")

            content = value
            if term in labels:
                content = f"{prefix}<a href='/terminology/{labels[term]}'>{term}</a>"
            lines.append(f"      <td{attrs}>{content}</td>")
        lines.append("    </tr>")
    lines.append("  </tbody>")
    lines.append("</table>")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Convert a terminology table to HTML")
    parser.add_argument("terminology", type=str, help="The terminology TSV file")
    parser.add_argument("table", type=str, help="The table TSV file")
    parser.add_argument("messages", nargs="?", type=str, help="The messages TSV file")
    parser.add_argument("output", type=str, help="The output HTML file")
    args = parser.parse_args()

    with open(args.output, 'w') as output:
        output.write(tsv2html(args.terminology, args.table, args.messages))


if __name__ == "__main__":
    main()

