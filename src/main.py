import sys
import os
from graph import load_students, build_conflict_graph
from coloring import find_min_slots


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/sample.csv"

    students = load_students(path)
    subjects, graph = build_conflict_graph(students)

    print("\n=== Conflict Graph ===")
    for s in subjects:
        print(f"  {s:<12} conflicts with: {sorted(graph[s]) or 'none'}")

    k, colors = find_min_slots(subjects, graph)

    print(f"\n=== Minimum time slots needed: {k} ===\n")
    for slot in range(1, k + 1):
        in_slot = [s for s in subjects if colors[s] == slot]
        print(f"  Slot {slot}: {', '.join(in_slot)}")


if __name__ == "__main__":
    main()