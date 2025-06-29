# JROT

The Job Rotation Optimization Tool (JROT) helps design and analyze job rotation schedules by estimating ergonomic risks for each worker across different jobs and time blocks. 
It leverages established fatigue failure tools (LiFFT, DUET, and ST) to quantify exposure and includes optimization features to minimize average and peak risks across rotations. 
JROT provides detailed visual tables with risk color coding, average calculations, and tailored suggestions to support the creation of more balanced, lower-risk job rotation schemes.

## Installation Guide

### 1. Install Python 3.10

Download and install Python 3.10.x from:

https://www.python.org/downloads/

Alternatively, on Windows, Python 3.10 is also available in the Microsoft Store.

During installation on Windows, make sure to check the box:

[X] Add Python 3.10 to PATH

If you forget, you will need to add Python to your system environment variables manually so `python` and `pip` can be found.

## Check if Python is added to your PATH (Windows)

- Open a **Command Prompt** (press **Win + R**, type `cmd`, and press **Enter**).

- Type the following command and press **Enter**:
  python --version
- You should see output like:
  Python 3.10.9

- You can also test if `pip` is available by typing:
  pip --version

- If you see an error such as `'python' is not recognized as an internal or external command`, it means Python is **not in your system PATH**.

### What to do if Python is not found
- During installation, make sure you check the option:
[x] Add Python 3.10 to PATH

- If you forgot, you can re-run the Python installer and choose **Modify**, then select **Add Python to environment variables**, and finish the setup.

- Alternatively, you can add Python manually:
- Find where Python was installed (often `C:\Users\<YourName>\AppData\Local\Programs\Python\Python310`).
- Follow the next steps:
   - Click **Start** → type **"environment variables"** → select **Edit the system environment variables** →
     in the **System Properties** window go to the **Advanced** tab → click **Environment Variables…**
   - In **System variables**, select **Path** → **Edit** → **New** → paste the Python folder path.
   - Also add the `Scripts` subfolder (for example: `C:\Users\<YourName>\AppData\Local\Programs\Python\Python310\Scripts`).
- After adding to PATH, open a **new** Command Prompt and try `python --version` again.


### 2. Download ErgoTools

Option A: Download ZIP

1. Visit https://github.com/mhenriquezschott/ErgoTools
2. Click the green "Code" button and select "Download ZIP".
3. Extract the ZIP file to a known folder, for example:
   C:\Users\YourName\Documents\ErgoTools
4. Or download:
   https://github.com/mhenriquezschott/ErgoTools/archive/refs/heads/jrot.zip  

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


# Installing GLPK on Windows


## 1. Check your Windows type (32-bit or 64-bit)
- Go to **Control Panel → System → About**
- Note if your system is **32-bit** or **64-bit**.

---

## 2. Download GLPK
- Download the latest Windows version of GLPK from SourceForge:
  - https://sourceforge.net/projects/winglpk/
- This will download a zip file (e.g., `glpk-4.65.zip`) to your **Downloads** folder.

---

## 3. Extract the ZIP file
- Right click on the downloaded zip file and select **Extract Here** (you can use 7-Zip or Windows built-in extractor).
- You should now have a folder named something like `glpk-4.65`.

---

## 4. Move the GLPK folder
- Move the extracted folder (e.g., `glpk-4.65`) to your **C:\ drive**. 
- You might need admin rights to do this.

---

## 5. Select the correct binary folder
- Open the `glpk-4.65` folder.
- If your system is **32-bit**, open the `w32` folder.
- If your system is **64-bit**, open the `w64` folder.

---

## 6. Copy the folder path
- Once inside `w32` or `w64`, **copy the full path** from the address bar.
  - Example: `C:\glpk-4.65\w64`

---

## 7. Set up the Environment Variable
- Click the Start (Windows) button and type "environment variables".
- Click on "Edit the system environment variables" from the search results.
- In the System Properties window that opens, go to the Advanced tab.
- Click the Environment Variables... button at the bottom.

## 8. Add GLPK to your PATH
- In the **System variables** section, scroll down and select **Path**, then click **Edit**.
- In the new window, click **New** and **paste the path** to your 32-bit or 64-bit GLPK directory (for example: `C:\glpk-4.65\w64`).
- Click **OK** on all windows to save and apply the changes.
- Close any open Command Prompts and open a **new** one so the updated PATH is recognized.
 

---

## 9. Verify the installation
- Open a **Command Prompt** window.
- Type:
  glpsol --help
     ```  
   - You should see usage info for the GLPK solver  

6. **Use with Python / Pyomo**  
   - Once `glpsol.exe` is in your PATH, Pyomo will be able to locate and use it reliably.
