#!/usr/bin/env python3

import argparse
import csv


def tsv2csv(tsv_path, csv_path):
    with open(csv_path, 'w') as c:
        w = csv.writer(c, dialect="excel")
        with open(tsv_path) as t:
            for row in csv.reader(t, delimiter="\t"):
                w.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Convert TSV to CSV")
    parser.add_argument("tsv", type=str, help="The input TSV file")
    parser.add_argument("csv", type=str, help="The output CSV file")
    args = parser.parse_args()

    tsv2csv(args.tsv, args.csv)


if __name__ == "__main__":
    main()

