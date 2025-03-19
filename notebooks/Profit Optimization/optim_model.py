import mlflow
import pandas as pd
from ortools.linear_solver import pywraplp


class OptimModel(mlflow.pyfunc.PythonModel):

    def load_context(self, context):
        pass

    def predict(self, model_input):
        if isinstance(model_input, pd.DataFrame):
            model_input = model_input.iloc[0].to_dict()

        # Create the solver with GLPK
        solver = pywraplp.Solver.CreateSolver("CBC")
        if not solver:
            solver = pywraplp.Solver.CreateSolver("SCIP")

        # Define variables (non-negative integers)
        x1 = solver.IntVar(0, solver.infinity(), "x1")
        x2 = solver.IntVar(0, solver.infinity(), "x2")

        # Get input parameters
        profit_P1 = model_input["profit_P1"]
        profit_P2 = model_input["profit_P2"]
        work_limit = model_input["work_limit"]
        material_limit = model_input["material_limit"]

        # Add constraints
        # Work constraint: 2*x1 + 4*x2 <= work_limit
        solver.Add(2 * x1 + 4 * x2 <= work_limit)

        # Material constraint: 3*x1 + 2*x2 <= material_limit
        solver.Add(3 * x1 + 2 * x2 <= material_limit)

        # Set objective function to maximize profit
        solver.Maximize(profit_P1 * x1 + profit_P2 * x2)

        # Solve the problem
        status = solver.Solve()

        # Prepare the return dictionary
        return_dict = {}

        if status == pywraplp.Solver.OPTIMAL:
            return_dict = {
                "status": "optimal",
                "x1": x1.solution_value(),
                "x2": x2.solution_value(),
                "profit": solver.Objective().Value(),
            }
        else:
            # Handle other statuses
            status_map = {
                pywraplp.Solver.INFEASIBLE: "infeasible",
                pywraplp.Solver.UNBOUNDED: "unbounded",
                pywraplp.Solver.ABNORMAL: "abnormal",
                pywraplp.Solver.NOT_SOLVED: "not_solved",
            }
            return_dict = {"status": status_map.get(status, f"unknown_status_{status}"), "x1": 0, "x2": 0, "profit": 0}

        return return_dict
