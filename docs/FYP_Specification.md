# FYP2 Technical Specification

## 1. Project

**Project Title:**
AI-Based Phishing Detection System Using XGBoost and BERT Techniques for Youth

## 2. Project Goal

Develop an AI-based phishing detection system capable of identifying:

* phishing emails
* phishing URLs

The system is intended as a research prototype for supporting safer online activities among youth users.

## 3. Research Objectives

**Objective 1**
Analyse phishing email and URL characteristics and examine existing machine learning and deep learning-based phishing detection approaches.

**Objective 2**
Design and develop a hybrid AI-based anti-phishing system using BERT and XGBoost for detecting phishing emails and URLs.

**Objective 3**
Evaluate the performance of the proposed phishing email and URL detection system using:

* Accuracy
* Precision
* Recall
* F1-score

## 4. Research Scope

The system focuses on phishing attacks delivered through:

* email
* URLs

The project does not attempt to develop a complete commercial cybersecurity solution.
Mobile applications and browser extensions are outside the project scope.

## 5. Development Environment

Primary development:

* Python
* Visual Studio Code
* Google Colab
* Jupyter Notebook

VS Code is used as the main development workspace.
Google Colab provides the computational runtime for machine learning experiments and GPU-based processing when required.

## 6. Proposed AI Architecture

### Email Detection

```
Email content
  → preprocessing
  → BERT contextual feature extraction
  → XGBoost classification
  → phishing / legitimate
```

### URL Detection

```
URL
  → preprocessing
  → BERT contextual feature extraction
  → URL lexical/structural feature extraction
  → XGBoost classification
  → phishing / legitimate
```

The exact feature combination may be refined during implementation, but any change must remain consistent with the approved research methodology.

## 7. Dataset Strategy

### Phishing URL Dataset

Primary source: **PhishTank**

The project will acquire phishing URL data programmatically from PhishTank.
The acquisition method must be reproducible and should preserve the retrieved raw dataset/snapshot.

### Phishing Email Dataset

A suitable public phishing email dataset will be obtained from an appropriate repository, potentially Kaggle, subject to dataset suitability.
The selected dataset should provide usable email content and phishing/legitimate labels.

### Dataset Principles

Raw datasets must be preserved.

The following information should be recorded where available:

* source
* dataset name
* dataset identifier
* retrieval date
* version
* relevant metadata

## 8. Data Preparation

Datasets will be inspected and prepared before model development.

Required checks include:

* missing values
* duplicate records
* class labels
* class distribution
* irrelevant fields
* inconsistent records
* potential data leakage

Appropriate preprocessing will be applied separately to email and URL data where necessary.

## 9. BERT

BERT is primarily used as a contextual feature extractor.

For email data, BERT will process textual email content.
For URL data, BERT may process the URL string as a textual sequence, while additional lexical and structural URL features may also be considered.

The extracted representations will be used as input features for XGBoost.

## 10. XGBoost

XGBoost is the primary classification component.

It will use the extracted BERT representations and relevant engineered features to classify samples as:

* phishing
* legitimate

Important hyperparameters may include:

* learning rate
* maximum tree depth
* number of estimators

Hyperparameters must be recorded for reproducibility.

## 11. Experimental Evaluation

The project should evaluate the proposed model using:

* Accuracy
* Precision
* Recall
* F1-score

Where appropriate, baseline models should be included so that the proposed hybrid approach can be meaningfully compared against alternative approaches.

All reported results must come from actual experiments.

## 12. Data Leakage Prevention

The project must prevent information from the test set being used during model training or model selection.

Train/test separation must be established before model training.

Any preprocessing operation that learns information from data must be handled carefully to avoid leakage.

## 13. Reproducibility

Experiments should record:

* dataset/source
* dataset version
* train/test split
* preprocessing steps
* model configuration
* hyperparameters
* random seed where applicable
* evaluation results

## 14. Prototype

A web-based prototype will allow users to submit:

* suspicious email content
* suspicious URLs

The system will return a phishing/legitimate classification result.

The prototype is intended to demonstrate the practical application of the proposed model rather than commercial deployment.

## 15. Development Methodology

The development process follows CRISP-DM and is aligned with the project's research objectives:

1. Business understanding / requirement analysis
2. Data understanding
3. Data preparation
4. Modelling
5. Evaluation
6. Prototype/deployment

## 16. Development Rules

Claude Code must:

* follow this specification
* avoid changing the approved research direction silently
* avoid unnecessary technologies
* avoid inventing results
* avoid modifying raw datasets
* preserve reproducibility
* explain important implementation decisions
* develop the system incrementally
* stop at the requested development stage unless instructed otherwise

## 17. Current Development Status

This document defines the **intended** system.

Actual progress, completed tasks, current problems and next steps are recorded separately in:

`docs/PROJECT_STATE.md`

Its purpose is to help Claude Code understand how the project actually looks at any point in time, and to define the flow followed each time a new development step is taken.
