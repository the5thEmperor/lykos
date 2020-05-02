

class MockDispatcher:

    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.client = "filler"

    @property
    def private(self):
        return

    @property
    def public(self):
        return

    def pm(self, *messages, **kwargs):
        """Send a private message or notice to the sender."""
        return

    def send(self, *messages, **kwargs):
        return

    def reply(self, *messages, prefix_nick=False, **kwargs):
        return
