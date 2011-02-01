class PlumbingCollision(RuntimeError):
    def __init__(self, left, right):
        msg = "\n".join([
            "",
            "    %s",
            "  with:",
            "    %s",
            ]) % (left, right)
        super(PlumbingCollision, self).__init__(msg)
