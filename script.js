function validateInputs() {
  const age = parseFloat(document.getElementById("age").value);
  const income = parseFloat(document.getElementById("income").value);
  const loanAmount = parseFloat(document.getElementById("loanAmount").value);
  const creditScore = parseFloat(document.getElementById("creditScore").value);
  const interestRate = parseFloat(document.getElementById("interestRate").value);
  const loanTerm = parseFloat(document.getElementById("loanTerm").value);

  const errors = [];

  if (isNaN(age) || age < 18 || age > 80) {
    errors.push("Age must be between 18 and 80 years");
  }

  if (isNaN(income) || income < 0 || income > 500000) {
    errors.push("Monthly Income must be between ฿0 and ฿500,000");
  }

  if (isNaN(loanAmount) || loanAmount < 0 || loanAmount > 10000000) {
    errors.push("Loan Amount must be between ฿0 and ฿10,000,000");
  }

  if (isNaN(creditScore) || creditScore < 300 || creditScore > 850) {
    errors.push("Credit Score must be between 300 and 850");
  }

  if (isNaN(interestRate) || interestRate < 0 || interestRate > 50) {
    errors.push("Interest Rate must be between 0% and 50%");
  }

  if (isNaN(loanTerm) || loanTerm < 1 || loanTerm > 30) {
    errors.push("Loan Term must be between 1 and 30 years");
  }


  return errors;
}

function displayErrors(errors) {
  const resultDiv = document.getElementById("result");
  resultDiv.innerHTML = '<div class="error-message">' + errors.join('<br>') + '</div>';
  resultDiv.style.color = 'red';
}

function displayResult(result) {
  const resultDiv = document.getElementById("result");
  
  if (result.includes("APPROVED")) {
    const lines = result.split('\n');
    resultDiv.innerHTML = `<div class="percentage">${lines[0]}</div><div class="status approved">${lines[2]}</div>`;
  } else if (result.includes("DENIED")) {
    const lines = result.split('\n');
    resultDiv.innerHTML = `<div class="percentage">${lines[0]}</div><div class="status denied">${lines[2]}</div>`;
  } else if (result.includes("UNCERTAIN")) {
    const lines = result.split('\n');
    const percentage = lines[0];
    const status = lines[2];
    const details = lines.slice(4).join('\n');
    resultDiv.innerHTML = `<div class="percentage">${percentage}</div><div class="status uncertain">${status}</div><div style="text-align: left; font-size: 16px; margin-top: 20px;">${details}</div>`;
  } else {
    resultDiv.innerHTML = '<div class="error-message">' + result + '</div>';
  }
}

document.getElementById("loanForm").addEventListener("submit", function(e) {
  e.preventDefault();

  const validationErrors = validateInputs();
  if (validationErrors.length > 0) {
    displayErrors(validationErrors);
    return;
  }

  const age = parseFloat(document.getElementById("age").value);
  const income = parseFloat(document.getElementById("income").value);
  const loanAmount = parseFloat(document.getElementById("loanAmount").value);
  const creditScore = parseFloat(document.getElementById("creditScore").value);
  const interestRate = parseFloat(document.getElementById("interestRate").value);
  const loanTerm = parseFloat(document.getElementById("loanTerm").value);
  const mortgage = document.getElementById("mortgage").value;
  const employment = document.getElementById("employment").value;

  const annualIncome = income * 12;
  let score = (annualIncome / loanAmount) * (creditScore / 850);
  score -= interestRate / 100;
  if (mortgage === "yes") score -= 0.15;
  
  if (age < 25) {
    score -= 0.2;
  } else if (age > 65) {
    score -= 0.3;
  } else if (age >= 35 && age <= 50) {
    score += 0.1;
  }
  
  if (employment === "unemployed") {
    score -= 0.4;
  } else if (employment === "parttime") {
    score -= 0.2;
  } else if (employment === "selfemployed") {
    score -= 0.1;
  } else if (employment === "fulltime") {
    score += 0.1;
  }
  
  const loanTermImpact = Math.max(-0.5, (15 - loanTerm) * 0.05);
  score += loanTermImpact;

  const approvalChance = Math.max(0, Math.min(100, score * 100));
  
  let result;
  if (approvalChance >= 60) {
    result = `${approvalChance.toFixed(1)}%\n\nAPPROVED`;
  } else if (approvalChance <= 40) {
    result = `${approvalChance.toFixed(1)}%\n\nDENIED`;
  } else {
    const recommendations = [];
    if (creditScore < 650) {
      recommendations.push("Improve credit score to 650+");
    }
    if (income / loanAmount < 3) {
      recommendations.push("Consider lower loan amount");
    }
    if (interestRate > 15) {
      recommendations.push("Try to get better interest rate");
    }
    if (employment === "unemployed") {
      recommendations.push("Get stable employment");
    }
    
    const positiveFactors = [];
    if (creditScore >= 650) {
      positiveFactors.push("Good credit score");
    }
    if (income / loanAmount >= 3) {
      positiveFactors.push("Reasonable debt-to-income ratio");
    }
    if (employment === "fulltime" || employment === "selfemployed") {
      positiveFactors.push("Stable employment");
    }
    if (interestRate <= 10) {
      positiveFactors.push("Competitive interest rate");
    }
    
    result = `${approvalChance.toFixed(1)}%\n\nUNCERTAIN\n\nPositive factors:\n${positiveFactors.join('\n')}\n\nRecommendations:\n${recommendations.join('\n')}`;
  }
  
  displayResult(result);
});
