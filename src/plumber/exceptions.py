import os

linesep = getattr(os, 'linsep', '\n')

class PlumbingCollision(RuntimeError):
    def __init__(self, left, right):
        msg = linesep.join([
            "",
            "    %s",
            "  with:",
            "    %s",
            ]) % (left, right)
        super(PlumbingCollision, self).__init__(msg)
