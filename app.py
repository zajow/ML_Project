import os
import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
import gradio as gr

ROOT = os.path.dirname(__file__)
ML_CSV = os.path.join(ROOT, "..", "ML", "ML_Project", "Loan_default.csv")
MODEL_PATH = os.path.join(ROOT, "loan_model.joblib")


def load_data():
    df = pd.read_csv(ML_CSV)
    return df


def build_and_train(save=True):
    df = load_data()

    col_map = {
        'Income': 'Income',
        'Income(USD)': 'Income',
        'LoanAmount': 'LoanAmount',
        'Loan_Amount': 'LoanAmount',
        'CreditScore': 'CreditScore',
        'Credit_Score': 'CreditScore',
        'InterestRate': 'InterestRate',
        'Interest_Rate(%)': 'InterestRate',
        'LoanTerm': 'LoanTerm',
        'Loan_Term(months)': 'LoanTerm',
        'HasMortgage': 'HasMortgage',
        'HasMortagage': 'HasMortgage',
        'EmploymentType': 'EmploymentType',
        'Default': 'Default'
    }

    for k, v in col_map.items():
        if k in df.columns and v not in df.columns:
            df = df.rename(columns={k: v})

    if 'Default' not in df.columns:
        raise RuntimeError('Could not find target column "Default" in CSV')

    df = df.dropna(subset=['Default'])

    features = ['Age', 'Income', 'LoanAmount', 'CreditScore', 'InterestRate', 'LoanTerm', 'HasMortgage', 'EmploymentType']
    for f in features:
        if f not in df.columns:
            if f == 'HasMortgage':
                df[f] = False
            elif f == 'EmploymentType':
                df[f] = 'fulltime'
            elif f == 'Age':
                df[f] = 35
            else:
                df[f] = 0

    X = df[features].copy()
    y = df['Default'].astype(int)

    X['HasMortgage'] = X['HasMortgage'].replace({"Yes": True, "No": False, "yes": True, "no": False}).infer_objects(copy=False).astype(bool)

    if X['LoanTerm'].median() > 50:
        X['LoanTerm'] = X['LoanTerm'] / 12.0

    cat_cols = ['EmploymentType']
    num_cols = ['Age', 'Income', 'LoanAmount', 'CreditScore', 'InterestRate', 'LoanTerm', 'HasMortgage']

    preproc = ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols)
    ], remainder='passthrough')

    model = make_pipeline(preproc, LogisticRegression(max_iter=1000))

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    model.fit(X_train, y_train)

    if save:
        joblib.dump(model, MODEL_PATH)

    score = model.score(X_test, y_test)
    return model, score


def get_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    else:
        model, score = build_and_train(save=True)
        return model


model = None
try:
    model = get_model()
except Exception as e:
    print('Model load/train failed:', e)


def validate_inputs(age, income, loanAmount, creditScore, interestRate, loanTerm, mortgage, employment):
    errors = []
    
    if age is None or age < 18 or age > 80:
        errors.append("Age must be between 18 and 80 years")
    
    if income is None or income < 0 or income > 500000:
        errors.append("Monthly Income must be between ฿0 and ฿500,000")
    
    if loanAmount is None or loanAmount < 0 or loanAmount > 10000000:
        errors.append("Loan Amount must be between ฿0 and ฿10,000,000")
    
    if creditScore is None or creditScore < 300 or creditScore > 850:
        errors.append("Credit Score must be between 300 and 850")
    
    if interestRate is None or interestRate < 0 or interestRate > 50:
        errors.append("Interest Rate must be between 0% and 50%")
    
    if loanTerm is None or loanTerm < 1 or loanTerm > 30:
        errors.append("Loan Term must be between 1 and 30 years")
    
    
    if mortgage not in ['yes', 'no', 'Yes', 'No', True, False]:
        errors.append("Mortgage status must be 'yes' or 'no'")
    
    valid_employment = ['fulltime', 'parttime', 'selfemployed', 'unemployed']
    if employment not in valid_employment:
        errors.append(f"Employment status must be one of: {', '.join(valid_employment)}")
    
    return errors

