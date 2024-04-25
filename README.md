

## Network Simulator

This Python script simulates a simple network environment with packet switching. It utilizes the `simpy` library for process-based simulation.

Features:

Models network elements like hosts, switches, and links.
Simulates packet transmission with delays based on link speeds.
Tracks and logs packet activity, including ID, source, destination, delay, and switch queue lengths.
Displays simulation logs in a clear table format.

**Requirements:**

 - Python 3.x
 - simpy library (pip install simpy)
 - tabulate library (optional, for formatted table output: pip install
   `tabulate`)

Usage:

Clone or download the repository containing the script (`nw_even.py`).
Install required libraries (pip install simpy and optionally `pip install tabulate`).
Run the script from the command line: `python nw_even.py`
