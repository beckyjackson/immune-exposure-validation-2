# Immune Exposure Model Makefile
#
# James A. Overton <james@overton.ca>

### Configuration
#
# These are standard options to make Make sane:
# <http://clarkgrubb.com/makefile-style-guide#toc2>

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:
	
ONTOLOGY_TABLES := src/ontology/prefix.tsv src/ontology/terminology.tsv
DOC_TABLES := build/schema.tsv build/valid.tsv build/invalid.tsv
VALVE_TABLES := build/datatype.tsv build/field.tsv build/rule.tsv
TABLES := $(ONTOLOGY_TABLES) $(DOC_TABLES) $(VALVE_TABLES)
PREFIXES := --prefixes build/prefix.json
ROBOT := java -jar bin/robot.jar $(PREFIXES)

bin build:
	mkdir -p $@

bin/robot.jar: | bin
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/master/lastSuccessfulBuild/artifact/bin/robot.jar

UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
    RDFTAB_URL := https://github.com/ontodev/rdftab.rs/releases/download/v0.1.1/rdftab-x86_64-apple-darwin
else
    RDFTAB_URL := https://github.com/ontodev/rdftab.rs/releases/download/v0.1.1/rdftab-x86_64-unknown-linux-musl
endif

bin/rdftab: | bin
	curl -L -o $@ $(RDFTAB_URL)
	chmod +x $@
	
build/immune_exposure.xlsx: | build
	curl -L -o $@ https://docs.google.com/spreadsheets/d/1A62wTHoSUMZENldjhCZt7loyb_OFA_PbfsqKPpDjWx4/export?format=xlsx

$(TABLES): build/immune_exposure.xlsx
	xlsx2csv -d tab --sheetname $(basename $(notdir $@)) $< > $@

build/prefix.json: src/ontology/prefix.tsv
	echo '{ "@context": {' > $@
	tail -n+2 $< \
	| sed 's/\(.*\)\t\(.*\)/    "\1": "\2",/' \
	| sed '$$s/,$$//' \
	>> $@
	echo '} }' >> $@
	
build/prefix.sql: src/ontology/prefix.tsv | build
	echo "CREATE TABLE IF NOT EXISTS prefix (" > $@
	echo "  prefix TEXT PRIMARY KEY," >> $@
	echo "  base TEXT NOT NULL" >> $@
	echo ");" >> $@
	echo "INSERT OR IGNORE INTO prefix VALUES" >> $@
	tail -n+2 $< \
	| sed 's/\(.*\)\t\(.*\)/("\1", "\2"),/' \
	| sed '$$s/,$$/;/' \
	>> $@

build/immune_exposure.owl: src/ontology/terminology.tsv build/prefix.json | bin/robot.jar
	$(ROBOT) template \
	--template $< \
	annotate \
	--ontology-iri "http://example.com" \
	--output $@

build/immune_exposure.db: build/prefix.sql build/immune_exposure.owl | bin/rdftab
	rm -f $@
	sqlite3 $@ < $<
	bin/rdftab $@ < $(word 2,$^)

.PRECIOUS: build/%-messages.tsv
build/%-messages.tsv: build/%.tsv $(VALVE_TABLES) $(ONTOLOGY_TABLES)
	cp $< build/exposure.tsv
	-valve -o $@ $(VALVE_TABLES) $(ONTOLOGY_TABLES) build/exposure.tsv

src/server/templates/%.html: src/server/tsv2html.py src/ontology/terminology.tsv build/%.tsv build/%-messages.tsv
	python3 $^ $@

src/server/templates/schema.html: src/server/tsv2html.py src/ontology/terminology.tsv build/schema.tsv
	python3 $^ $@
	
examples/immune-exposure-example-%.csv: src/server/tsv2csv.py build/%.tsv
	python3 $^ $@
	
examples/immune-exposure-template.csv: examples/immune-exposure-example-valid.csv
	head -n1 $< > $@

.PHONY: docs
docs: src/server/templates/schema.html src/server/templates/valid.html src/server/templates/invalid.html

.PHONY: examples
examples: examples/immune-exposure-example-valid.csv examples/immune-exposure-example-invalid.csv examples/immune-exposure-template.csv
examples: build/valid-messages.tsv
examples: build/invalid-messages.tsv

.PHONY:
all: docs examples build/immune_exposure.db

.PHONY: clean
clean:
	rm -rf build

.PHONY: clobber
clobber: clean
	rm -rf bin

.PHONY: update
update:
	rm -f $(TABLES)
	make clean all
