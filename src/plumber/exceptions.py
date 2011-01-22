class PlumbingCollision(RuntimeError):
    def __init__(self, name, there, new):
        msg = "'%s' %s collides with %s" % (name, new, there)
        super(PlumbingCollision, self).__init__(msg)
