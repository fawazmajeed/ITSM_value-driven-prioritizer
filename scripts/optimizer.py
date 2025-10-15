import pandas as pd
from pulp import LpProblem, LpMaximize, lpSum, LpVariable, LpStatus

def run_optimization():
    """
    Reads the problem backlog, calculates impact, and runs a linear programming
    model to find the optimal set of problems to fix within resource constraints.
    """
    try:
        # Load the problem data from the CSV file in the parent 'data' directory
        problem_df = pd.read_csv('../data/problem_records.csv')
    except FileNotFoundError:
        print("Error: 'problem_records.csv' not found. Make sure it is in the 'data' directory.")
        return

    # --- This is where the logic from Chapter 2 (Quantify Impact) would go ---
    # For now, we use a simplified placeholder for the 'ImpactScore'
    # A more advanced model would combine financial, operational, and user frustration scores.
    problem_df['ImpactScore'] = (problem_df['FinancialImpactUSD'] / 1000) + \
                                (problem_df['BusinessHoursLost'] * 0.1) + \
                                (problem_df['UserFrustrationScore'] * 10)

    # --- Define Resource Constraints ---
    # This is the total number of engineering hours available for the quarter.
    MAX_EFFORT_HOURS = 200

    # --- Set up the Optimization Model ---
    model = LpProblem(name="problem-prioritization-optimizer", sense=LpMaximize)

    # Define decision variables: a binary variable for each problem
    # The variable will be 1 if the problem is selected, and 0 otherwise.
    problem_vars = {
        row.ProblemID: LpVariable(name=row.ProblemID, cat='Binary')
        for _, row in problem_df.iterrows()
    }

    # Define the Objective Function:
    # We want to maximize the sum of 'ImpactScore' for the selected problems.
    model += lpSum(
        problem_df.loc[problem_df.ProblemID == pid, 'ImpactScore'].values[0] * var
        for pid, var in problem_vars.items()
    ), "Total_Impact_Score"

    # Define the Constraint:
    # The sum of 'EstimatedFixEffortHours' for the selected problems must not exceed our available hours.
    model += lpSum(
        problem_df.loc[problem_df.ProblemID == pid, 'EstimatedFixEffortHours'].values[0] * var
        for pid, var in problem_vars.items()
    ) <= MAX_EFFORT_HOURS, "Total_Effort_Constraint"

    # --- Solve the Model and Print the Results ---
    status = model.solve()

    print("--- Value-Driven Prioritization Results ---")
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
        print(f"Total Hours Required: {total_hours}/{MAX_EFFORT_HOURS}")
    else:
        print("Could not find an optimal solution.")

if __name__ == "__main__":
    run_optimization()
