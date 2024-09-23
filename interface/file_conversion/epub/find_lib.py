from typing import List, Tuple


def find_between(
    text: str, patterns: List[str], start_index: int = 0
) -> Tuple[List[str], int]:
    if len(patterns) < 2 or start_index == -1:
        return [], -1

    indices: List[int] = []
    current_index = start_index
    prev_pattern_length = 0

    for pattern in patterns:
        current_index = text.find(pattern, current_index + prev_pattern_length)
        if current_index != -1:
            indices.append(current_index)
            prev_pattern_length = len(pattern)
        else:
            return [], -1

    found_segments = []
    for i in range(len(indices) - 1):
        start = indices[i] + len(patterns[i])
        end = indices[i + 1]
        found_segments.append(text[start:end])

    return found_segments, indices[-1] + len(patterns[-1])


def find_one(text: str, patterns: List[str]) -> str:
    segments, end_index = find_between(text, patterns)
    return segments[0] if end_index != -1 else ""


def find_all(text: str, patterns: List[str], index: int = -1) -> List[str]:
    results = []
    current_index = 0

    while True:
        segments, end_index = find_between(text, patterns, current_index)
        if end_index == -1:
            break
        results.append(segments[index])
        current_index = end_index + 1

    return results
