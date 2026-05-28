# Simulador SEP - 13 Barras (TCC)

Este é um aplicativo desktop interativo para simulação e análise de Sistemas Elétricos de Potência (SEP) baseado em um sistema de 13 barras.

## Características:
- **Fluxo de Potência**: Utiliza `pandapower` para calcular tensões nodais, fluxo de potência e perdas nas linhas.
- **Análise Modal**: Avalia a estabilidade de tensão através dos autovalores e fatores de participação do sistema.
- **Curva PV**: Gera iterativamente a curva de tensão por potência (Curva do Nariz), mostrando o ponto de colapso de tensão.
- **Interface Gráfica Interativa**:
    - Desenvolvido em `PyQt6` com um tema escuro (*Dark Mode*).
    - Diagrama unifilar desenhado com `QGraphicsView`.
    - Edição de parâmetros da rede (Cargas, Geração, Impedâncias) com duplo clique sobre barras ou linhas.
    - Gráficos integrados gerados com `matplotlib`.
- **Multithreading**: A simulação roda num `QThread` à parte, evitando travamentos da interface.

## Requisitos de Sistema:
- Python 3.8+

## Como Instalar

```bash
pip install PyQt6 pandapower matplotlib scipy
```

## Como Executar

Execute o script principal a partir da raiz do projeto:

```bash
python main.py
```

## Arquitetura (6 Arquivos):
1. `data_models.py`: Gerenciamento de Estado e Dados usando DataClasses.
2. `engine_sep.py`: Motor de Cálculo Elétrico (`pandapower`, `scipy`).
3. `diagram_view.py`: Visualização Interativa da Rede (`QGraphicsScene`).
4. `plot_utils.py`: Geração de Gráficos e Tabelas (`matplotlib`).
5. `ui_main.py`: Definição da Interface do Usuário (Layouts em abas, QSS).
6. `main.py`: Controlador Central e *Entry Point*.
