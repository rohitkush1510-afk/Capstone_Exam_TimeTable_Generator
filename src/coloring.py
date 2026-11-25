def is_safe(subject, color, graph, colors):
    """Can this subject take this color? Only if no neighbor already has it."""
    for neighbor in graph[subject]:
        if colors.get(neighbor) == color:
            return False
    return True


def backtrack_color(order, graph, colors, index, max_colors):
    """
    Try to color order[index] onwards.
    Returns True if a full valid coloring is found.
    """
    # Base case: every subject is colored
    if index == len(order):
        return True

    subject = order[index]

    for color in range(1, max_colors + 1):   # try slot 1, 2, 3 ...
        if is_safe(subject, color, graph, colors):
            colors[subject] = color           # CHOOSE
            if backtrack_color(order, graph, colors, index + 1, max_colors):
                return True                   # success, stop
            del colors[subject]               # UNDO (backtrack)

    return False   # no color works -> go back to the previous subject


def find_min_slots(subjects, graph):
    """
    Try k = 1, 2, 3, ... until a valid coloring exists.
    The first k that works is the minimum number of slots.
    """
    # Order: most conflicts first (easier to solve)
    order = sorted(subjects, key=lambda s: len(graph[s]), reverse=True)

    for k in range(1, len(subjects) + 1):
        colors = {}
        if backtrack_color(order, graph, colors, 0, k):
            return k, colors
    return None, {}