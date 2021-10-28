import re
import argparse
import json
from reservationStation import ReservationStation
from registerState import RegisterState
from instruction import Instruction

# lista de instruções
# TODO: completar instruções que faltam
load_instructions = ['ld', 'lw', 'lwu', 'lh', 'lhu' , 'lb', 'lbu', 'fld', 'flw']
store_instructions = ['sd', 'sw', 'sh', 'sb', 'fsd', 'fsw']
add_instructions = ['add', 'sub', 'subi', 'addi']
mult_instructions = ['mul']
branch_instructions = ['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu']

# tipos de instruções (R, I, S, B, U, J)
R_type = ['add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra', 'or', 'and']
I_type = ['jalr', 'lb', 'lh', 'lw', 'lbu', 'lhu', 'addi', 'slti', 'sltiu', 'xori', 'ori', 'andi', 'slli', 'srli', 'srai']
S_type = ['sb', 'sh', 'sw']
B_type = ['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu']
U_type = ['lui', 'auipc']
J_type = ['jal']

# dicionário contendo o estado dos registradores
reg_stat = {} 
cycle = 0

# lista contendo as estações de reserva
RS = []
def init_RS(config_path: str):
    # carregar configuração do simulador
    with open(config_path) as config_file:
        config = json.load(config_file)
    
    # inicialização das estações de reserva
    for FU_name, FU in config.items():
        for i in range(FU['num']):
            RS.append(ReservationStation(FU_name + str(i+1), FU_name, FU['latency']))

def parse_instructions(filepath: str) -> list:
    # padrões para parsear as instruções
    instr_pattern = re.compile('^(?P<instruction>\S+)\s+(?P<arguments>\S+)')
    imm_pattern = re.compile('(?P<imm>-?\d+)\((?P<rs>\S+)\)')
    
    # abrir arquivo ASM
    file = open(filepath, 'r')

    instr_list = []
    
    for line in file.readlines():
        line.lower()
        if match := instr_pattern.match(line):
            # parsear instrução
            instruction = match.group('instruction')
            arguments = match.group('arguments')
            arguments = arguments.split(',')
            
            # R-type instructions
            if instruction in R_type:
                rd = arguments[0]
                rs = arguments[1]
                rt = arguments[2]
                # TODO: tratar operações lógicas
                if instruction in add_instructions:
                    fu_type = 'add'
                else:
                    fu_type = 'mult'
                instr_list.append(Instruction(instruction, fu_type, {
                    'rd': rd,
                    'rs': rs,
                    'rt': rt
                }))
            
            # I-type e B-type instructions
            elif instruction in I_type or instruction in B_type:
                rt = arguments[0]
                if match := imm_pattern.match(arguments[1]):
                    imm = match.group('imm')
                    rs = match.group('rs')
                else:
                    rs = arguments[1]
                    imm = arguments[2]
                
                # TODO: tratar operações lógicas
                if instruction in load_instructions or instruction in B_type:
                    fu_type = 'load'
                else:
                    fu_type = 'add'
                instr_list.append(Instruction(instruction, fu_type, {
                    'rt': rt,
                    'imm': imm,
                    'rs': rs
                }))

            # S-type instruction
            elif instruction in S_type:
                rt = arguments[0]
                if match := imm_pattern.match(arguments[1]):
                    imm = match.group('imm')
                    rs = match.group('rs')
                else:
                    raise ValueError(f'Argumento inválido: {arguments}')

                instr_list.append(Instruction(instruction, 'load', {
                    'rt': rt,
                    'imm': imm,
                    'rs': rs
                }))

            # U-type e J-type instructions
            elif instruction in U_type or instruction in J_type:
                rt = arguments[0]
                imm = arguments[1]
                instr_list.append(Instruction(instruction, 'add', {
                    'rt': rt,
                    'imm': imm
                }))

            # TODO: tratar as instruções de chamada de sistema e as do tipo CSR
            else:
                pass
                           
    return instr_list

def emit_instruction(instruction: Instruction):
    if instruction.fu_type == 'load':
        # encontrar a primeira estação livre para a operação desejada
        available_stations = [r for r, station in enumerate(RS) if (station.fu_type == 'load' and not station.busy)]
        rt = instruction.operands['rt']
        imm = instruction.operands['imm']
        rs = instruction.operands['rs']
        while not available_stations: # não existe estação livre
            stall()
            available_stations = [r for r, station in enumerate(RS) if (station.fu_type == 'load' and not station.busy)]
        else: # existe estação livre
            print('emitindo', instruction)
            r = available_stations[0]
            RS[r].reserve(instruction.op)
            if rs not in reg_stat:
                reg_stat[rs] = RegisterState()
            if reg_stat[rs].qi != 0:
                RS[r].qj = reg_stat[rs].qi
            else:
                RS[r].vj = rs
                RS[r].qj = 0
                RS[r].address = imm
                RS[r].busy = True
            if instruction in load_instructions:
                reg_stat[rt].qi = RS[r].name
            if instruction in store_instructions:
                if reg_stat[rt].qi != 0:
                    RS[r].qk = reg_stat[rs].qi
                else:
                    RS[r].vk = rt
                    RS[r].qk = 0
    # TODO: lidar com instruções com operando imediato
    elif instruction.fu_type == 'add' and instruction.op in R_type: # add ou mult
        # encontrar a primeira estação livre para a operação desejada
        available_stations = [r for r, station in enumerate(RS) if (station.fu_type == instruction.fu_type and not station.busy)]
        rs = instruction.operands['rs']
        rt = instruction.operands['rt']
        rd = instruction.operands['rd']
        while not available_stations: # não existe estação livre
            stall()
            available_stations = [r for r, station in enumerate(RS) if (station.fu_type == instruction.fu_type and not station.busy)]
        else: # existe uma estação livre
            print('emitindo', instruction)
            r = available_stations[0]
            RS[r].reserve(instruction.op)
            if rs not in reg_stat:
                reg_stat[rs] = RegisterState()
            if reg_stat[rs].qi != 0:
                RS[r].qj = reg_stat[rs].qi
            else:
                RS[r].vj = rs
                RS[r].qj = 0
            if rt not in reg_stat:
                reg_stat[rt] = RegisterState()
            if reg_stat[rt] != 0:
                RS[r].qk = reg_stat[rt].qi
            else:
                RS[r].vk = rt
                RS[r].qk = 0
                RS[r].busy = True
                if rd not in reg_stat:
                    reg_stat[rd] = RegisterState()
                reg_stat[rd].qi = r

def execute():
    pass

def write_result():
    pass

def stall():
    # atualizar ciclo atual
    global cycle
    cycle += 1
    # atualizar estações de reserva
    for station in RS:
        station.update()

if __name__=='__main__':
    # parsear argumentos
    parser = argparse.ArgumentParser(description='Simular o algoritmo de Tomasulo')
    parser.add_argument('asm_path', type=str, help='caminho para o arquivo contendo o assembly do código a ser simulado')
    parser.add_argument('--config_path', type=str, default='config.json', help='caminho para o arquivo contendo as configurações')
    args = parser.parse_args()
    filepath = args.asm_path
    config_path = args.config_path

    # inicializar estações de reserva
    init_RS(config_path)

    # parsear instruções
    instr_list = parse_instructions(filepath)

    # executar simulação
    for instruction in instr_list:
        emit_instruction(instruction)
