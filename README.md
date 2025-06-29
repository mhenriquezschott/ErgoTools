# JROT

The Job Rotation Optimization Tool (JROT) helps design and analyze job rotation schedules by estimating ergonomic risks for each worker across different jobs and time blocks. 
It leverages established fatigue failure tools (LiFFT, DUET, and ST) to quantify exposure and includes optimization features to minimize average and peak risks across rotations. 
JROT provides detailed visual tables with risk color coding, average calculations, and tailored suggestions to support the creation of more balanced, lower-risk job rotation schemes.


# ErgoTools

ErgoTools is a Python-based software suite that includes ergonomic analysis modules:

- PLOT (Plant-Layout Organizational Tool): visualizes ergonomic risk distributions across a plant layout, with filters by gender, area, line, age, and summary statistics.
- JROT (Job Rotation Optimization Tool): designs and optimizes job rotation schemes to help reduce ergonomic risk by balancing work assignments.

ErgoTools is under active development and aims to support ergonomists and engineers in making data-driven decisions.

## Installation Guide

### 1. Install Python 3.10

Download and install Python 3.10.x from:

https://www.python.org/downloads/

Alternatively, on Windows, Python 3.10 is also available in the Microsoft Store.

During installation on Windows, make sure to check the box:

[ ] Add Python 3.10 to PATH

If you forget, you will need to add Python to your system environment variables manually so `python` and `pip` can be found.

### 2. Download ErgoTools

Option A: Download ZIP

1. Visit https://github.com/mhenriquezschott/ErgoTools
2. Click the green "Code" button and select "Download ZIP".
3. Extract the ZIP file to a known folder, for example:
   C:\Users\YourName\Documents\ErgoTools

Option B: Clone using Git

If you have Git installed, you can run:
git clone https://github.com/mhenriquezschott/ErgoTools.git

### 3. Install Python dependencies
Open a terminal (Linux/macOS) or Command Prompt / PowerShell (Windows), navigate to the ErgoTools directory (cd path/to/ErgoTools), and run:

pip3 install -r requirements.txt

This installs packages like PyQt5, Pyomo, pulp, matplotlib, and others.

## Running ErgoTools

### Option 1 – Run from the terminal

Inside the ErgoTools folder, execute:
python3 main.py

or on Windows:
python main.py

### Option 2 – Create a Windows desktop shortcut

1. Inside the `src` folder, there is a batch file named: run_ergotools.batz
2. Rename it to: run_ergotools.bat
3. Right-click `run_ergotools.bat` and select "Create shortcut".
4. Move the shortcut to your Desktop. Now you can double-click it to launch ErgoTools without opening a terminal.

## Notes on optimizers

JROT includes two types of optimizers:

- A single-tool optimizer that minimizes the average ergonomic risk for workers based on a selected tool (LiFFT, DUET, or Shoulder Tool). It is implemented with Python’s PuLP library and solved using CBC (Coin-or Branch and Cut).

- A multi-tool optimizer that simultaneously considers all three ergonomic tools to minimize the highest average exposure (per tool) and reduce the spread of risk between workers. It uses Pyomo and is solved by GLPK (GNU Linear Programming Kit).

The multi-tool optimization is more computationally intensive and may take longer, especially for larger problems. Having both optimizers provides flexibility: quicker runs with the single-tool optimizer and more comprehensive balancing with the multi-tool model.

Disclaimer: The Job Rotation Optimization Tool is based on a statistical model using LIFFT, DUET, and The Shoulder Tool. Estimates depend on input data; rotating high-risk jobs may elevate risk for workers in lower-risk jobs.


