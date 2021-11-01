# Simulador de Tomasulo - Grupo 6

## Execução
Para executar a simulação do algoritmo de Tomasulo, basta executar:

``` python tomasulo_simulator.py [caminho do arquivo em assembly] ```

## Configuração
O arquivo *config.json* contém os parâmetros das unidades funcionais no formato JSON. Os parâmetros "num" e "latency" correspondem respectivamente ao número e à latência das unidades funcionais de cada tipo, sendo "load" a unidade de load-store e "add" uma unidade lógica aritmética. Para alterar os parêmetros, basta modificá-los diretamente no arquivo *config.json*.

## Exemplos
Na pasta *examples* constam alguns exemplos de arquivo em assembly (arquivos *.asm*) e suas respectivas saídas esperadas (arquivos *.txt*). As saídas são esperadas para a seguinte configuração:

*config.json*
```json
{
    "load": {
        "num": 3,
        "latency": 7
    },
    "add": {
        "num": 3,
        "latency": 1
    }
}
```

## Contribuições