# ParaRefine-GUI

ParaRefine-GUI is a PyQt5-based graphical user interface for automated computational chemistry workflows, including force field parameterization, dihedral scanning, and liquid property (Lennard-Jones) optimization. 

**Note:** This project includes a **modified version of ForceBalance** (`forcebalance-modify`) to support custom parameterization features required by this GUI.

## 📁 Project Structure
- `src/`: Contains the main GUI code and templates.
- `forcebalance-modify/`: The customized ForceBalance source code (with C-extensions).

## ⚠️ Prerequisites

Before running the GUI, you must have the following external computational tools installed:
- [Psi4](https://psicode.org/)
- [GROMACS](https://www.gromacs.org/)
- [OpenBabel](https://openbabel.org/)
- [Packmol](https://m3g.github.io/packmol/)
- [TorsionDrive](https://github.com/lpwgroup/torsiondrive)

## 🛠️ Installation Guide

We strongly recommend using `conda` to set up the environment, as the modified ForceBalance requires C/C++ compilers to build its extensions.

### Step 1: Clone the repository
```bash
git clone https://github.com/math-diff/ParaRefine-GUI.git
cd ParaRefine-GUI
```

### Step 2: Create Conda Environment & Install Dependencies
Create an environment and install the required external tools **and compilers**:

```bash
conda create -n pararefine python=3.10
conda activate pararefine

# Install compilers and external tools
conda install -c conda-forge compilers
conda install -c conda-forge psi4 gromacs=2019.5 openbabel packmol torsiondrive simple-dftd3 dftd3-python
```

### Step 3: Compile and Install the Modified ForceBalance
Because this repository contains a custom version of ForceBalance, you must build and install it locally:

```bash
cd forcebalance-modify
pip install .
cd ..
```

### Step 4: Install GUI Python Libraries
Install the required Python packages for the interface:

```bash
pip install -r requirements.txt
```

## 🚀 How to Run

Navigate to the `src` directory and run the main script:

```bash
conda activate pararefine
cd src
python main.py
```