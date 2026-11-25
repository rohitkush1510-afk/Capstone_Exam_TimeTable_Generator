import csv
from itertools import combinations


def load_students(path):
    """Read the CSV and return a dict: {student_name: [subject, ...]}"""
    students = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects = [s.strip() for s in row["subjects"].split(";") if s.strip()]
            students[row["student"].strip()] = subjects
    return students


def build_conflict_graph(students):
    """
    Returns:
        subjects : sorted list of all subject names (the vertices)
        graph    : dict {subject: set(conflicting subjects)} (the edges)
    """
    subjects = sorted({s for subs in students.values() for s in subs})
    graph = {s: set() for s in subjects}

    # If two subjects appear in the same student's list -> add an edge
    for subs in students.values():
        for a, b in combinations(set(subs), 2):
            graph[a].add(b)
            graph[b].add(a)

    return subjects, graph