def predict(age, income, loanAmount, creditScore, interestRate, loanTerm, mortgage, employment):
    validation_errors = validate_inputs(age, income, loanAmount, creditScore, interestRate, loanTerm, mortgage, employment)
    if validation_errors:
        return f'<div class="error-message">{"<br>".join(validation_errors)}</div>'
    
    row = {
        'Age': [float(age)],
        'Income': [float(income)],
        'LoanAmount': [float(loanAmount)],
        'CreditScore': [float(creditScore)],
        'InterestRate': [float(interestRate)],
        'LoanTerm': [float(loanTerm)],
        'HasMortgage': [True if mortgage in ('yes', 'Yes', True) else False],
        'EmploymentType': [employment]
    }
    X = pd.DataFrame(row)
    if model is None:
        return '<div class="error-message">Model not available</div>'

    try:
        annual_income = income * 12
        row['Income'] = [annual_income * 33]
        row['LoanAmount'] = [loanAmount * 33]
        X = pd.DataFrame(row)
        
        prob_default = float(model.predict_proba(X)[0, 1])
        base_approval_chance = (1 - prob_default) * 100
        
        age_impact = 0
        if age < 25:
            age_impact = -20
        elif age > 65:
            age_impact = -30
        elif age >= 35 and age <= 50:
            age_impact = 10
            
        employment_impact = 0
        if employment == "unemployed":
            employment_impact = -40
        elif employment == "parttime":
            employment_impact = -20
        elif employment == "selfemployed":
            employment_impact = -10
        elif employment == "fulltime":
            employment_impact = 10
            
        loan_term_impact = max(-50, (15 - loanTerm) * 5)
        
        approval_chance = base_approval_chance + age_impact + employment_impact + loan_term_impact
        approval_chance = max(0, min(100, approval_chance))
        
        percentage_html = f'<div class="percentage animated">{approval_chance:.1f}%</div>'
        
        if approval_chance >= 60:
            status_html = f'<div class="status approved animated">APPROVED</div>'
        elif approval_chance <= 40:
            status_html = f'<div class="status denied animated">DENIED</div>'
        else:
            status_html = f'<div class="status uncertain animated">UNCERTAIN</div>'
        
        return percentage_html + status_html
        
    except Exception as e:
        return f'<div class="error-message">Prediction error: {e}</div>'
def launch_interface():
    custom_css = """
    .percentage {
        font-size: 72px;
        font-weight: 900;
        color: #0077ff;
        text-align: center;
        margin: 20px 0;
        opacity: 0;
        transform: scale(0.5);
        transition: all 0.8s ease-out;
    }
    
    .percentage.animated {
        opacity: 1;
        transform: scale(1);
    }
    
    .status {
        font-size: 48px;
        font-weight: 900;
        text-align: center;
        margin: 20px 0;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.6s ease-out 0.3s;
    }
    
    .status.animated {
        opacity: 1;
        transform: translateY(0);
    }
    
    .status.approved {
        color: #28a745;
    }
    
    .status.denied {
        color: #dc3545;
    }
    
    .status.uncertain {
        color: #ffc107;
    }
    
    .error-message {
        background-color: #ffe6e6;
        border: 1px solid #ffcccc;
        color: #d63384;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
    }
    """
    
    with gr.Blocks(title="Loan Approval Prediction", css=custom_css) as demo:
        gr.Markdown("# Thai Loan Approval Prediction")
        gr.Markdown("Enter your loan application details in Thai Baht to get your approval percentage.")
        
        with gr.Row():
            with gr.Column():
                age = gr.Number(label="Age", value=35, minimum=18, maximum=80)
                income = gr.Number(label="Monthly Income (THB)", value=30000, minimum=0, maximum=500000, step=1)
                loan_amount = gr.Number(label="Loan Amount (THB)", value=500000, minimum=0, maximum=10000000, step=1)
                credit_score = gr.Number(label="Credit Score", value=700, minimum=300, maximum=850)
                interest_rate = gr.Number(label="Interest Rate (%)", value=5.0, minimum=0, maximum=50, step=0.01)
                loan_term = gr.Number(label="Loan Term (Years)", value=5, minimum=1, maximum=30)
                mortgage = gr.Dropdown(choices=["yes", "no"], label="Has Mortgage?", value="no")
                employment = gr.Dropdown(choices=["fulltime", "parttime", "selfemployed", "unemployed"], label="Employment Status", value="fulltime")
                
                predict_btn = gr.Button("Get Prediction", variant="primary")
            
            with gr.Column():
                result_display = gr.HTML("")
        
        predict_btn.click(
            fn=predict,
            inputs=[age, income, loan_amount, credit_score, interest_rate, loan_term, mortgage, employment],
            outputs=result_display
        )
    
    demo.launch(server_name='0.0.0.0')


if __name__ == '__main__':
    launch_interface()
