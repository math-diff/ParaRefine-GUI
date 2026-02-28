import sys
import os
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QProgressDialog
from gui import MyMainWindow, Psi4SettingDialog, FbSettingDialog, VibAnimateDialog, PackmolViewDialog
from PyQt5.QtCore import QProcess, Qt, QUrl
import expand_gromacs_includes
import split_topol, process_fb_itp, process_user_params
import shutil, update_coord
import generate_psi4_dat, psi4out_convert_vdata
from generate_fb_vib_in import generate_fb_vib
import anifrq_all, generate_vib_html
import glob
import remove_vib_modes
import json
from select_dih import generate_dihedral_html
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QMessageBox, QMainWindow
import process_lj_itp
import generate_packmolinp, generate_data_csv
from PyQt5 import QtCore
from generate_fb_lj_in import save_fb_lj_in
class lj_logic:
    def select_coordinate_file_3(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Coordinate File",
            "./",
            "Coordinate File (*.pdb)"
        )
        if file_path:
            self.coordinate_file_Edit_3.setText(file_path)
    def select_topology_file_3(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Topology File",
            "./",
            "Topology File (*.top);;All Files (*)"
        )
        if file_path:
            self.lineEdit_topology_file_3.setText(file_path)
    def select_project_folder_3(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Working Directory", "./")
        if folder_path:
            self.lineEdit_project_folder_3.setText(folder_path)
    def create_new_directory_3(self):
        base_path = self.lineEdit_project_folder_3.text().strip()
        folder_name = self.lineEdit_project_name_3.text().strip()
        if not base_path or not folder_name:
            QMessageBox.warning(self, "Warning", "Please ensure 'Project Name' and 'Project Folder' are filled in.")
            return
        project_full_path = os.path.join(base_path, folder_name)
        forcefield_path = os.path.join(project_full_path, "forcefield")
        targets_path = os.path.join(project_full_path, "targets")
        ligand_liquid_path = os.path.join(targets_path, "ligand_liquid")
        try:
            os.makedirs(forcefield_path, exist_ok=True)
            os.makedirs(targets_path, exist_ok=True)
            os.makedirs(ligand_liquid_path, exist_ok=True)
            msg = (f"Created successfully\n\n"
                   f"Directory: {project_full_path}\n"
                   f"Subfolders: forcefield/, targets/, ligand_liquid/")
            QMessageBox.information(self, "Success", msg)
            print(f"Created: {forcefield_path}")
            print(f"Created: {targets_path}")
            print(f"Created: {ligand_liquid_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fail", f"Failed to create directory：\n{str(e)}")
    def execute_expansion_3(self):
        input_path = self.lineEdit_topology_file_3.text().strip()
        if not input_path:
            QMessageBox.warning(self, "Warning", "Please select a Topology file first.")
            return
        project_base = self.lineEdit_project_folder_3.text().strip()
        project_name = self.lineEdit_project_name_3.text().strip()
        target_dir = os.path.join(project_base, project_name, "forcefield")
        output_path = os.path.join(target_dir, "ligand.itp")
        success, message = expand_gromacs_includes.run_expansion(input_path, output_path)
        if success:
            print(f"Log: {message}")
        else:
            QMessageBox.critical(self, "Error", message)
        return success
    def run_extract_system_section_3(self):
        project_base = self.lineEdit_project_folder_3.text().strip()
        project_name = self.lineEdit_project_name_3.text().strip()
        source_dir = os.path.join(project_base, project_name, "forcefield")
        input_file = os.path.join(source_dir, "ligand.itp")
        target_dir = os.path.join(project_base, project_name, "targets", "ligand_liquid")
        output_file = os.path.join(target_dir, "gas.top")
        split_topol.extract_system_section(input_file, output_file)
    def run_process_input_topol_3(self):
        step1_success = self.execute_expansion_3()
        if not step1_success:
            return
        self.run_extract_system_section_3()
    def pdb_convert_gas_gro(self):
        import subprocess
        input_pdb_file = self.coordinate_file_Edit_3.text().strip()
        project_base = self.lineEdit_project_folder_3.text().strip()
        project_name = self.lineEdit_project_name_3.text().strip()
        target_dir = os.path.join(project_base, project_name, "targets", "ligand_liquid")
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create directory:\n{str(e)}")
                return
        target_path = os.path.join(target_dir, "gas.gro")
        target_copy_name = "gas.pdb"
        target_copy_path = os.path.join(target_dir, target_copy_name)
        if not input_pdb_file or not os.path.exists(input_pdb_file):
            QMessageBox.warning(self, "Error", f"Source file does not exist or is not selected:\n{input_pdb_file}")
            return
        cmd = ["obabel", input_pdb_file, "-O", target_path]
        try:
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0:
                try:
                    shutil.copy(input_pdb_file, target_copy_path)
                except Exception as copy_error:
                    QMessageBox.warning(self, "Warning", f"Gro conversion successful, but failed to copy PDB file:\n{str(copy_error)}")
                    return
                print(f"Successfully converted {input_pdb_file} to {target_path}")
                QMessageBox.information(self, "message", f"Success")
            else:
                error_msg = process.stderr
                print(f"Obabel Error: {error_msg}")
                QMessageBox.critical(self, "Conversion Failed", f"Obabel command failed:\n{error_msg}")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not find 'obabel' command.\nPlease ensure OpenBabel is installed and added to system PATH.")
        except Exception as e:
            QMessageBox.critical(self, "Execution Error", f"Failed to run conversion:\n{str(e)}")
    def run_process_lj_itp(self):
        project_base = self.lineEdit_project_folder_3.text().strip()
        project_name = self.lineEdit_project_name_3.text().strip()
        input_itp = os.path.join(project_base, project_name, "forcefield", "ligand.itp")
        output_itp = os.path.join(project_base, project_name, "forcefield", "ligand_lj.itp")
        sigma_input = self.lineEdit_sigma.text().strip()
        epsilon_input = self.lineEdit_epsilon.text().strip()
        if not os.path.exists(input_itp):
            QMessageBox.warning(self, "Error", f"Input file not found:\n{input_itp}\nPlease run expansion first.")
            return
        if not sigma_input and not epsilon_input:
            QMessageBox.information(self, "Info", "No atom IDs provided in Sigma or Epsilon fields.")
            return
        success, msg = process_lj_itp.save_lj_itp(input_itp, output_itp, sigma_input, epsilon_input)
        if success:
            QMessageBox.information(self, "Success", f"Generated {output_itp}\n{msg}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to generate output:\n{msg}")
    def run_generate_packmolinp_gmx(self):
        import subprocess
        import re
        project_base = self.lineEdit_project_folder_3.text().strip()
        project_name = self.lineEdit_project_name_3.text().strip()
        pdb_file = self.coordinate_file_Edit_3.text().strip()
        density_str = self.lineEdit_density.text().strip()
        match = re.search(r"\([^,]+,[^,]+,([^,)]+)\)", density_str)
        if match:
            processed_density = match.group(1).strip()
        else:
            processed_density = density_str
        if not project_base or not project_name:
            QMessageBox.warning(self, "Warning", "Please select Project Folder and Name first.")
            return
        if not pdb_file or not os.path.exists(pdb_file):
            QMessageBox.warning(self, "Warning", "Please select a valid Coordinate (PDB) file.")
            return
        if not density_str:
            QMessageBox.warning(self, "Warning", "Please enter a Density value (kg/m3).")
            return
        target_dir = os.path.join(project_base, project_name, "targets", "ligand_liquid")
        os.makedirs(target_dir, exist_ok=True)
        inp_file = os.path.join(target_dir, "liquid.inp")
        liquid_pdb = os.path.join(target_dir, "liquid.pdb")
        liquid_gro = os.path.join(target_dir, "liquid.gro")
        gas_top = os.path.join(target_dir, "gas.top")
        liquid_top = os.path.join(target_dir, "liquid.top")
        current_dir = os.getcwd()
        template_file = os.path.join(current_dir, "temp", "template.packmol")
        success, msg = generate_packmolinp.generate_packmol_input(
            pdb_file, processed_density, template_file, inp_file
        )
        if not success:
            QMessageBox.critical(self, "Error", f"Failed to generate Packmol input:\n{msg}")
            return
        try:
            num_molecules = re.search(r"Molecules:\s*(\d+)", msg).group(1)
        except Exception:
            QMessageBox.critical(self, "Error", "Could not parse molecule count from generator.")
            return
        print("Running Packmol...")
        try:
            with open(inp_file, 'r') as f_in:
                proc = subprocess.run(["packmol"], stdin=f_in, cwd=target_dir, capture_output=True, text=True)
            if proc.returncode != 0:
                QMessageBox.critical(self, "Packmol Error", f"Packmol failed:\n{proc.stderr}")
                return
            if not os.path.exists(liquid_pdb):
                QMessageBox.critical(self, "Error", "Packmol ran but 'liquid.pdb' was not found.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred running Packmol:\n{str(e)}")
            return
        print("Running GMX editconf...")
        try:
            cmd_gmx = ["gmx", "editconf", "-f", "liquid.pdb", "-o", "liquid.gro", "-box", "3"]
            proc_gmx = subprocess.run(cmd_gmx, cwd=target_dir, capture_output=True, text=True)
            if proc_gmx.returncode != 0:
                QMessageBox.critical(self, "GMX Error", f"GMX editconf failed:\n{proc_gmx.stderr}")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred running GMX:\n{str(e)}")
            return
        if os.path.exists(gas_top):
            try:
                with open(gas_top, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                new_lines = []
                in_molecules_section = False
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("[") and "molecules" in stripped.lower():
                        in_molecules_section = True
                        new_lines.append(line)
                        continue
                    if in_molecules_section and stripped and not stripped.startswith(";"):
                        if stripped.startswith("["):
                            in_molecules_section = False
                            new_lines.append(line)
                        else:
                            parts = stripped.split()
                            if len(parts) >= 2:
                                parts[1] = str(num_molecules)
                                new_lines.append(f"{parts[0]:<15} {parts[1]}\n")
                            else:
                                new_lines.append(line)
                    else:
                        new_lines.append(line)
                with open(liquid_top, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"Successfully generated {liquid_top} with {num_molecules} molecules.")
            except Exception as e:
                QMessageBox.warning(self, "Topolgy Error", f"Failed to update molecules in topology:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Warning", f"gas.top not found at {gas_top}, skipping liquid.top generation.")
        self.display_liquid_pdb(liquid_pdb)
    def display_liquid_pdb(self, pdb_path):
        if not os.path.exists(pdb_path):
            return
        try:
            with open(pdb_path, 'r') as f:
                pdb_content = f.read()
            pdb_content_js = pdb_content.replace('\n', '\\n').replace('\r', '')
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
              <script src="https://3dmol.org/build/3Dmol-min.js"></script>
              <style>
                html, body {{ margin: 0; padding: 0; height: 100%; overflow: hidden; }}
                #container {{ width: 100%; height: 100%; }}
              </style>
            </head>
            <body>
              <div id="container"></div>
              <script>
                $(function() {{
                  let element = $("#container");
                  let viewer = $3Dmol.createViewer(element, {{ backgroundColor: "white" }});
                  let pdbData = `{pdb_content_js}`;
                  viewer.addModel(pdbData, "pdb");
                  viewer.setStyle({{}}, {{stick: {{radius: 0.15}}, sphere: {{scale: 0.15}}}});
                  viewer.zoomTo();
                  viewer.render();
                }});
              </script>
            </body>
            </html>
            """
            html_path = os.path.abspath(pdb_path.replace(".pdb", "_view.html"))
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.packmol_popup = PackmolViewDialog(self)
            url = QtCore.QUrl.fromLocalFile(html_path)
            self.packmol_popup.webEngineView.setUrl(url)
            self.packmol_popup.show()
            print(f"Visualization pop-up loaded: {html_path}")
        except Exception as e:
            print(f"Failed to generate visualization: {e}")
            QMessageBox.warning(self, "Visualization Error", f"Could not display PDB:\n{str(e)}")
    def run_generate_data_csv(self):
        project_base = self.lineEdit_project_folder_3.text().strip()
        project_name = self.lineEdit_project_name_3.text().strip()
        if not project_base or not project_name:
            QMessageBox.warning(self, "Warning", "Please ensure Project Folder and Name are filled.")
            return
        target_dir = os.path.join(project_base, project_name, "targets", "ligand_liquid")
        os.makedirs(target_dir, exist_ok=True)
        output_file = os.path.join(target_dir, "data.csv")
        current_dir = os.getcwd()
        template_file = os.path.join(current_dir, "temp", "template.data.csv")
        density_str = self.lineEdit_density.text().strip()
        hvap_str = self.lineEdit_enthalpy_of_vaporization.text().strip()
        r_denom = getattr(self, "denom_rho", "7.8")
        h_denom = getattr(self, "denom_hvap", "0.3")
        if not density_str:
            QMessageBox.warning(self, "Warning", "Density input is empty.")
            return
        success, msg = generate_data_csv.save_data_csv(
            density_str,
            hvap_str,
            template_file,
            output_file,
            rho_denom=r_denom,
            hvap_denom=h_denom
        )
        if success:
            print(f"Generated {output_file}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to generate data.csv:\n{msg}")
    def run_generate_fb_lj_in(self):
        project_base = self.lineEdit_project_folder_3.text().strip()
        project_name = self.lineEdit_project_name_3.text().strip()
        if not project_base or not project_name:
            QMessageBox.warning(self, "Warning", "Please ensure Project Folder and Name are filled.")
            return False
        project_full_path = os.path.join(project_base, project_name)
        output_path = os.path.join(project_full_path, "lj.in")
        fb_params = {
            "criteria": getattr(self, "fb_criteria", "1.0"),
            "forcefield": "ligand_lj.itp",
            "penalty_type": getattr(self, "fb_penalty_type", "L2"),
            "normalize_weights": getattr(self, "fb_normalize_weights", "0"),
            "maxstep": getattr(self, "fb_maxstep", "100"),
            "convergence_step": getattr(self, "fb_convergence_step", "0.01"),
            "convergence_objective": getattr(self, "fb_convergence_objective", "0.01"),
            "convergence_gradient": getattr(self, "fb_convergence_gradient", "0.01"),
            "trust0": getattr(self, "fb_trust0", "0.1"),
            "mintrust": getattr(self, "fb_mintrust", "0.05"),
            "adaptive_damping": getattr(self, "fb_adaptive_damping", "1.0"),
            "adaptive_factor": getattr(self, "fb_adaptive_factor", "1.2"),
            "eig_lowerbound": getattr(self, "fb_eig_lowerbound", "0.01"),
            "penalty_additive": getattr(self, "fb_penalty_additive", "1.0"),
            "weight": self.lineEdit_weight_3.text().strip() or "1.0",
            "liquid_eq_steps": self.lineEdit_liquid_eq_steps.text().strip() or "10000",
            "liquid_md_steps": self.lineEdit_liquid_md_steps.text().strip() or "100000",
            "liquid_timestep": self.lineEdit_liquid_timestep.text().strip() or "2.0",
            "gas_md_steps": self.lineEdit_gas_md_steps.text().strip() or "100000",
            "gas_timestep": self.lineEdit_gas_timestep.text().strip() or "1.0",
            "w_rho": self.lineEdit_w_rho.text().strip() or "1.0",
            "w_hvap": self.lineEdit_w_hvap.text().strip() or "1.0",
            "md_threads": self.lineEdit_md_threads.text().strip() or "1"
        }
        try:
            save_fb_lj_in(output_path, **fb_params)
            print(f"ForceBalance LJ config generated: {output_path}")
            return True, project_full_path
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate LJ config:\n{str(e)}")
            return False, None
    def run_full_workflow_3(self):
        self.run_generate_data_csv()
        success, working_dir = self.run_generate_fb_lj_in()
        if success:
            try:
                current_dir = os.getcwd()
                temp_dir = os.path.join(current_dir, "temp")
                target_liquid_dir = os.path.join(working_dir, "targets", "ligand_liquid")
                os.makedirs(target_liquid_dir, exist_ok=True)
                for mdp_file in ["gas.mdp", "liquid.mdp"]:
                    source_path = os.path.join(temp_dir, mdp_file)
                    destination_path = os.path.join(target_liquid_dir, mdp_file)
                    if os.path.exists(source_path):
                        shutil.copy(source_path, destination_path)
                        print(f"Copied {mdp_file} to {target_liquid_dir}")
                    else:
                        print(f"Warning: Source file {source_path} not found.")
            except Exception as e:
                QMessageBox.warning(self, "Copy Error", f"Failed to copy mdp files: {str(e)}")
            self.run_forcebalance_exec_lj(working_dir)
    def run_forcebalance_exec_lj(self, working_dir):
        self.fb_log_cache_lj = ""
        from plot_data import LJOutputHandler
        self.lj_handler = LJOutputHandler(working_dir)
        self.fb_process_lj.setWorkingDirectory(working_dir)
        self.fb_process_lj.start("ForceBalance.py", ["lj.in"])
        self.progress_dialog = QProgressDialog("Running FB Liquid Optimization...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("LJ Optimization Status")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.fb_process_lj.kill)
        self.progress_dialog.show()
    def on_fb_lj_output(self):
        data = self.fb_process_lj.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        stderr = self.fb_process_lj.readAllStandardError().data().decode('utf-8', errors='ignore')
        full_output = data + stderr
        if full_output:
            print(full_output.strip())
            self.fb_log_cache_lj += full_output
            if hasattr(self, 'lj_handler'):
                trigger_keywords = ["Iteration", "Total", "Total Gradient", "Calculation Finished", "Objective function rises"]
                if any(kw in full_output for kw in trigger_keywords):
                    self.lj_handler.parse_and_save(self.fb_log_cache_lj)
                    print('#------------lj_handler--process----')
    def on_fb_finished_lj(self, exit_code, exit_status):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
        if exit_status == QProcess.NormalExit and exit_code == 0:
            QMessageBox.information(self, "Success", "LJ Optimization finished successfully!")
        else:
            QMessageBox.critical(self, "Error", f"LJ Optimization failed with exit code: {exit_code}")
