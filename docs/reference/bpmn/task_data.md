# Task Data

Task data is copied from task to task.

For example, consider the following sequence of tasks:

1. Start Event
2. Set Variable (sets variable a)
3. Read Variable (reads variable a)

In this scenario, if the "Set Variable" task sets the value of variable a to the number 1, the "Read Variable" task that follows can access that value (oh, cool, 1).

When the flow splits, as in a set of parallel branches, each branch gets a copy of the same data.
Then, when the data is merged back together at a merging gateway, if multiple branches write to the same variable, the last branch to complete will be the data that is propagated to tasks after the merging gateway.
Therefore, if you have tasks a, b, and c that run in parallel, it might not be a good idea for both a and b to set the "desired_withdrawal_amount" variable since, depending on how fast a and b run (and other implementation details around the parallel processing), the expected "winner" would not be knowable in advance.

This general branching and merging strategy is applied to all parallel constructs, including inclusive gateways.
