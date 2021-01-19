#!/usr/bin/env python3

import csv
import os.path

import gizmos.tree
import gizmos.search

from flask import Flask, request, render_template, send_from_directory
from io import TextIOWrapper
from tempfile import TemporaryDirectory
from tsv2html import tsv2html
from valve import validate

app = Flask(__name__)

predicate_ids = [
  "rdfs:label",
  "IAO:0000118",
  "IAO:0000115",
  "IAO:0000119",
  "IAO:0000112",
  "rdf:type",
  "rdfs:subClassOf",
]
valve_tables = [
  "build/datatype.tsv",
  "build/field.tsv",
  "build/rule.tsv",
  "src/ontology/prefix.tsv",
  "src/ontology/terminology.tsv"
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/instructions")
def instructions():
    return render_template("instructions.html")

@app.route("/examples")
def example():
    return render_template("examples.html")

@app.route("/examples/<path:filename>")
def download(filename):
    dir = os.path.join(os.getcwd(), "examples")
    return send_from_directory(dir, filename)

@app.route("/terminology")
@app.route("/terminology/")
@app.route("/terminology/<id>")
def terminology(id=None):
    db = "build/immune_exposure.db"
    if request.args and "text" in request.args:
        return gizmos.search.search(db, request.args["text"])
    else:
        html = gizmos.tree.tree(db, id, title="Immune Exposure Terminology", href="/terminology/{curie}", predicate_ids=predicate_ids, standalone=False)
        return render_template("terminology.html", content=html)

@app.route("/validator", methods=["GET", "POST"])
def validator():
    if request.method == "GET":
        return render_template("validator.html")
    else:
        if 'file' not in request.files:
            message = f"<p class='alert alert-danger'>Please upload a file.</p>"
            return render_template("validator.html", message=message)
        else:
            f = request.files["file"]
            filename = f.filename
            if filename.endswith(".csv"):
                suffix = ".csv"
            elif filename.endswith(".tsv"):
                suffix = ".tsv"
            else:
                message = f"<p class='alert alert-danger'>Unrecognized file type for '{filename}'. Please use CSV or TSV format.</p>"
                return render_template("validator.html", message=message)

            tempdir = TemporaryDirectory()
            path = os.path.join(tempdir.name, "exposure" + suffix)
            f.save(path)
            messages = validate(valve_tables + [path])
            messages = [m for m in messages if m["table"] == "exposure"]

            if messages:
                message = "<p class='alert alert-danger'>This template contains errors.</p>"
            else:
                message = "<p class='alert alert-success'>This template is valid.</p>"

            table = tsv2html("src/ontology/terminology.tsv", path, messages)
            message += "\n\n" + table
        return render_template("validator.html", message=message)
