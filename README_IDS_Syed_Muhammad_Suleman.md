
# Intrusion Detection System (IDS) using Machine Learning

## Overview
This project demonstrates the implementation of a Machine Learning-based Intrusion Detection System (IDS) using the **UNSW-NB15 dataset**. It aims to classify network traffic into normal or malicious categories to improve cybersecurity monitoring and prevention.

## Dataset
- **Name:** UNSW-NB15 Dataset  
- **Source:** [UNSW Canberra Cyber Range Lab](https://research.unsw.edu.au/projects/unsw-nb15-dataset)
- **Description:** Contains realistic modern network traffic with normal and multiple attack types (DoS, Fuzzers, Reconnaissance, Exploits, etc.).

## Features
- Data preprocessing (encoding, scaling, missing values handling)
- Supervised ML algorithms: Logistic Regression, Random Forest
- Model evaluation with accuracy, precision, recall, F1-score, and confusion matrix
- Model persistence using `joblib`

## File Structure
```
IDS-Project/
│
├── UNSW_NB15.csv
├── ids_model.py
├── rf_ids_model.joblib
├── IDS_Report_Syed_Muhammad_Suleman.docx
└── README.md
```

## Installation
```bash
pip install pandas numpy scikit-learn matplotlib joblib
```

## How to Run
1. Place the dataset (`UNSW_NB15.csv`) in the same directory.
2. Run the Python script:
```bash
python ids_model.py
```
3. The script will output model performance metrics and a confusion matrix plot.
4. The trained model will be saved as `rf_ids_model.joblib`.

## Results Summary
- Logistic Regression: Moderate accuracy, good for baseline.
- Random Forest: Higher accuracy and recall, better detection of diverse attacks.
- Recall emphasized for minimizing false negatives (missed attacks).

## Future Enhancements
- Deep Learning models (LSTM/Autoencoder)
- Online learning for live intrusion detection
- Integration with SIEM tools for automated alerts

## Author
**Name:** Syed Muhammad Suleman  
**Enrollment:** 03-134221-038  
**Date:** October 2025
