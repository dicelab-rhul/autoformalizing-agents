# 🏆 Game-Theoretic Tournaments with Autoformalizing Agents

A Python and Prolog-based tournament simulator that enables users to create, simulate, and analyze game-theoretic tournaments using autoformalizing agents. The project supports game-theoric experiments and includes tools for validating autoformalized Prolog programs. Currently, it supports 2x2 simultaneous-move games, but its modular architecture allows for extensions to other types of games. The framework and its evaluation are described in more detail in this [paper](https://arxiv.org/abs/2412.08805). 

## 📑 Table of Contents

- ✨ [Features](#-features)
- 🚀 [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- ⚙️ [Experiment Configuration](#%EF%B8%8F-experiment-configuration)
- 🗂️ [Project Structure](#%EF%B8%8F-project-structure)
- 📚 [Examples](#-examples)
- 🛠️ [Built With](#%EF%B8%8F-built-with)
- 👥 [Authors](#-authors)
- 📝 [Citing This Work](#citing-this-work)

## ✨ Features

- **Autoformalization of Game Rules and Strategies**: Use agents to autoformalize game rules, strategies, or both using natural language descriptions as input.
- **Configurable Tournament Parameters**: Easily customize the number of agents, rounds, and target payoffs.
- **Results Logging**: Automatically log tournament results for analysis.
- **Modular Design**: Easily extendable and modifiable for other types of games.

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.8 or higher
- `pip` (Python package installer)
- SWI-Prolog (for solving game strategies)
- Git (for cloning the repository)

To use GPT-4 used by default in the framework, the OpenAI API key has to be stored in an environment variable. To use an alternative LLM, an interface provided by [LLM class](src/base_llm.py) has to be implemented. 

### Installation

1. **Clone the Repository**
    ```bash
    git clone https://github.com/dicelab-rhul/autoformalizing-agents.git
    cd autoformalizing-agents
    ```

2. **Create a Virtual Environment**
    ```bash
    python3 -m venv auto-agents-env
    source auto-agents-env/bin/activate  # On Windows, use `auto-agents-env\Scripts\activate`
    ```

3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    
4. **Install SWI-Prolog**:

   - [Download SWI-Prolog](https://www.swi-prolog.org/Download.html) and follow the installation [instructions](https://wwu-pi.github.io/tutorials/lectures/lsp/010_install_swi_prolog.html) for your operating system.    


## ⚙️ Experiment Configuration

A sample configuration file is located at `DATA/CONFIG/sample_config.ini`:

```ini
[Paths]
GAME_DIR = ../DATA/GAMES
OUT_DIR = ../LOGS
SOLVER_PATH = ../src/solver.pl

[Params]
num_agents = 10
num_rounds = 5
target_payoffs = 100;200;150
```

## 🗂️ Project Structure

```bash
autoformalizing-agents/
├── DATA/
│   ├── AGENTS/
│   ├── CONFIG/
│   ├── EVAL/
│   ├── GAMES/
│   ├── GAME_RULES/
│   ├── MISC/
│   ├── PROMPTS/
│   ├── STRATEGIES/
│   └── STRATEGY_DESCRIPTIONS/
├── LOGS/
├── SAMPLE_EXPERIMENTS/
├── llms/
│   └── gpt4.py
├── src/
│   ├── agents
│   ├── agent.py
│   ├── base_llm.py
│   ├── game.py
│   ├── setup_logger.py
│   ├── solver.pl
│   ├── solver.py
│   ├── tournament.py
│   ├── utils.py
│   └── validator.py
├── LICENSE
├── README.md
├── experiment1.py
├── experiment2.py
├── experiment3.py
└── requirements.txt
```

## 📚 Examples
Simple examples are located in [SAMPLE_EXPERIMENTS](SAMPLE_EXPERIMENTS/agent_reading_experiment.py). 
1. **Reading predefined agents**
    ```bash
    python3 agent_reading_experiment.py
    ```
2. **Autoformalizing game descriptions**
    ```bash
    python3 sample_experiment.py
    ```    

## 🛠️ Built With
- Python 🐍
- SWI-Prolog ⚙️
- OpenAI GPT

## 👥 Authors

Agnieszka Mensfelt </br>
Kostas Stathis </br>
Vince Trencsenyi

## Citing This Work

```bibtex
@article{mensfelt24agents,
    author={Agnieszka Mensfelt and Kostas Stathis and Vince Tencsenyi},
    title={Autoformalizing and Simulating Game-Theoretic Scenarios using LLM-augmented Agents},
    year={2024},
    journal={arXiv preprint arXiv:2412.08805},
    url={https://arxiv.org/abs/2412.08805} 
    year={2024}
}
```

Coming soon.
