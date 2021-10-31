import re
import argparse
import json
from reservationStation import ReservationStation
from registerState import RegisterState
from instruction import Instruction

# lista de instruções
# TODO: completar instruções que faltam
#load_instructions = ['ld', 'lw', 'lwu', 'lh', 'lhu' , 'lb', 'lbu', 'fld', 'flw']
#store_instructions = ['sd', 'sw', 'sh', 'sb', 'fsd', 'fsw']
load_instructions = ['lb', 'lh', 'lw', 'lbu', 'lhu']
store_instructions = ['sb', 'sh', 'sw']
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

# fila para execução de instruções de acesso à memória
mem_queue = []
pop_mem_queue = False

# fila para escrita no cdb
cdb_queue = []

# tabela de saída do simulador tomasulo no formato
# [ instrução , emissão , execução , escreve resultado ]
output = {}

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

def init_reg_stat():
    reg_stat_names = ['r' + str(n) for n in range(32)]
    for name in reg_stat_names:
        reg_stat[name] = RegisterState()

def parse_instructions(filepath: str) -> list:
    # padrões para parsear as instruções
    instr_pattern = re.compile('^(?P<instruction>\S+)\s+(?P<arguments>\S+)')
    imm_pattern = re.compile('(?P<imm>-?\d+)\((?P<rs>\S+)\)')
    
    # abrir arquivo ASM
    file = open(filepath, 'r')

    instr_list = []
    
    for i, line in enumerate(file.readlines()):
        line.lower()
        if match := instr_pattern.match(line):
            # parsear instrução
            instruction = match.group('instruction')
            arguments = match.group('arguments')
            output[i] = [f'{instruction} {arguments}']
            arguments = arguments.split(',')
            
            # R-type instructions
            if instruction in R_type:
                rd = arguments[0]
                rs = arguments[1]
                rt = arguments[2]
                fu_type = 'add'
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
                
                if instruction in load_instructions:
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

def emit_instruction(i: int, instruction: Instruction):
    if instruction.fu_type == 'load':
        # encontrar a primeira estação livre para a operação desejada
        rt = instruction.operands['rt']
        imm = instruction.operands['imm']
        rs = instruction.operands['rs']
        while not (available_stations := [r for r, station in enumerate(RS) if (station.fu_type == 'load' and not station.busy)]): # não existe estação livre
            stall()
        else: # existe estação livre
            #print('emitindo', instruction)
            r = available_stations[0]
            mem_queue.append(RS[r])
            RS[r].reserve(instruction.op, i)
            output[i] += [cycle, []]
            if reg_stat[rs].qi != 0:
                RS[r].qj = reg_stat[rs].qi
            else:
                RS[r].vj = rs
                RS[r].qj = 0
                RS[r].address = imm
            if instruction.op in load_instructions:
                reg_stat[rt].qi = RS[r].name
            if instruction.op in store_instructions:
                if reg_stat[rt].qi != 0:
                    RS[r].qk = reg_stat[rt].qi
                else:
                    RS[r].vk = rt
                    RS[r].qk = 0
    
    elif instruction.fu_type == 'add':
        # encontrar a primeira estação livre para a operação desejada        
        while not (available_stations := [r for r, station in enumerate(RS) if (station.fu_type == 'add' and not station.busy)]): # não existe estação livre
            stall()           
        else: # existe uma estação livre
            #print('emitindo', instruction)
            r = available_stations[0]
            RS[r].reserve(instruction.op, i)
            output[i] += [cycle, []]

            # R-type instructions
            if instruction.op in R_type:
                rs = instruction.operands['rs']
                rt = instruction.operands['rt']
                rd = instruction.operands['rd']         
                if reg_stat[rs].qi != 0:
                    RS[r].qj = reg_stat[rs].qi
                else:
                    RS[r].vj = reg_stat[rs].value
                    RS[r].qj = 0
                if reg_stat[rt].qi != 0:
                    RS[r].qk = reg_stat[rt].qi
                else:
                    RS[r].vk = reg_stat[rt].value
                    RS[r].qk = 0
                reg_stat[rd].qi = RS[r].name
                
            else:
                imm = instruction.operands['imm']
                rt = instruction.operands['rt']

                # I-type instructions
                if instruction.op in I_type:
                    rs = instruction.operands['rs']
                    if reg_stat[rs].qi != 0:
                        RS[r].qj = reg_stat[rs].qi
                    else:
                        RS[r].vj = reg_stat[rs].value
                        RS[r].qj = 0
                    RS[r].vk = imm
                    RS[r].qk = 0
                    reg_stat[rt].qi = RS[r].name
                
                # B-type instructions
                elif instruction.op in B_type:
                    rs = instruction.operands['rs']
                    if reg_stat[rs].qi != 0:
                        RS[r].qj = reg_stat[rs].qi
                    else:
                        RS[r].vj = reg_stat[rs].value
                        RS[r].qj = 0
                    if reg_stat[rt].qi != 0:
                        RS[r].qk = reg_stat[rt].qi
                    else:
                        RS[r].vk = reg_stat[rt].value
                        RS[r].qk = 0
                    RS[r].address = imm
                    
                # U/J-type instructions
                else:
                    RS[r].vj = imm
                    RS[r].qj = 0
                    RS[r].qk = 0   # TODO: outro approach?
                    reg_stat[rt].qi = RS[r].name

