# show-run-status command

Use this command to summarize one Agent Pipeline run without resuming it.

## Required input

- A run id under `.agent-runs/`.

## Procedure

1. Run:

   ```bash
   python scripts/show_run_status.py --run <run-id>
   ```

2. Report the status block exactly enough for the operator to see:

   - last run-log event;
   - current stage;
   - whether a final response is allowed;
   - stop condition;
   - next required action;
   - artifact count.

3. Do not mutate project files. This is a read-only status command.
