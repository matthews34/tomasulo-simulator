class RegisterState():
    def __repr__(self):
        return (
            f'value = {self.value}\n'
            f'qi = {self.qi}\n'
        )
    def __init__(self, qi=0, value=None):
        self.qi = qi
        self.value = value