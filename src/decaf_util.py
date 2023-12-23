from typing import List, Optional, Union


class Counter:
    def __init__(self, start: int):
        self.start = start
        self.curr = start

    def next(self):
        out = self.curr
        self.curr += 1
        return out

    def reset(self, new_start: Optional[int] = None):
        if new_start != None:
            self.start = new_start
        self.curr = self.start


NestedStrList = List[Union[str, "NestedStrList"]]
