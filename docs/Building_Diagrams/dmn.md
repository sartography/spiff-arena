# Decision Tables

DMN tables are powerful tools for modeling and implementing business rules and decision logic.
They allow you to define rules and their associated conditions and actions in a structured manner.
By evaluating the conditions in each rule, the DMN engine can determine which rules are triggered based on the provided inputs and execute the corresponding actions.
This provides a flexible and configurable approach to decision-making in various scenarios.

A DMN (Decision Model and Notation) table consists of several components that help define the decision logic and structure the decision-making process.
The main components of a DMN table are:

## DMN Components

- ***Input Variables:*** These are the variables that represent the information or data used as input for the decision.
Each input variable is typically represented as a column in the table.
Multiple columns represent multiple input variables.
- ***Conditions:*** Conditions specify the criteria or constraints that need to be evaluated for each input variable.
They define the rules or expressions that determine when a particular decision rule should be triggered.
Conditions are usually represented in the "When" column of the table.
- ***Actions or Expressions:*** Actions or expressions define the operations or calculations that are executed when a specific rule is triggered.
They represent the logic associated with the decision outcome and are represented in the same row as the conditions in the table.
- ***Decision Rules:*** Decision rules are the individual rows in the DMN table.
Each rule represents a specific combination of conditions and actions that define the behavior or logic for a particular scenario.
Decision rules combine the input conditions and output actions in a structured manner.
- ***Hit Policy:*** The hit policy determines how the decision engine selects or combines the applicable decision rules when multiple rules are triggered.
It defines the behavior for resolving conflicts or overlaps between rules.
Common hit policies include "First," "Unique," "Priority," "Any," and "Collect."

## Hit Policy

**Unique:** Only one rule can match the given inputs.
If multiple rules match, it results in an error or an undefined outcome.
This policy ensures that only one result is produced.

**First:** The first rule that matches the inputs is selected, and its corresponding output is returned.
Other matching rules are ignored.
This policy is useful when you want to prioritize the order of rules.

**Collect:** All rules that match the inputs are selected, and the outputs from those rules are collected and returned as a list or a collection.
This policy allows for gathering multiple results.
