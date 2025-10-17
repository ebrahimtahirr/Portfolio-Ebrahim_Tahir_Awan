📊 Customer Churn Prediction Dashboard

Live App: https://ebrahimtahirr-customer-churn-dashboard.hf.space
Tech Stack: Python · Scikit-learn · Streamlit · Hugging Face Spaces

🧠 Overview

This interactive web app predicts the likelihood of customer churn for a telecom company using a Logistic Regression model.
The model was trained on the IBM Telco dataset and deployed using Streamlit on Hugging Face Spaces.
The dashboard allows users to input customer details, instantly get churn probability, visualize key feature impacts, and interpret business insights.

⚙️ Tools & Libraries
Data Prep: pandas, numpy
Modeling: scikit-learn (Pipeline, Logistic Regression)
Visualization: matplotlib, seaborn
Deployment: streamlit, joblib
Platform: Hugging Face Spaces

🧩 Dataset Summary

Source: IBM Telco Customer Churn dataset
Size: ~7,043 records
Target: Churn (Yes / No)
Key Features:
Demographics: SeniorCitizen, Partner, Dependents
Services: InternetService, StreamingTV, OnlineSecurity, etc.
Financials: MonthlyCharges, TotalCharges, Contract type, etc.

🧮 Model Pipeline

Preprocessing:

Encodes categorical variables using OneHotEncoder
Standardizes numeric features using StandardScaler
Combines preprocessing with ColumnTransformer

Modeling:
Logistic Regression (fast, interpretable, and robust)
Evaluated with Accuracy, ROC-AUC, and Classification Report

Deployment:
Trained pipeline exported with joblib
Streamlit app loads the model and provides an interactive front-end

🎨 Dashboard Features:

🧾 Real-time churn prediction with input sliders & dropdowns
📈 Probability output with clear “High” or “Low Risk” flag

📊 Graphs visualizing:

Feature importance
Churn probability distribution
Tenure vs Monthly Charges relationship

💡 Business Insights auto-generated in the app
These insights help managers focus retention strategies on at-risk customers.

🧑‍💼 Author

M.Ebrahim Tahir Awan
📍 MS Business Analytics @ Arizona State University
💼 Aspiring Business Analyst & Strategy Consultant
