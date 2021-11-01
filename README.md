# Simulador de Tomasulo - Grupo 6

## Execução
Para executar a simulação do algoritmo de Tomasulo, basta executar:

``` python tomasulo_simulator.py [nome do arquivo em assembly] ```

Na pasta *dataset* constam alguns exemplos de arquivo em assembly (arquivos *.asm*) e suas respectivas saídas esperadas (arquivos *.txt*).

## Configuração
O arquivo *config.json* contém os parâmetros das unidades funcionais no formato JSON. Os parâmetros "num" e "latency" correspondem respectivamente ao número e à latência das unidades funcionais de cada tipo, sendo "load" a unidade de load-store, "add" uma unidade lógica aritmética, e "mult" uma unidade de multiplicação. Para alterar os parêmetros, basta modificá-los diretamente no arquivo *config.json*.

## Contribuições