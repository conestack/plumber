class PlumbingCollision(RuntimeError):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        msg = '\n'.join(
            [
                '',
                '    %s',
                '  with:',
                '    %s',
            ]
        ) % (left, right)
        super().__init__(msg)
