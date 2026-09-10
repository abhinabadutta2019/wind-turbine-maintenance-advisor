# Wind Turbine Maintenance Advisor

## Overview

This project provides a lightweight Wind Turbine Operation and
Maintenance Advisor based on a technical maintenance manual.

The system works in two modes:

-   Offline mode
-   Optional Groq/Llama mode

The offline advisor is the main system and works without any paid API.
Groq/Llama is used only to improve the wording of the final answer.

## Main Features

-   Structured maintenance knowledge base
-   TF-IDF retrieval
-   Rule-based component detection
-   Rule-based intent detection
-   Safety warnings
-   Confidence estimation
-   Evidence chunks from the manual
-   Optional Groq/Llama answer improvement
-   Offline fallback

## Project Structure

``` text
code-july-24/
├── data/
│   ├── chunks.json
│   └── knowledge_base.json
├── reports/
├── src/
│   ├── advisor.py
│   ├── app.py
│   └── llm_answer.py
├── tests/
├── README.md
└── requirements.txt
```

## Running the Advisor

### Offline

``` bash
python src/app.py "How do I maintain the battery?"
```

### With Optional LLM

``` bash
python src/app.py "How do I maintain the battery?" --use-llm
```
