# app.py

from flask import Flask, render_template, request
import financial_models as fm
import numpy as np

app = Flask(__name__)

# It's good practice to set a secret key for Flask apps
# (even if not using sessions directly in this simple version, future features might)
app.secret_key = 'Dhuqed@312Ghi' # **IMPORTANT: Change this to a strong, random string in production**

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None
    # Initialize form fields with defaults or None for re-population after POST
    form_data = {
        'current_age': None, 'retirement_age': None, 'life_expectancy': None,
        'current_savings': None, 'monthly_contribution': None,
        'desired_annual_income_today': None, 'avg_annual_return': None,
        'std_dev_annual_return': None, 'post_retirement_return_rate': None,
        'inflation_rate': None
    }

    if request.method == 'POST':
        try:
            # Get data from form and convert to appropriate types
            # Using .get() with default None handles missing fields if needed, but 'required' in HTML should prevent
            form_data['current_age'] = int(request.form.get('current_age'))
            form_data['retirement_age'] = int(request.form.get('retirement_age'))
            form_data['life_expectancy'] = int(request.form.get('life_expectancy'))
            form_data['current_savings'] = float(request.form.get('current_savings'))
            form_data['monthly_contribution'] = float(request.form.get('monthly_contribution'))
            form_data['desired_annual_income_today'] = float(request.form.get('desired_annual_income_today'))

            # Convert percentage inputs to decimals for calculations
            form_data['avg_annual_return'] = float(request.form.get('avg_annual_return')) / 100
            form_data['std_dev_annual_return'] = float(request.form.get('std_dev_annual_return')) / 100
            form_data['post_retirement_return_rate'] = float(request.form.get('post_retirement_return_rate')) / 100
            form_data['inflation_rate'] = float(request.form.get('inflation_rate')) / 100

            # --- Basic Input Validations ---
            if not (1 <= form_data['current_age'] <= 99):
                raise ValueError("Current age must be between 1 and 99 years.")
            if not (form_data['current_age'] < form_data['retirement_age'] <= 99):
                raise ValueError("Retirement age must be after current age and less than 100.")
            if not (form_data['retirement_age'] < form_data['life_expectancy'] <= 120):
                raise ValueError("Life expectancy must be after retirement age and less than 120.")
            if form_data['current_savings'] < 0 or form_data['monthly_contribution'] < 0 or form_data['desired_annual_income_today'] < 0:
                raise ValueError("Savings, contributions, and desired income cannot be negative.")
            if not (0 <= form_data['avg_annual_return'] <= 1): # Between 0 and 100%
                raise ValueError("Pre-retirement return rate should be between 0 and 100%.")
            if not (0 <= form_data['post_retirement_return_rate'] <= 1): # Between 0 and 100%
                raise ValueError("Post-retirement return rate should be between 0 and 100%.")
            if not (0 <= form_data['inflation_rate'] <= 1): # Between 0 and 100%
                raise ValueError("Inflation rate should be between 0 and 100%.")
            if not (0 <= form_data['std_dev_annual_return'] <= 1): # Between 0 and 100%
                raise ValueError("Annual return standard deviation should be between 0 and 100%.")


            years_to_retirement = form_data['retirement_age'] - form_data['current_age']
            years_in_retirement = form_data['life_expectancy'] - form_data['retirement_age']

            # 1. Calculate Required Corpus
            required_corpus = fm.calculate_required_corpus(
                form_data['desired_annual_income_today'],
                form_data['retirement_age'],
                form_data['current_age'],
                form_data['life_expectancy'],
                form_data['inflation_rate'],
                form_data['post_retirement_return_rate']
            )

            # 2. Project Savings Growth (Deterministic)
            projected_savings_by_year_list = fm.project_savings_growth(
                form_data['current_savings'],
                form_data['monthly_contribution'],
                form_data['avg_annual_return'],
                years_to_retirement
            )
            # Get the final projected savings at retirement from the list
            projected_savings_at_retirement = projected_savings_by_year_list[-1] if projected_savings_by_year_list else form_data['current_savings']


            # 3. Monte Carlo Simulation (for projected savings at retirement)
            num_simulations = 1000 # Number of simulations for robustness
            monte_carlo_results = fm.run_monte_carlo_simulation(
                form_data['current_savings'],
                form_data['monthly_contribution'],
                years_to_retirement,
                num_simulations,
                form_data['avg_annual_return'],
                form_data['std_dev_annual_return']
            )
            # Analyze Monte Carlo results to get key percentiles
            monte_carlo_min = np.percentile(monte_carlo_results, 0.5) # A very low percentile for a 'worst case' scenario
            monte_carlo_avg = np.mean(monte_carlo_results)
            monte_carlo_median = np.median(monte_carlo_results)
            monte_carlo_10th_percentile = np.percentile(monte_carlo_results, 10) # 10% chance it's worse than this value
            monte_carlo_90th_percentile = np.percentile(monte_carlo_results, 90) # 10% chance it's better than this value


            # 4. Asset Allocation Recommendation (Heuristic)
            asset_allocation = fm.recommend_asset_allocation(
                form_data['current_age'], form_data['retirement_age']
            )

            # 5. Gap Analysis (comparing deterministic projection to required corpus)
            net_corpus_difference = projected_savings_at_retirement - required_corpus
            savings_vs_corpus = 'neutral' # Default
            if net_corpus_difference > 0:
                savings_vs_corpus = 'surplus'
            elif net_corpus_difference < 0:
                savings_vs_corpus = 'shortfall'


            results = {
                'years_to_retirement': years_to_retirement,
                'years_in_retirement': years_in_retirement,
                'desired_income_at_retirement': required_corpus * form_data['post_retirement_return_rate'], # Approximate annual income from required corpus
                'required_corpus': required_corpus,
                'projected_savings_by_year': list(enumerate(projected_savings_by_year_list, start=1)), # For display in HTML
                'projected_savings_at_retirement': projected_savings_at_retirement,
                'monte_carlo_min': monte_carlo_min,
                'monte_carlo_avg': monte_carlo_avg,
                'monte_carlo_median': monte_carlo_median,
                'monte_carlo_10th_percentile': monte_carlo_10th_percentile,
                'monte_carlo_90th_percentile': monte_carlo_90th_percentile,
                'asset_allocation': asset_allocation,
                'net_corpus_difference': abs(net_corpus_difference), # Display absolute difference for shortfall/surplus
                'savings_vs_corpus': savings_vs_corpus
            }

        except ValueError as e:
            error = str(e) # Catch validation errors
        except Exception as e:
            error = f"An unexpected error occurred: {e}. Please ensure all inputs are valid numbers."

    # Render the template, passing results, error, and form_data to re-populate fields
    return render_template('index.html', results=results, error=error, **form_data)

if __name__ == '__main__':
    # Running on port 5000, debug=True for development
    app.run(debug=True, port=5000)