import sys
import os
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QProgressDialog
from gui import MyMainWindow, Psi4SettingDialog, FbSettingDialog, VibAnimateDialog
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
from process_dih_itp import save_dihedrals_to_itp
class AtomBridge(QObject):
    atomsSelected = pyqtSignal(list)
    def __init__(self, parent=None):
        super(AtomBridge, self).__init__(parent)
    @pyqtSlot(str)
    def receiveAtoms(self, atoms_str):
        if atoms_str:
            atom_list = atoms_str.split(',')
            self.atomsSelected.emit(atom_list)
class dih_logic:
    def select_coordinate_file_2(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Coordinate File",
            "./",
            "Coordinate File (*.pdb)"
        )
        if file_path:
            self.coordinate_file_Edit_2.setText(file_path)
    def select_topology_file_2(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Topology File",
            "./",
            "Topology File (*.top);;All Files (*)"
        )
        if file_path:
            self.lineEdit_topology_file_2.setText(file_path)
    def select_project_folder_2(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Working Directory", "./")
        if folder_path:
            self.lineEdit_project_folder_2.setText(folder_path)
    def create_new_directory_2(self):
        base_path = self.lineEdit_project_folder_2.text().strip()
        folder_name = self.lineEdit_project_name_2.text().strip()
        if not base_path or not folder_name:
            QMessageBox.warning(self, "Warning", "Please ensure 'Project Name' and 'Project Folder' are filled in.")
            return
        project_full_path = os.path.join(base_path, folder_name)
        forcefield_path = os.path.join(project_full_path, "forcefield")
        targets_path = os.path.join(project_full_path, "targets")
        ligand_dih_path = os.path.join(targets_path, "ligand_dih")
        scan_path = os.path.join(project_full_path, "scan")
        try:
            os.makedirs(forcefield_path, exist_ok=True)
            os.makedirs(targets_path, exist_ok=True)
            os.makedirs(ligand_dih_path, exist_ok=True)
            os.makedirs(scan_path, exist_ok=True)
            msg = (f"Created successfully\n\n"
                   f"Directory: {project_full_path}\n"
                   f"Subfolders: forcefield/, targets/, scan/")
            QMessageBox.information(self, "Success", msg)
            print(f"Created: {forcefield_path}")
            print(f"Created: {targets_path}")
            print(f"Created: {scan_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fail", f"Failed to create directory：\n{str(e)}")
    def execute_expansion_2(self):
        input_path = self.lineEdit_topology_file_2.text().strip()
        if not input_path:
            QMessageBox.warning(self, "Warning", "Please select a Topology file first.")
            return
        project_base = self.lineEdit_project_folder_2.text().strip()
        project_name = self.lineEdit_project_name_2.text().strip()
        target_dir = os.path.join(project_base, project_name, "forcefield")
        output_path = os.path.join(target_dir, "ligand.itp")
        success, message = expand_gromacs_includes.run_expansion(input_path, output_path)
        if success:
            QMessageBox.information(self, "Success", message)
            print(f"Log: {message}")
        else:
            QMessageBox.critical(self, "Error", message)
        return success
    def run_extract_system_section_2(self):
        project_base = self.lineEdit_project_folder_2.text().strip()
        project_name = self.lineEdit_project_name_2.text().strip()
        source_dir = os.path.join(project_base, project_name, "forcefield")
        input_file = os.path.join(source_dir, "ligand.itp")
        target_dir = os.path.join(project_base, project_name, "targets", "ligand_dih")
        output_file = os.path.join(target_dir, "topol.top")
        split_topol.extract_system_section(input_file, output_file)
    def run_process_input_topol_2(self):
        step1_success = self.execute_expansion_2()
        if not step1_success:
            return
        self.run_extract_system_section_2()
    def run_process_input_pdb_2(self):
        input_pdb_file = self.coordinate_file_Edit_2.text().strip()
        project_base = self.lineEdit_project_folder_2.text().strip()
        project_name = self.lineEdit_project_name_2.text().strip()
        target_dir = os.path.join(project_base, project_name, "scan")
        target_filename = "ligand.pdb"
        target_path = os.path.join(target_dir, target_filename)
        if not os.path.exists(input_pdb_file):
            print(f"Error: Source file {input_pdb_file} does not exist.")
            return
        try:
            shutil.copy(input_pdb_file, target_path)
            print(f"Copied {input_pdb_file} to {target_path}")
        except Exception as e:
            QMessageBox.critical(self, "Copy Error", f"Failed to copy coordinate file:\n{str(e)}")
    def run_psi4_generation_file_2(self):
        val_memory = self.psi4_memory
        val_threads = self.psi4_cpu
        charge = self.lineEdit_charge_2.text().strip()
        multiplicity = self.lineEdit_Multiplicity_2.text().strip()
        basis = self.comboBox_basis_2.currentText().strip()
        method = self.comboBox_method_2.currentText().strip()
        project_base = self.lineEdit_project_folder_2.text().strip()
        project_name = self.lineEdit_project_name_2.text().strip()
        if not project_base or not project_name:
            QMessageBox.warning(self, "Warning", "Please set Project Folder and Name first.")
            return
        target_dir = os.path.join(project_base, project_name, "scan")
        pdb_file = os.path.join(target_dir, "ligand.pdb")
        output_file = os.path.join(target_dir, "psi4.dat")
        current_dir = os.getcwd()
        template_file = os.path.join(current_dir, "temp", "template.psi4.dih")
        success, msg = generate_psi4_dat.create_psi4_file(
            charge=charge,
            multiplicity=multiplicity,
            basis_set=basis,
            method=method,
            memory=val_memory,
            threads=val_threads,
            template_path=template_file,
            output_path=output_file,
            pdb_path=pdb_file
        )
        if success:
            QMessageBox.information(self, "Success", f"Psi4 input file created in 'scan' folder:\n{output_file}")
        else:
            QMessageBox.critical(self, "Error", msg)
    def open_dihedral_viewer(self):
        pdb_path = self.coordinate_file_Edit_2.text().strip()
        if not pdb_path or not os.path.exists(pdb_path):
            QMessageBox.warning(self, "Warning", "Please select a valid PDB file!")
            return
        try:
            with open(pdb_path, 'r') as f:
                pdb_content = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Read Error: {e}")
            return
        self.dihedral_win = QMainWindow(self)
        self.dihedral_win.setWindowTitle("Dihedral Atom Selector")
        self.dihedral_win.resize(562, 476)
        web_view = QWebEngineView()
        bridge = AtomBridge(web_view)
        bridge.atomsSelected.connect(self.update_dihedral_lineedit)
        channel = QWebChannel(web_view.page())
        channel.registerObject("pyBridge", bridge)
        web_view.page().setWebChannel(channel)
        html_content = generate_dihedral_html(pdb_content)
        web_view.setHtml(html_content)
        self.dihedral_win.setCentralWidget(web_view)
        self.dihedral_win.show()
    def update_dihedral_lineedit(self, atom_list):
        new_atoms_str = " ".join(atom_list)
        current_text = self.lineEdit_select_dihedral_angle.text().strip()
        if current_text:
            updated_text = f"{current_text};{new_atoms_str}"
        else:
            updated_text = new_atoms_str
        self.lineEdit_select_dihedral_angle.setText(updated_text)
    def save_dihedrals_to_scan(self):
        base_path = self.lineEdit_project_folder_2.text().strip()
        folder_name = self.lineEdit_project_name_2.text().strip()
        if not base_path or not folder_name:
            QMessageBox.warning(self, "Warning", "Please ensure 'Project Name' and 'Project Folder' are filled in.")
            return
        scan_dir = os.path.join(base_path, folder_name, "scan")
        file_path = os.path.join(scan_dir, "dihedrals.txt")
        raw_text = self.lineEdit_select_dihedral_angle.text().strip()
        if not raw_text:
            QMessageBox.warning(self, "Warning", "Dihedral Angle is empty!")
            return
        processed_text = raw_text.replace(";", "\n")
        try:
            os.makedirs(scan_dir, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(processed_text)
            print(f"File saved: {file_path}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save dihedrals.txt:\n{str(e)}")
            return False
    def run_process_dih_itp(self):
        base_path = self.lineEdit_project_folder_2.text().strip()
        folder_name = self.lineEdit_project_name_2.text().strip()
        if not base_path or not folder_name:
            QMessageBox.warning(self, "Warning", "Please ensure 'Project Name' and 'Project Folder' are filled in.")
            return
        forcefield_dir = os.path.join(base_path, folder_name, "forcefield")
        input_itp_path = os.path.join(forcefield_dir, "ligand.itp")
        output_itp_path = os.path.join(forcefield_dir, "ligand_dih.itp")
        dihedral_str = self.lineEdit_select_dihedral_angle.text().strip()
        if not dihedral_str:
            QMessageBox.warning(self, "Warning", "Please select dihedrals first (Input is empty).")
            return
        try:
            success, msg = save_dihedrals_to_itp(input_itp_path, dihedral_str, output_path=output_itp_path)
            if success:
                print(f"ITP Processed: {input_itp_path} -> {output_itp_path}")
                print(f"Log: {msg}")
                return True
            else:
                QMessageBox.warning(self, "Failed", f"Failed to update ITP:\n{msg}")
                return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")
            return False
    def run_torsiondrive_cmd(self):
        base_path = self.lineEdit_project_folder_2.text().strip()
        folder_name = self.lineEdit_project_name_2.text().strip()
        grid_spacing = self.lineEdit_grid_spacing.text().strip()
        if not grid_spacing:
            QMessageBox.warning(self, "Warning", "Please enter Grid Spacing (e.g. 15).")
            return
        scan_dir = os.path.abspath(os.path.join(base_path, folder_name, "scan"))
        if not os.path.exists(os.path.join(scan_dir, "psi4.dat")):
            QMessageBox.warning(self, "Error", "psi4.dat not found in scan folder! Please generate it first.")
            return
        if not hasattr(self, 'td_process'):
            self.td_process = QProcess()
            self.td_process.readyReadStandardOutput.connect(self.on_td_output)
            self.td_process.readyReadStandardError.connect(self.on_td_output)
            self.td_process.finished.connect(self.on_torsiondrive_finished)
        if self.td_process.state() == QProcess.Running:
            QMessageBox.warning(self, "Warning", "TorsionDrive is already running.")
            return
        self.td_process.setWorkingDirectory(scan_dir)
        program = "torsiondrive-launch"
        arguments = [
            "psi4.dat",
            "dihedrals.txt",
            "-g", grid_spacing,
            "-e", "psi4",
            "-v"
        ]
        print(f"Executing: {program} {' '.join(arguments)}")
        self.td_process.start(program, arguments)
        self.progress_dialog = QProgressDialog("TorsionDrive is running... This may take hours.", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("TorsionDrive Status")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.kill_td_process)
        self.progress_dialog.show()
    def on_td_output(self):
        data = self.td_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        if data:
            print(data.strip())
        err = self.td_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        if err:
            print(f"TD_LOG: {err.strip()}")
    def kill_td_process(self):
        if hasattr(self, 'td_process') and self.td_process.state() == QProcess.Running:
            self.td_process.kill()
            print("TorsionDrive process killed by user.")
    def on_torsiondrive_finished(self, exit_code, exit_status):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        if exit_status == QProcess.NormalExit and exit_code == 0:
            QMessageBox.information(self, "Success", "TorsionDrive finished successfully!\nYou can now proceed to Refinement.")
        else:
            if exit_status == QProcess.CrashExit:
                 print("TorsionDrive stopped.")
            else:
                 QMessageBox.critical(self, "Error", f"TorsionDrive failed. (Exit code: {exit_code})\nCheck console for details.")
    def run_torsiondrive_all(self):
        if not self.save_dihedrals_to_scan():
            return
        if not self.run_process_dih_itp():
            return
        self.run_torsiondrive_cmd()
    def copy_and_xyz_convert_pdb(self):
        base_path = self.lineEdit_project_folder_2.text().strip()
        folder_name = self.lineEdit_project_name_2.text().strip()
        if not base_path or not folder_name:
            QMessageBox.warning(self, "Warning", "Please ensure 'Project Name' and 'Project Folder' are filled in for Tab 2.")
            return False
        project_full_path = os.path.abspath(os.path.join(base_path, folder_name))
        scan_dir = os.path.join(project_full_path, "scan")
        ligand_dih_dir = os.path.join(project_full_path, "targets", "ligand_dih")
        xyz_file = os.path.join(scan_dir, "scan.xyz")
        if not os.path.exists(xyz_file):
            QMessageBox.critical(self, "Error", f"Required file not found: {xyz_file}\nPlease ensure TorsionDrive finished correctly.")
            return False
        process = QProcess()
        process.setWorkingDirectory(scan_dir)
        program = "obabel"
        dst_pdb_path = os.path.join(ligand_dih_dir, "scan.pdb")
        arguments = ["scan.xyz", "-O", dst_pdb_path]
        print(f"Running: {program} {' '.join(arguments)} in {scan_dir}")
        process.start(program, arguments)
        if not process.waitForFinished(30000):
            QMessageBox.critical(self, "Error", "obabel command timed out or failed to start.")
            return False
        if process.exitCode() != 0:
            err_msg = process.readAllStandardError().data().decode('utf-8', errors='ignore')
            QMessageBox.critical(self, "Error", f"obabel failed with error:\n{err_msg}")
            return False
        if os.path.exists(dst_pdb_path):
            try:
                with open(dst_pdb_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                cryst_line = "CRYST1    0.000    0.000    0.000  90.00  90.00  90.00 P 1           1\n"
                lines.insert(1, cryst_line)
                with open(dst_pdb_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"Successfully inserted CRYST1 line into {dst_pdb_path}")
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Failed to insert CRYST1 line into scan.pdb:\n{str(e)}")
        src_qdata = os.path.join(scan_dir, "qdata.txt")
        dst_qdata = os.path.join(ligand_dih_dir, "qdata.txt")
        if os.path.exists(src_qdata):
            try:
                shutil.copy2(src_qdata, dst_qdata)
                print(f"File copied and renamed to: {dst_qdata}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to copy qdata.txt:\n{str(e)}")
                return False
        else:
            QMessageBox.warning(self, "Warning", "obabel finished, but qdata.txt was not found in scan folder.")
            return False
    def run_generate_fb_dih_in(self):
        project_base = self.lineEdit_project_folder_2.text().strip()
        project_name = self.lineEdit_project_name_2.text().strip()
        if not project_base or not project_name:
            QMessageBox.warning(self, "Warning", "Please set Project Folder and Name for Tab 2 first.")
            return
        project_full_path = os.path.join(project_base, project_name)
        output_path = os.path.join(project_full_path, "dih.in")
        val_forcefield = "ligand_dih.itp"
        fb_dih_params = {
            "criteria": self.fb_criteria,
            "maxstep": self.fb_maxstep,
            "convergence_gradient": self.fb_convergence_gradient,
            "convergence_objective": self.fb_convergence_objective,
            "convergence_step": self.fb_convergence_step,
            "trust0": self.fb_trust0,
            "mintrust": self.fb_mintrust,
            "adaptive_damping": self.fb_adaptive_damping,
            "adaptive_factor": self.fb_adaptive_factor,
            "eig_lowerbound": self.fb_eig_lowerbound,
            "penalty_additive": self.fb_penalty_additive,
            "normalize_weights": self.fb_normalize_weights,
            "penalty_type": self.fb_penalty_type,
            "forcefield": val_forcefield,
            "weight": self.lineEdit_weight_2.text().strip(),
            "energy": self.lineEdit_energy.text().strip(),
            "force": self.lineEdit_force.text().strip(),
            "w_energy": self.lineEdit_w_energy.text().strip(),
            "w_force": self.lineEdit_w_force.text().strip()
        }
        try:
            from generate_fb_dih_in import generate_fb_dih
            generate_fb_dih(output_path, **fb_dih_params)
            print(f"Success! Dihedral fitting config generated: {output_path}")
            self.run_forcebalance_exec_dih(project_full_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate dih.in:\n{str(e)}")
    def run_forcebalance_exec_dih(self, working_dir):
        self.fb_log_cache_2 = ""
        from plot_data import FBOutputHandler
        self.fb_handler = FBOutputHandler(working_dir)
        self.fb_process_2.setWorkingDirectory(working_dir)
        self.fb_process_2.start("ForceBalance.py", ["dih.in"])
        self.progress_dialog = QProgressDialog("Running ForceBalance (Dihedral Fit)...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("(Dihedral Fit Status")
        self.progress_dialog.canceled.connect(self.kill_fb_process_2)
        self.progress_dialog.show()
    def kill_fb_process_2(self):
        if self.fb_process_2.state() == QProcess.Running:
            self.fb_process_2.kill()
            print("Tab 2 ForceBalance process killed by user.")
    def on_fb_dih_output(self):
        data = self.fb_process_2.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        err_data = self.fb_process_2.readAllStandardError().data().decode('utf-8', errors='ignore')
        combined_data = data + err_data
        if combined_data:
            print(combined_data, end="")
            self.fb_log_cache_2 += combined_data
            if "Step" in combined_data or "Total Gradient" in combined_data:
                if hasattr(self, 'fb_handler'):
                    self.fb_handler.parse_and_save(self.fb_log_cache_2)
    def on_fb_finished_2(self, exit_code, exit_status):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        error_keywords = ["Traceback", "Error:", "CRITICAL"]
        if exit_status == QProcess.NormalExit and exit_code == 0:
            found_error = any(kw in self.fb_log_cache_2 for kw in error_keywords)
            if found_error:
                QMessageBox.critical(self, "Error", "ForceBalance (Tab 2) had internal errors. Check console.")
            else:
                QMessageBox.information(self, "Success", "Dihedral Fit finished successfully!")
        elif exit_status == QProcess.CrashExit:
             print("Tab 2 process crashed/stopped.")
        else:
            QMessageBox.critical(self, "Error", f"Tab 2 Fit failed with exit code: {exit_code}")
    def run_full_workflow_2(self):
        if not self.copy_and_xyz_convert_pdb():
            return
        self.run_generate_fb_dih_in()
