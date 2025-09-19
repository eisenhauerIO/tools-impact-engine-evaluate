# Shared base classes or utilities for assistants can go here.
class BaseAssistant:
    def assist(self, *args, **kwargs):
        raise NotImplementedError("Assist method must be implemented by subclasses.")
