FINAL SHORT REPORT

1. Project Goal

This project implements a lightweight Wind Turbine Operation and Maintenance Advisor based on a technical manual.

The advisor is designed to be simple, reproducible, easy to demonstrate, and usable from the command line.

The main system works offline. Groq/Llama is used only as an optional layer to improve the wording of the answer.

2. System Architecture

The system has two modes:

1. Offline mode
2. Optional Groq/Llama mode

The offline mode uses:

- data/knowledge_base.json
- data/chunks.json
- TF-IDF retrieval
- rule-based component detection
- rule-based intent detection
- general-topic detection
- safety-topic detection
- safety warnings
- manual evidence chunks

The process is simple.

The user enters a question through src/app.py.

The app calls the offline advisor in src/advisor.py.

The advisor detects the component, intent, and safety topics. It then creates an answer using the structured knowledge base and retrieves relevant manual chunks using TF-IDF.

The final answer includes confidence, tools or materials, safety warnings, and evidence from the manual.

When --use-llm is selected, src/llm_answer.py improves only the wording of the offline answer.

3. Offline Advisor

The offline advisor is the main part of the project.

It performs:

- question normalization
- component detection
- intent detection
- general-topic detection
- TF-IDF retrieval
- confidence calculation
- safety-warning collection
- offline answer generation

The main function is:

generate_offline_answer(question: str) -> dict

The offline command is:

python src/app.py "How do I maintain the battery?"

This command works without Groq, Llama, internet access, or paid token usage.

4. Optional Groq/Llama Layer

The optional LLM mode is started with:

python src/app.py "How do I maintain the battery?" --use-llm

The offline advisor always runs first.

Groq/Llama receives only:

- the user question
- the offline answer
- the safety warnings
- the top retrieved manual chunks

The LLM is instructed to improve wording only.

It must preserve the technical meaning, keep the same number of instructions, avoid adding new information, and avoid removing safety warnings.

The full manual is never sent to Groq/Llama.

If Groq is unavailable or the API key is missing, the application automatically returns the offline answer.

5. Safety Behavior

The safety layer works offline.

The system can detect and display warnings related to:

- electrical hazards
- short circuits
- batteries
- magnets
- blades and moving parts
- tower lowering and raising
- damaged cables
- personal protective equipment

Safety warnings are based on the structured knowledge base and manual-supported rules.

Evidence chunks are displayed with every answer.

6. Example Outputs

The complete outputs for the eight required demo questions are saved in:

reports/demo_outputs_offline.txt

The eight questions are:

1. How do I maintain the battery?
2. What are the risks with magnets?
3. What should I do if there is rust?
4. How do I inspect the blades?
5. What safety equipment should I wear?
6. What should I check in the tower?
7. What should I do in case of short circuit?
8. How do I maintain the cable?

Example:

Question:
What safety equipment should I wear?

Detected intent:
safety

Detected component:
general safety

Confidence:
high

Answer:

1. Wear protective gloves.
2. Wear safety shoes.
3. Wear a safety helmet.
4. Work carefully and make sure everyone nearby behaves responsibly.

Safety warnings:

- Safety must remain the primary concern during all maintenance operations.
- Be attentive to both electrical and mechanical risks.

Evidence from manual:

- chunk_id: 9
- chunk_id: 50
- chunk_id: 53

The offline and Groq/Llama modes were also tested together.

The LLM preserved the technical content and did not replace the offline advisor.

7. Limitations

The current system has some limitations.

Component detection is based on aliases and rules.

Intent detection is based on keywords.

TF-IDF retrieval depends on word overlap.

Some retrieved chunks may contain additional surrounding text.

The structured knowledge base does not include every detail from the manual.

Groq mode requires internet access and a valid API key.

These limitations were accepted to keep the system simple, reproducible, and easy to demonstrate.

8. Conclusion

The project provides a working command-line Wind Turbine Operation and Maintenance Advisor.

The system works offline using TF-IDF retrieval and a structured knowledge base.

It displays confidence, safety warnings, and supporting evidence from the manual.

Groq/Llama is used only as an optional wording layer.

The core advisor remains fully usable without paid token usage.