def execute(station: ReservationStation):
    # TODO: Um if personalizado para cada instrução?
    station.done = True
    global pop_mem_queue
    if mem_queue and mem_queue[0].name == station.name:
        pop_mem_queue = True

    if station.op in S_type or station.op in B_type:
        # TODO: Fazer mais o que?
        output[station.table_id] += ['-']
        station.release()
    else:
        cdb_queue.append(station)

def write_result():
    if cdb_queue:
        i = cdb_queue[0].table_id
        exec_end = output[i][2][-1]
        if exec_end != cycle:
            station = cdb_queue.pop(0)
            for reg in reg_stat:
                if reg_stat[reg].qi == station.name:
                    reg_stat[reg].value = station.vk
                    reg_stat[reg].qi = 0
            for s in RS:
                if s.qj == station.name:
                    s.vj = station.vk
                    s.qj = 0
                if s.qk == station.name:
                    s.vk = station.vk
                    s.qk = 0
            output[station.table_id] += [cycle]
            station.release()

def update_all():
    global pop_mem_queue

    # atualizar estações de reserva
    for station in RS:
        if station.busy and not station.done:
            if mem_queue:
                top_mem_queue = mem_queue[0].name
            else:
                top_mem_queue = None

            if station.op in load_instructions:
                flag_op = 'load'
            elif station.op in load_instructions:
                flag_op = 'store'
            else:
                flag_op = 'add'

            if station.update(top_mem_queue, flag_op):
                output[station.table_id][2].append(cycle)
            # executar a operação
            if station.has_finished():
                execute(station)

    # escrever resultado
    write_result()

    if pop_mem_queue:
        mem_queue.pop(0)
        pop_mem_queue = False


def stall():
    # atualizar ciclo atual
    global cycle
    update_all()
    cycle += 1


def print_table():
    # VERSÃO ALTERNATIVA
    # Acho que fica menos bonito
    '''
    from pandas import DataFrame

    for i in output:
        output[i][2] = f'{output[i][2][0]}_{output[i][2][-1]}'
    output_db = DataFrame.from_dict(output, orient='index')
    output_db.columns = ['Instrucao', 'Emissao', 'Execucao (inicio_fim)', 'Escreve resultado']
    print(output_db)
    '''

    for i in output:
        tmp = output[i][1:]
        output[i] = output[i][0].split(' ')
        output[i] += tmp
        output[i][3] = f'{output[i][3][0]}_{output[i][3][-1]}'

    # determinar largura máxima de cada coluna
    col_widths = []
    for i in range(5):
        max_width = 0
        for j in output:
            element = output[j][i]
            if len(str(element)) > max_width:
                max_width = len(str(element))
        col_widths.append(max_width)

    col_labels = ['Instrucao', 'Emissao', 'Execucao (inicio_fim)', 'Escrever resultado']
    labels_width = [col_widths[0] + 1 + col_widths[1]] + col_widths[2:]
    labels_width = [labels_width[i] if (labels_width[i] >= len(col_labels[i])) else len(col_labels[i]) for i in range(len(col_labels))]
    col_widths[2:] = labels_width[1:]

    # impressão dos nomes das colunas da tabela
    print(f'| ', end='')
    for i in range(len(col_labels)):
        s_pad = labels_width[i]
        print(f'{col_labels[i] : ^{s_pad}}', end=' | ')
    print(f'\n{"":-<{sum(labels_width) + 13}}')

    # impressão dos dados
    for i in output:
        print(f'| ', end='')
        for j in range(5):
            if j == 0:
                s_pad = col_widths[j] + 1
                print(f'{output[i][j] : <{s_pad}}', end='')
            elif j == 1:
                s_pad = col_widths[1] if labels_width[0] - (col_widths[0] + 1) < 0 else (labels_width[0] - (col_widths[0] + 1))
                print(f'{output[i][j] : <{s_pad}}', end=' | ')
            else:
                s_pad = col_widths[j]
                print(f'{output[i][j] : ^{s_pad}}', end=' | ')
        print('')


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
    init_reg_stat()

    # parsear instruções
    instr_list = parse_instructions(filepath)

    # executar simulação
    for i, instruction in enumerate(instr_list):
        cycle += 1

        update_all()
        emit_instruction(i, instruction)
        
    stop = False
    while not stop:
        stop = True
        cycle += 1

        update_all()
        for station in RS:
            if station.busy:
                stop = False
                break

    # imprimir tabela final
    print_table()