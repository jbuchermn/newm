
class State:
    """
    Encapsulates all animatable properties ("var") of a stateful
    object.

    State must provide a constructor taking all vars in the order
    given in "var"

    A stateful class provides a "state" property,
    which carries the information used for layouting stuff
    that does not care about animations.

    Additionally such a class provides an "update" function
    taking ?some sort of state? to be called during animation.
    After the animation, the new property "state" will be reset
    and "update" called again.

    """
    def __init__(self, var):
        self.var = var

    def copy(self):
        vals = [self.__dict__[k] for k in self.var]
        return self.__class__(*vals)

    def kwargs(self):
        return {k:self.__dict__[k] for k in self.var}
