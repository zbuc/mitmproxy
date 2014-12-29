import libmproxy.console.input as input


class TInput(input.Input):
    @input.key("j", "Down")
    def down(self):
        pass


def test_simple():
    t = TInput()
    print t
    t.down()


