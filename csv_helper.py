#!/usr/bin/env python3

from collections import defaultdict
from mechanisms import model_string, model_label
import os
import csv


def merge_csvs():
    cwd = os.getcwd()
    output_folder = os.path.join(cwd, "output_files", "csvs", "")
    output_file = os.path.join(output_folder, "growth_data.csv")
    files = [
        os.path.join(output_folder, file)
        for file in os.listdir(output_folder)
        if file not in {"growth_data.csv", "average_growth_data.csv"}
    ]
    write_header = not os.path.exists(output_file)
    with open(output_file, "a") as output:
        if write_header:
            output.write("n,cdf,model,p,q,days\n")
        writer = csv.writer(output)
        for file in files:
            with open(file, "r") as data:
                reader = csv.reader(data)
                writer.writerows(reader)
    for file in files:
        os.remove(file)


def add_arrays(A, B):
    if len(A) > len(B):
        return [A[i] + B[i] for i in range(len(B))] + A[len(B) :]
    else:
        return [A[i] + B[i] for i in range(len(A))] + B[len(A) :]


def average_csv():
    cwd = os.getcwd()
    output_folder = os.path.join(cwd, "output_files", "csvs", "")
    input_file = os.path.join(output_folder, "growth_data.csv")
    output_file = os.path.join(output_folder, "average_growth_data.csv")
    growth_rate = defaultdict(list)
    counts = defaultdict(int)
    with open(input_file, "r") as input_csv:
        reader = csv.reader(input_csv)
        next(reader)
        for row in reader:
            n = int(row[0])
            cdf = row[1]
            model = row[2]
            p = float(row[3])
            q = float(row[4])
            data = [int(x) for x in row[5:]]
            key = (n, cdf, model, p, q)
            growth_rate[key] = add_arrays(growth_rate[key], data)
            counts[key] += 1
    with open(output_file, "w") as output_csv:
        output_csv.write("n,cdf,model,p,q,num_trials,days\n")
        for key in growth_rate:
            n, cdf, model, p, q = key
            t = counts[key]
            growth_rate_string = ",".join([str(x / t) for x in growth_rate[key]])
            output_csv.write(f"{n},{cdf},{model},{p},{q},{t},{growth_rate_string}\n")


def csv_helper():
    merge_csvs()
    average_csv()


def main():
    return 0


if __name__ == "__main__":
    main()
