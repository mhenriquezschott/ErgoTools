# ErgoTools -  Plant-Layout Organizational Tool (PLOT)
Plant-Layout Organizational Tool
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


### 2. Download ErgoTools-PLOT

Option A: Download ZIP

1. Visit https://github.com/mhenriquezschott/plot
3. Click the green "Code" button and select "Download ZIP".
4. Extract the ZIP file to a known folder, for example:
   C:\Users\YourName\Documents\ErgoTools
5. Or download:
   https://github.com/mhenriquezschott/plot/archive/refs/heads/main.zip
   
Option B: Clone using Git

If you have Git installed, you can run:
git clone https://github.com/mhenriquezschott/plot.git

### 3. Install Python dependencies
Open a terminal (Linux/macOS) or Command Prompt / PowerShell (Windows), navigate to the ErgoTools directory (cd path/to/ErgoTools), and run:

pip3 install -r requirements.txt

This installs packages like PyQt5, VTK and others.

## Running ErgoTools-PLOT
- Inside the src folder, open a terminal and run:
python main.py

