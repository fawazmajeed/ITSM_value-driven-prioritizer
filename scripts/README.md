# ITSM Value-Driven Prioritizer Playbook
### Pre requisits
*   **/data**: Contains sample datasets, including `problem_records.csv`, to use with the models.
*   **/scripts**: Contains the Python script (`optimizer.py`) for the prescriptive analytics model.
*   **/budget parameter**: Currently the budget constraint of 200 Hrs is hardcode in python to local variable
*   --- Define Resource Constraints ---
    **/MAX_EFFORT_HOURS = 200** [Change or automize it using excel column or variable based on your need]

### How to test for results
1.  **data csv file:** Ensure you have your csv file for problem records in the data folder or read it manually using python.
2.  **python code:** Get your code script as optimizer.py 
3.  **cmd line:** run cmd line and navigate to your `/scripts` directory.
4.  **Run code:** python optimizer.py => wait and let the code do the magic and give you the desired result.
