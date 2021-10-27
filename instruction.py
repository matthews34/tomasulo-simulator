class Instruction():
    def __repr__(self):
        return f'Instrução: {self.op}; FU: {self.fu_type}; operandos: {self.operands}'
    def __init__(self, op, fu_type, operands: dict):
        self.op = op
        self.fu_type = fu_type
        self.operands = operands