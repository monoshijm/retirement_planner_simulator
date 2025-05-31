# financial_models.py

import numpy as np
import pandas as pd
from scipy.stats import norm

def calculate_future_value_of_expense_with_inflation(current_expense, inflation_rate, years):
    """Calculates the future value of an expense adjusted for inflation."""
    if years < 0:
        return current_expense
    return current_expense * ((1 + inflation_rate) ** years)

def calculate_required_corpus(
    desired_annual_income_today,
    retirement_age,
    current_age,
    life_expectancy,
    inflation_rate,
    post_retirement_return_rate
):
    """
    Calculates the total corpus needed at retirement to generate desired annual income,
    adjusted for inflation and considering post-retirement returns.
    """
    years_to_retirement = retirement_age - current_age
    years_in_retirement = life_expectancy - retirement_age

    if years_to_retirement < 0 or years_in_retirement <= 0:
        return 0.0 # Invalid input, or already retired/past life expectancy

    # Desired annual income at retirement (inflation-adjusted)
    desired_income_at_retirement = desired_annual_income_today * ((1 + inflation_rate) ** years_to_retirement)

    # Annuity formula to calculate corpus
    # Corpus = Annual Income * [ (1 - (1 + r)^-n) / r ]
    # Where r is post_retirement_return_rate and n is years_in_retirement
    if post_retirement_return_rate == 0:
        # If return rate is 0, corpus is simply (income * years_in_retirement)
        required_corpus = desired_income_at_retirement * years_in_retirement
    else:
        # Using present value of an annuity formula for required corpus
        # Note: This assumes income is withdrawn at the END of each year in retirement
        required_corpus = desired_income_at_retirement * ((1 - (1 + post_retirement_return_rate)**(-years_in_retirement)) / post_retirement_return_rate)

    return required_corpus

def project_savings_growth(
    current_savings,
    monthly_contribution,
    annual_return_rate,
    years_to_project
):
    """
    Projects the growth of savings over time, considering monthly contributions and annual returns.
    Returns a list of projected balances for each year.
    """
    projected_balances = []
    balance = float(current_savings)
    monthly_return_rate = annual_return_rate / 12

    for year in range(1, years_to_project + 1):
        for _ in range(12): # Apply monthly contribution and return
            balance = balance * (1 + monthly_return_rate) + monthly_contribution
        projected_balances.append(round(balance, 2))
    return projected_balances

def run_monte_carlo_simulation(
    initial_investment,
    monthly_contribution,
    num_years,
    num_simulations,
    avg_annual_return, # e.g., 0.10 for 10%
    std_dev_annual_return # e.g., 0.15 for 15% volatility
):
    """
    Runs a Monte Carlo simulation for investment growth.
    Returns a list of final portfolio values from all simulations.
    """
    final_portfolio_values = []
    # Convert annual rates to monthly rates for simulation
    monthly_return_avg = avg_annual_return / 12
    monthly_std_dev = std_dev_annual_return / np.sqrt(12) # Standard deviation scales by sqrt(time)

    for _ in range(num_simulations):
        portfolio_value = initial_investment
        for year in range(num_years):
            # Simulate monthly returns using a normal distribution
            # A more advanced model might use log-normal or historical data
            monthly_returns = np.random.normal(monthly_return_avg, monthly_std_dev, 12)
            for r in monthly_returns:
                portfolio_value = portfolio_value * (1 + r) + monthly_contribution
        final_portfolio_values.append(portfolio_value)

    return final_portfolio_values

def recommend_asset_allocation(current_age, retirement_age):
    """
    Provides a simple heuristic for asset allocation based on age and time horizon.
    Returns a dictionary with equity and debt percentages and a note.
    """
    years_to_retirement = retirement_age - current_age
    if years_to_retirement <= 0:
        return {"equity": "20%", "debt": "80%", "note": "Highly conservative, focus on capital preservation during retirement."}
    elif years_to_retirement < 10:
        return {"equity": "40%", "debt": "60%", "note": "Moderately conservative, shifting towards capital preservation as retirement nears."}
    elif years_to_retirement < 20:
        return {"equity": "60%", "debt": "40%", "note": "Balanced approach, aiming for growth with moderate risk."}
    else: # 20 years or more
        return {"equity": "75%", "debt": "25%", "note": "Aggressive, maximizing growth potential for a long investment horizon."}