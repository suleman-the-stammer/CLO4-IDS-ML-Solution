import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.utils import resample
import matplotlib.pyplot as plt
import joblib

df = pd.read_csv("E:\Study\IS\UNSW_NB15_training-set.csv")
if "label" in df.columns:
    target_col = "label"
elif "attack_cat" in df.columns:
    target_col = "attack_cat"
else:
    target_col = df.columns[-1]
y = df[target_col].copy()
X = df.drop(columns=[target_col])
X = X.replace([np.inf, -np.inf], np.nan)
X = X.dropna(axis=0, how="any")
y = y.loc[X.index]
if y.dtype == object:
    y = y.astype(str)
numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
if len(cat_cols) > 0:
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
scaler = StandardScaler()
X[numeric_cols] = scaler.fit_transform(X[numeric_cols])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
if len(np.unique(y_train)) > 2:
    classes = np.unique(y_train)
else:
    classes = np.unique(y_train)
lr = LogisticRegression(max_iter=1000)
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_test)
rf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)
acc_lr = accuracy_score(y_test, y_pred_lr)
acc_rf = accuracy_score(y_test, y_pred_rf)
print("Logistic Regression Accuracy:", acc_lr)
print("Random Forest Accuracy:", acc_rf)
print("\nRandom Forest Classification Report:")
print(classification_report(y_test, y_pred_rf, digits=4))
cm = confusion_matrix(y_test, y_pred_rf, labels=classes)
fig, ax = plt.subplots(figsize=(8,6))
im = ax.imshow(cm, interpolation="nearest")
ax.set_title("Confusion Matrix")
ax.set_xticks(np.arange(len(classes)))
ax.set_yticks(np.arange(len(classes)))
ax.set_xticklabels(classes, rotation=45, ha="right")
ax.set_yticklabels(classes)
for i in range(len(classes)):
    for j in range(len(classes)):
        ax.text(j, i, format(cm[i, j], "d"), ha="center", va="center")
plt.tight_layout()
plt.show()
joblib.dump({"model": rf, "scaler": scaler, "columns": X.columns.tolist()}, "rf_ids_model.joblib")
