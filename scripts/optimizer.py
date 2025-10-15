import pandas as pd
from pulp import LpProblem, LpMaximize, lpSum, LpVariable, LpStatus, PULP_CBC_CMD

def winsorized_min_max(series, lower_percentile=0.05, upper_percentile=0.95):
    """
    Applies Winsorization and Min-Max scaling to a pandas Series.
    
    Args:
        series (pd.Series): The data column to normalize.
        lower_percentile (float): The lower percentile to clip at.
        upper_percentile (float): The upper percentile to clip at.

    Returns:
        pd.Series: The normalized data (scaled 0 to 1).
    """
    # Determine the clipping boundaries from the data's distribution
    lower_bound = series.quantile(lower_percentile)
    upper_bound = series.quantile(upper_percentile)
    
    # Clip the data to handle extreme outliers
    winsorized_series = series.clip(lower=lower_bound, upper=upper_bound)
    
    # Handle the edge case where all values are the same
    if upper_bound == lower_bound:
        return pd.Series([0.0] * len(series), index=series.index)
        
    # Apply Min-Max normalization to the "tamed" data
    normalized_series = (winsorized_series - lower_bound) / (upper_bound - lower_bound)
    
    return normalized_series

def run_optimization():
    """
    Reads the problem backlog, calculates a normalized impact score, and runs a 
    linear programming model to find the optimal set of problems to fix within 
    resource constraints.
    """
    try:
        # Load the problem data from the CSV file
        problem_df = pd.read_csv('../data/problem_records.csv')
    except FileNotFoundError:
        print("Error: 'problem_records.csv' not found. Make sure it is in the 'data' directory.")
        return

    # --- NEW: Calculate Impact using Winsorized Min-Max Normalization ---
    # This section replaces the old manual formula.
    
    # 1. Normalize each impact dimension onto a fair 0-to-1 scale
    problem_df['BH_norm'] = winsorized_min_max(problem_df['BusinessHoursLost'])
    problem_df['FI_norm'] = winsorized_min_max(problem_df['FinancialImpactUSD'])
    problem_df['XLA_norm'] = winsorized_min_max(problem_df['UserFrustrationScore'])
    
    # 2. Calculate the final ImpactScore by summing the normalized values (equal weighting)
    problem_df['ImpactScore'] = problem_df['BH_norm'] + problem_df['FI_norm'] + problem_df['XLA_norm']

    # --- Define Resource Constraints ---
    MAX_EFFORT_HOURS = 200

    # --- Set up the Optimization Model (this part remains the same) ---
    model = LpProblem(name="problem-prioritization-optimizer", sense=LpMaximize)

    problem_vars = {
        row.ProblemID: LpVariable(name=row.ProblemID, cat='Binary')
        for _, row in problem_df.iterrows()
    }

    model += lpSum(
        problem_df.loc[problem_df.ProblemID == pid, 'ImpactScore'].values[0] * var
        for pid, var in problem_vars.items()
    ), "Total_Impact_Score"

    model += lpSum(
        problem_df.loc[problem_df.ProblemID == pid, 'EstimatedFixEffortHours'].values[0] * var
        for pid, var in problem_vars.items()
    ) <= MAX_EFFORT_HOURS, "Total_Effort_Constraint"

    # --- Solve the Model and Print the Results ---
    # Suppress solver messages for cleaner output
    # --- FIX #2: Call PULP_CBC_CMD directly ---
    status = model.solve(PULP_CBC_CMD(msg=0))
    ##status = model.solve(LpProblem.PULP_CBC_CMD(msg=0))

    print("--- Value-Driven Prioritization Results (using Winsorized Min-Max) ---")
    print(f"Optimization Status: {LpStatus[status]}\n")

    if status == 1: # 'Optimal' status
        total_impact = model.objective.value()
        total_hours = sum(problem_df.loc[problem_df.ProblemID == pid, 'EstimatedFixEffortHours'].values[0] for pid, var in problem_vars.items() if var.value() == 1.0)

        print(f"Optimal problems to fix within the {MAX_EFFORT_HOURS}-hour budget:\n")
        for pid, var in problem_vars.items():
            if var.value() == 1.0:
                desc = problem_df.loc[problem_df.ProblemID == pid, 'Description'].values[0]
                print(f"  - {pid}: {desc}")

        print(f"\nTotal Impact Score Achieved: {total_impact:.2f}")
        print(f"Total Hours Required: {int(total_hours)}/{MAX_EFFORT_HOURS}")
    else:
        print("Could not find an optimal solution.")

if __name__ == "__main__":
    run_optimization()

