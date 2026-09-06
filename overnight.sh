#!/bin/bash
# Overnight chain. Runs unattended; each stage is resumable and ceiling-guarded.
cd "/Users/hsuanlo/Desktop/Papers/AI fairness in real estate"
echo "=== overnight start $(date) ==="

# 1) wait for the luna full grid already in flight
while pgrep -f "08_run_grid.py.*luna" > /dev/null; do sleep 60; done
echo "=== luna grid finished $(date) ==="
python3 -c "import sys;sys.path.insert(0,'code');import providers;providers.status()"

# 2) capability-tier comparison: gpt-5.6-sol, S1 only, 75 scenarios
#    Sized to the remaining prepaid balance. The ceiling is absolute: the run
#    aborts itself rather than exceed it, independent of my cost estimate.
python3 -u code/08_run_grid.py --scenarios 60 --arch S1 --reps 3 \
        --model gpt-5.6-sol --workers 6 --ceiling 18 >> out/grid_sol.log 2>&1
echo "=== sol subsample finished $(date) ==="
python3 -c "import sys;sys.path.insert(0,'code');import providers;providers.status()"
echo "=== overnight done $(date) ==="
