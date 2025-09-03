class Rule:
    def __init__(self, data: dict):
        self.data = data

    def process(self):
        pass

def rule_class(cls):
    cls._is_rule = True
    return cls