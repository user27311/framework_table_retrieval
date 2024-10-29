# CORD19 has 1.056.661 extract 1000
from cord19_plus.downloadpdf.downloaders import Cord19Reader
import csv
from random import randrange


def extract_records(read_path, write_path, size, limit):
    ids_to_etract = set()
    while len(ids_to_etract) != size:
        id = randrange(0, limit)
        ids_to_etract.add(id)

    records = []
    with open(read_path, "r") as fp:
        headers = fp.readline()
        line = fp.readline()
        counter = 0
        while line != "":
            if counter in ids_to_etract:
                records.append(line)
            line = fp.readline()
            counter += 1

    with open(write_path, "w") as fp:
        fp.write(headers)
        for line in records:
            fp.write(line)


def filter_none_dois(read_path, write_path):
    with open(write_path, "w") as fp_write:
        with open(read_path, "r") as fp_read:
            reader = csv.reader(fp_read)
            writer = csv.writer(fp_write)
            headers = next(reader)
            writer.writerow(headers)
            counter = 0
            for row in reader:
                if row[4] == "":
                    continue
                else:
                    counter += 1
                    writer.writerow(row)
    return counter


if __name__ == "__main__":
    limit = filter_none_dois("metadata.csv", "metadata_clean.csv")
    extract_records(read_path="metadata_clean.csv", write_path="metadata_1000_sample.csv", size=1000, limit=limit)
