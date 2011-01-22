import os

class PlumbingCollision(RuntimeError):
    def __init__(self, there, new):
        msg = os.linesep.join([
            "",
            "    %s",
            "  with:",
            "    %s",
            ]) % (new, there)
        super(PlumbingCollision, self).__init__(msg)
