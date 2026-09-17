# FYP2 Project Instructions

## Project Title

AI-Based Phishing Detection System Using XGBoost and BERT Techniques for Youth

## Project Purpose

This repository contains the implementation of my Final Year Project.

The system is designed to detect:

1. Phishing emails
2. Phishing URLs

The project is a research prototype and is not intended to be a commercial cybersecurity product.

## Approved Research Objectives

### Objective 1

Analyse phishing email and URL characteristics and examine existing machine learning and deep learning-based phishing detection approaches.

### Objective 2

Design and develop a hybrid AI-based anti-phishing system using BERT and XGBoost for detecting phishing emails and URLs.

### Objective 3

Evaluate the performance of the proposed phishing email and URL detection system using:

* Accuracy
* Precision
* Recall
* F1-score

## Approved Methodology

The technical development follows CRISP-DM.

Relevant development stages include:

1. Dataset collection
2. Data understanding
3. Data preparation
4. BERT feature extraction
5. XGBoost classification
6. Model training
7. Prototype development
8. Evaluation

## Core Model

BERT:

* Used primarily for contextual feature extraction.
* Produces contextual feature representations.

XGBoost:

* Used as the classification model.
* Receives the extracted feature representations and relevant engineered features.
* Produces phishing or legitimate classification.

## Development Environment

Primary environment:

* Python
* Google Colab
* VS Code
* Jupyter notebooks

Google Colab provides the remote computational runtime and GPU when required.

VS Code is the main development environment.

Claude Code is the development agent.

## Dataset

The project focuses on phishing and legitimate email and URL data.

PhishTank is one of the primary sources for phishing URL data according to the approved project methodology.

Do not invent dataset properties.

Always inspect the actual dataset before making assumptions.

## Important Research Rules

1. Do not change the approved research objectives without explicit instruction.

2. Do not silently change the BERT + XGBoost methodology.

3. Do not invent experimental results.

4. Never claim a model is better without actual experimental comparison.

5. Avoid data leakage.

6. Never use the test set for model training or model selection.

7. Keep preprocessing reproducible.

8. Use fixed random seeds where appropriate.

9. Record important model parameters and experiment settings.

10. Keep the implementation suitable for an undergraduate Final Year Project.

11. Prefer understandable and defensible approaches over unnecessary complexity.

12. Do not introduce additional models merely to make the project appear more advanced.

13. Clearly distinguish:

* approved methodology
* implementation decision
* optional experiment
* recommendation

14. If the report and implementation conflict, identify the conflict before changing anything.

## Development Behaviour

For substantial tasks:

1. Inspect the existing project.
2. Explain your understanding of the task.
3. Identify affected files.
4. Create an implementation plan.
5. Wait for approval before major architectural changes.
6. Implement incrementally.
7. Run the relevant tests or notebook cells.
8. Inspect the output.
9. Fix actual errors rather than guessing.
10. Summarise what changed.

Do not rewrite unrelated code.

Do not delete working code unless there is a clear reason.

## Notebook Development Rule

When a task explicitly targets a `.ipynb` file:

* The notebook itself is the primary artifact.
* Modify the `.ipynb` file directly.
* Do not substitute a `.py` script for the requested notebook work.
* Preserve existing notebook cells unless modification is required.
* After editing, reopen and verify the actual `.ipynb` file.
* If notebook execution is requested, execute the relevant cells using the active Jupyter/Colab kernel.
* Only update `docs/PROJECT_STATE.md` after the notebook change has been successfully verified.

## Machine Learning Discipline

For every experiment, record:

* Dataset
* Number of samples
* Class distribution
* Train/validation/test split
* Preprocessing
* Feature extraction method
* Model
* Important hyperparameters
* Random seed
* Evaluation metrics
* Execution time when relevant
* Results
* Interpretation

All reported results must come from actual execution.

## Google Colab

When working with notebooks:

* Assume the notebook may execute on a remote Google Colab runtime.
* Do not assume local GPU availability.
* Check CUDA/GPU availability before GPU-dependent work.
* Keep installation cells reproducible.
* Avoid unnecessary package installations.
* Do not assume files exist on the Colab runtime unless they are actually available.
* Separate persistent project files from temporary runtime files.

## Code Style

Use clear Python code.

Prefer:

* descriptive variable names
* modular functions
* reusable components
* comments for important ML logic
* type hints where useful
* error handling where appropriate

Avoid unnecessarily complicated abstractions.

## Project Documents

Two documents in `docs/` extend these instructions. Read both at the start of any substantial task.

| Document | Question it answers |
| --- | --- |
| `docs/FYP_Specification.md` | What is the system meant to be? (objectives, scope, architecture, dataset strategy, rules) |
| `docs/PROJECT_STATE.md` | Where are we now? (current stage, dataset, model, experiments, results, known problems, next task) |

## Current Development Stage

Do not record the current stage or current task here.

The single source of truth for current stage, current task, and progress is `docs/PROJECT_STATE.md`.

Update `docs/PROJECT_STATE.md` at the end of every working session, and whenever the stage, dataset, model, experiments, results, or known problems change.

## Important Instruction

Do not build the entire project in one step.

The project must be developed stage by stage.
