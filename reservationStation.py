class ReservationStation():
    def __repr__(self):
        if not self.busy:
            return f'{self.name}: busy = False'
        else:
            return (
                f'{self.name}:\n'
                f'busy = {self.busy}\n'
                f'op = {self.op}\n'
                f'vj = {self.vj}\n'
                f'vk = {self.vk}\n'
                f'qj = {self.qj}\n'
                f'qk = {self.qk}\n'
                f'address = {self.address}\n'
                f'time to finish = {self.time_to_finish}'
            )
    
    def __init__(self, name: str, fu_type: str, fu_latency: int):
        self.name = name
        self.fu_type = fu_type
        self.fu_latency = fu_latency
        self.busy = False
        self.op = None
        self.vj = None
        self.vk = None
        self.qj = None
        self.qk = None
        self.address = None
        self.time_to_finish = 0
        self.done = False
    
    def reserve(self, op: str):
        self.op = op
        self.busy = True
        self.time_to_finish = self.fu_latency
    
    def update(self):
        if self.busy:
            # TODO: incluir condição para operações de load/store
            if self.qj == 0 and self.qk == 0:
                    self.time_to_finish -= 1
            """
            if self.time_to_finish <= 0:
                # remover registrador no reg_stat?
                self.op = None
                self.busy = False
            """

    def release(self):
        self.busy = False
        self.op = None
        self.vj = None
        self.vk = None
        self.qj = None
        self.qk = None
        self.address = None

    def has_finished(self):
        return self.time_to_finish == 0