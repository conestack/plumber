import os

class PlumbingCollision(RuntimeError):
    def __init__(self, left, right):
        msg = os.linesep.join([
            "",
            "    %s",
            "  with:",
            "    %s",
            ]) % (left, right)
        super(PlumbingCollision, self).__init__(msg)
