## 1 - Plan Mode value
-Where did amending a plan prevent a problem that would have required a revert? Cite the session number from PLAN_LOG.md.
     - In Session 1, Claude pointed out that I had function signatures under DO NOT TOUCH, which would have affected the agent's implementation by creating identical functions of create_task and list_task with the new priority field parameter. Plan mode caught this, and asked if I wanted to change anything before it continued. I omitted these functions from DO NOT TOUCH as they needed to be changed.
## 2 - Plan Mode Limits
- Describe the one case where the output did not match the amended plan. What does that tell you about the reliability boundary of Plan Mode?
    - In Session 2, Claude went against the amended plan and implemented a faulty version of it. However, the agent summarized its actions and pointed out the ambiguity in my plan that caused the error. Claude's output in Plan mode is only as reliable as the plan you and the agent create and modify.
## 3 - Subagent value
- Which subagent boundary was the most important to enforce? Why? What would have happened if you had let Claude implement the feature in a single session?
    - I think that the input and handoff boundaries are the most important to enforce in subagents, as these enforce the proper pipeline of input and output from one agent to another, specifying the scope that each subagent plays. If Claude were to implement this feature in one single session, I fear that maybe the context window of each layer (data, service, API, tests) would become too large to comprehend all at one time, so breaking these up into subproblems for multiple agents to handle is more wise.
## 4 - Gap analysis
- Both techniques are advisory (~80% reliable). Name the specific rule or constraint from Task
2 that you would most want to enforce mechanically. Describe in one sentence what a hook
that enforces it would do.
    - A constraint I would mechanically enforce would be "Don't alter or delete tests to weaken them." A hook would be implemented to run before and after an agent editing test files, and compares the pre and post edit to see if the agent rewrote or deleted an assertion. If so, the agent returns with a message like "Altered tests. Fix the code, don't weaken the test cases." 