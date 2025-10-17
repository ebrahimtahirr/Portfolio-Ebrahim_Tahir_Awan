# =========================================================
# 📊 Customer Churn Prediction Dashboard (Final Portfolio Version)
# =========================================================
import streamlit as st
import pandas as pd
import joblib, pickle, warnings
import matplotlib.pyplot as plt
import numpy as np

warnings.filterwarnings("ignore")

# ---------------------------------------------------------
# ✅ Streamlit Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Customer Churn Prediction Dashboard",
    layout="wide",
    page_icon="📈"
)

# ---------------------------------------------------------
# 🧠 App Title
# ---------------------------------------------------------
st.title("📊 Customer Churn Prediction Dashboard")
st.write("""
This interactive dashboard uses a **Logistic Regression model**
to predict the likelihood of customer churn and visualize key insights.
""")

# ---------------------------------------------------------
# ⚙️ Load Model (with compatibility fallback)
# ---------------------------------------------------------
@st.cache_resource
def load_model():
    try:
        model = joblib.load("churn_model.joblib")
        st.success("✅ Model loaded successfully!")
        return model
    except AttributeError as e:
        st.warning(f"⚠️ Version mismatch detected: {e}")
        try:
            with open("churn_model.joblib", "rb") as f:
                model = pickle.load(f)
            st.success("✅ Model loaded (compatibility mode)!")
            return model
        except Exception as e2:
            st.error(f"❌ Failed to load model: {e2}")
            return None

model = load_model()

# ---------------------------------------------------------
# 🧮 Sidebar Inputs
# ---------------------------------------------------------
st.sidebar.header("Enter Customer Information")

tenure = st.sidebar.slider("Tenure (months)", 0, 72, 12)
monthly = st.sidebar.number_input("Monthly Charges ($)", 0.0, 150.0, 70.0)
total = st.sidebar.number_input("Total Charges ($)", 0.0, 10000.0, 1000.0)
senior = st.sidebar.selectbox("Senior Citizen", ["No", "Yes"])
partner = st.sidebar.selectbox("Has Partner", ["No", "Yes"])
dependents = st.sidebar.selectbox("Has Dependents", ["No", "Yes"])
contract = st.sidebar.selectbox("Contract Type", ["Month-to-month", "One year", "Two year"])
device = st.sidebar.selectbox("Device Protection", ["No", "Yes", "No internet service"])
internet = st.sidebar.selectbox("Internet Service", ["Fiber optic", "DSL", "No"])

# Encode categorical values
senior_val = 1 if senior == "Yes" else 0

# ---------------------------------------------------------
# 🔮 Prediction Logic
# ---------------------------------------------------------
if st.button("🔮 Predict Churn"):
    if model is None:
        st.error("Model not loaded. Please ensure churn_model.joblib is uploaded.")
    else:
        # ✅ Send same raw column names as during model training
        X_input = pd.DataFrame([{
            'SeniorCitizen': senior_val,
            'tenure': tenure,
            'MonthlyCharges': monthly,
            'TotalCharges': total,
            'Partner': partner,
            'Dependents': dependents,
            'Contract': contract,
            'DeviceProtection': device,
            'InternetService': internet
        }])

        try:
            pred = model.predict(X_input)[0]
            prob = model.predict_proba(X_input)[0][1]

            # ---------------------------------------------------------
            # 🎯 Prediction Result Section
            # ---------------------------------------------------------
            st.subheader("📈 Prediction Result")
            col1, col2 = st.columns([2, 3])

            with col1:
                if pred == 1:
                    st.error(f"⚠️ **High Risk of Churn**")
                else:
                    st.success(f"✅ **Low Risk of Churn**")
                st.markdown(f"**Churn Probability:** `{prob:.2f}`")

            with col2:
                fig, ax = plt.subplots(figsize=(4, 2))
                ax.set_xlim(0, 1)
                ax.barh([0], [prob], color="crimson" if prob > 0.5 else "seagreen")
                ax.set_yticks([])
                ax.set_xlabel("Churn Probability", fontsize=10)
                ax.set_title("Customer Churn Likelihood", fontsize=11)
                st.pyplot(fig)

            # ---------------------------------------------------------
            # 🧩 Feature Importance Visualization
            # ---------------------------------------------------------
            st.subheader("🔍 Key Feature Influence")
            try:
                feature_names = model.named_steps['model'].coef_[0]
                cols = model.named_steps['preprocessor'].get_feature_names_out()
                importances = pd.Series(feature_names, index=cols).sort_values(key=abs, ascending=False)[:8]

                fig2, ax2 = plt.subplots(figsize=(6, 3))
                importances.plot(kind="barh", ax=ax2, color="dodgerblue")
                ax2.set_title("Top Predictive Features")
                ax2.set_xlabel("Coefficient Impact")
                st.pyplot(fig2)
            except Exception:
                st.info("Feature importance visualization not available for this model type.")

            # ---------------------------------------------------------
            # 💡 Business Insights Section
            # ---------------------------------------------------------
            st.subheader("💡 Business Insights")

            if prob > 0.7:
                st.warning("""
                **Customer at High Risk:**  
                - Likely has month-to-month contract or high monthly charges.  
                - Recommend retention offers or personalized loyalty discounts.  
                - Focus on customer experience improvements and proactive support.
                """)
            elif 0.4 < prob <= 0.7:
                st.info("""
                **Medium Risk Segment:**  
                - Moderate risk based on tenure and service bundle.  
                - Increase engagement with bundled packages or streaming offers.  
                - Automatic payments and contract renewals help stabilize churn.
                """)
            else:
                st.success("""
                **Loyal Customer Segment:**  
                - Long-term and low-maintenance customers.  
                - Maintain loyalty with referral rewards or family plans.  
                - Use satisfaction surveys to further strengthen retention.
                """)

        except Exception as e:
            st.error(f"Prediction failed: {e}")

# ---------------------------------------------------------
# ℹ️ Footer
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.info("""
**About this app:**  
Built with Streamlit + Scikit-learn  
Model: Logistic Regression  
Author: Ebrahim Tahir  
""")
