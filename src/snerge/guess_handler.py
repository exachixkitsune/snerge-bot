from __future__ import annotations

from typing import Dict, List, Set

import statistics


class guess_handler:
    use_latest_reply: bool
    guesses: Dict

    def __init__(self, use_latest_reply: bool = True):
        self.use_latest_reply = use_latest_reply
        self.guesses = {}

    def accept_guess(self, name: str, value: int) -> None:
        if self.use_latest_reply:
            self.guesses[name] = value
        else:
            if name not in self.guesses:
                self.guesses[name] = value

    def get_score(
        self, value: float, closest_without_going_over: bool
    ) -> (List[str], Set[int]):
        # Find the score value to use as a result
        raw_values = list(self.guesses.values())
        raw_values.sort()

        if closest_without_going_over:
            # Which value is the closest value that isn't over
            # Note, raw_values are sorted; let's find the value before that
            result_values = raw_values[0]
            last_i = raw_values[0]
            for i in raw_values[1:]:
                if value < i:
                    result_values = last_i
                    break
                last_i = i
            result_values = set([result_values])
        else:
            diffs = [abs(i - value) for i in raw_values]
            min_diff = min(diffs)
            result_values = []
            for i_indx in range(len(diffs)):
                if diffs[i_indx] == min_diff:
                    result_values.append(raw_values[i_indx])
            result_values = set(result_values)

        result_names = []
        for i_name in self.guesses:
            if self.guesses[i_name] in result_values:
                result_names.append(i_name)

        return (result_names, result_values)

    def num_replies(self) -> int:
        return len(self.guesses)

    def stats(self) -> Dict[str, int | float]:
        raw_values = list(self.guesses.values())

        return {
            "count": self.num_replies(),
            "min": min(raw_values),
            "max": max(raw_values),
            "mean": statistics.mean(raw_values),
            "stdev": statistics.stdev(raw_values),
            "median": statistics.median(raw_values),
            "multimode": statistics.multimode(raw_values),
            "quartiles": statistics.quantiles(raw_values, n=4),
        }
