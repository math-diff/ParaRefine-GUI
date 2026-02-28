import sys
import os
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QProgressDialog
from gui import MyMainWindow, Psi4SettingDialog, FbSettingDialog, VibAnimateDialog,PackmolViewDialog
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
from dih_logic import dih_logic
from lj_logic import lj_logic
from analyze_logic import AnalyzeLogic
from plot_data import VibOutputHandler
class VibLogicDialog(VibAnimateDialog):
    def __init__(self, parent=None, html_files=None):
        super(VibLogicDialog, self).__init__(parent)
        self.html_files = html_files if html_files else []
        self.current_index = 0
        self.pushButton_next.clicked.connect(self.show_next)
        self.pushButton_prev.clicked.connect(self.show_prev)
        if self.html_files:
            self.load_current_html()
        else:
            print("No HTML files list provided to dialog.")
    def load_current_html(self):
        if 0 <= self.current_index < len(self.html_files):
            file_path = self.html_files[self.current_index]
            abs_path = os.path.abspath(file_path)
            url = QUrl.fromLocalFile(abs_path)
            self.webEngineView_vib.setUrl(url)
            file_name = os.path.basename(file_path)
            self.setWindowTitle(f"Vibration Animation - {file_name} ({self.current_index + 1}/{len(self.html_files)})")
    def show_next(self):
        if self.html_files and self.current_index < len(self.html_files) - 1:
            self.current_index += 1
            self.load_current_html()
        else:
            print("Already at the last file.")
    def show_prev(self):
        if self.html_files and self.current_index > 0:
            self.current_index -= 1
            self.load_current_html()
        else:
            print("Already at the first file.")
class MainWindowLogic(MyMainWindow, dih_logic, lj_logic, AnalyzeLogic):
    def __init__(self):
        super(MainWindowLogic, self).__init__()
        self.vib_handler = None
        self.connect_bond_tab_signals()
    def connect_bond_tab_signals(self):
        self.pushButton_project_folder.clicked.connect(self.select_project_folder)
        self.pushButton_create_folder.clicked.connect(self.create_new_directory)
        self.browse_topology_browse.clicked.connect(self.select_topology_file)
        self.browse_coodrinate.clicked.connect(self.select_coordinate_file)
        self.pushButton_process_input.clicked.connect(self.run_process_input_topol)
        self.pushButton_process_input.clicked.connect(self.run_process_input_pdb)
        self.compute_button.clicked.connect(self.run_psi4_all)
        self.checkBox_select_all.toggled.connect(self.on_select_all_toggled)
        self.run_button.clicked.connect(self.run_full_workflow)
        self.connect_dih_tab_signals()
    def connect_dih_tab_signals(self):
        self.pushButton_project_folder_2.clicked.connect(self.select_project_folder_2)
        self.pushButton_create_folder_2.clicked.connect(self.create_new_directory_2)
        self.browse_topology_browse_2.clicked.connect(self.select_topology_file_2)
        self.browse_coodrinate_2.clicked.connect(self.select_coordinate_file_2)
        self.pushButton_process_input_2.clicked.connect(self.run_process_input_topol_2)
        self.pushButton_process_input_2.clicked.connect(self.run_process_input_pdb_2)
        self.pushButton_view_dihedral.clicked.connect(self.open_dihedral_viewer)
        self.pushbutton_creat_psi4_dat.clicked.connect(self.run_psi4_generation_file_2)
        self.pushbutton_compute.clicked.connect(self.run_torsiondrive_all)
        self.run_button_2.clicked.connect(self.run_full_workflow_2)
        self.connect_lj_tab_signals()
    def connect_lj_tab_signals(self):
        self.pushButton_project_folder_3.clicked.connect(self.select_project_folder_3)
        self.pushButton_create_folder_3.clicked.connect(self.create_new_directory_3)
        self.browse_topology_browse_3.clicked.connect(self.select_topology_file_3)
        self.browse_coodrinate_3.clicked.connect(self.select_coordinate_file_3)
        self.pushButton_process_input_3.clicked.connect(self.run_process_input_topol_3)
        self.pushButton_process_input_3.clicked.connect(self.pdb_convert_gas_gro)
        self.pushButton_process_itp.clicked.connect(self.run_process_lj_itp)
        self.pushButton_start_modeling.clicked.connect(self.run_generate_packmolinp_gmx)
        self.run_button_3.clicked.connect(self.run_full_workflow_3)
        self.connect_analyze_tab_signals()
    def connect_analyze_tab_signals(self):
        self.pushButton_browse_Score.clicked.connect(self.select_analyze_score_file)
        self.pushButton_browse_Grad.clicked.connect(self.select_analyze_grad_file)
        self.pushButton_browse_rmsd.clicked.connect(self.select_analyze_rmsd_file)
        self.pushButton_browse_vibration_mode.clicked.connect(self.select_analyze_vib_mode_file)
        self.pushButton_browse_energy_difference.clicked.connect(self.select_analyze_energy_diff_file)
        self.pushButton_browse_density_hvap.clicked.connect(self.select_analyze_density_hvap_file)
        self.pushButton_view_plot.clicked.connect(self.run_plot)
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.on_process_output)
        self.process.readyReadStandardError.connect(self.on_process_output)
        self.process.finished.connect(self.on_process_finished_convert)
        self.progress_dialog = None
        self.fb_process = QProcess()
        self.fb_process.readyReadStandardOutput.connect(self.on_fb_output)
        self.fb_process.readyReadStandardError.connect(self.on_fb_output)
        self.fb_process.finished.connect(self.on_fb_finished)
        self.fb_log_cache = ""
        self.fb_process_2 = QProcess()
        self.fb_process_2.readyReadStandardOutput.connect(self.on_fb_dih_output)
        self.fb_process_2.readyReadStandardError.connect(self.on_fb_dih_output)
        self.fb_process_2.finished.connect(self.on_fb_finished_2)
        self.fb_log_cache_2 = ""
        self.td_process = QProcess()
        self.td_process.readyReadStandardOutput.connect(self.on_td_output)
        self.td_process.readyReadStandardError.connect(self.on_td_output)
        self.td_process.finished.connect(self.on_torsiondrive_finished)
        self.fb_process_lj = QProcess()
        self.fb_process_lj.readyReadStandardOutput.connect(self.on_fb_lj_output)
        self.fb_process_lj.readyReadStandardError.connect(self.on_fb_lj_output)
        self.fb_process_lj.finished.connect(self.on_fb_finished_lj)
        self.fb_log_cache_lj = ""
    def select_coordinate_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Coordinate File",
            "./",
            "Coordinate File (*.pdb)"
        )
        if file_path:
            self.coordinate_file_Edit.setText(file_path)
    def select_topology_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Topology File",
            "./",
            "Topology File (*.top);;All Files (*)"
        )
        if file_path:
            self.lineEdit_topology_file.setText(file_path)
    def select_project_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Working Directory", "./")
        if folder_path:
            self.lineEdit_project_folder.setText(folder_path)
    def create_new_directory(self):
        base_path = self.lineEdit_project_folder.text().strip()
        folder_name = self.lineEdit_project_name.text().strip()
        if not base_path or not folder_name:
            QMessageBox.warning(self, "Warning", "Please ensure 'Project Name' and 'Project Folder' are filled in.")
            return
        project_full_path = os.path.join(base_path, folder_name)
        forcefield_path = os.path.join(project_full_path, "forcefield")
        targets_path = os.path.join(project_full_path, "targets")
        ligand_optgeo_path = os.path.join(targets_path, "ligand_optgeo")
        ligand_vib_path = os.path.join(targets_path, "ligand_vib")
        psi4_working_path = os.path.join(project_full_path, "psi4_working")
        try:
            os.makedirs(forcefield_path, exist_ok=True)
            os.makedirs(targets_path, exist_ok=True)
            os.makedirs(ligand_vib_path, exist_ok=True)
            os.makedirs(ligand_optgeo_path, exist_ok=True)
            os.makedirs(psi4_working_path, exist_ok=True)
            msg = (f"Created successfully\n\n"
                   f"Create Directory: {project_full_path}\n"
                   f"Include subfolders: forcefield/, targets/, psi4_working/")
            QMessageBox.information(self, "Success", msg)
            print(f"Created: {forcefield_path}")
            print(f"Created: {targets_path}")
            print(f"Created: {psi4_working_path}")
            print(f"Created: {ligand_vib_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fail", f"Failed to create directory：\n{str(e)}")
    def execute_expansion(self):
        input_path = self.lineEdit_topology_file.text().strip()
        if not input_path:
            QMessageBox.warning(self, "Warning", "Please select a Topology file first.")
            return
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        target_dir = os.path.join(project_base, project_name, "forcefield")
        output_path = os.path.join(target_dir, "ligand.itp")
        success, message = expand_gromacs_includes.run_expansion(input_path, output_path)
        if success:
            QMessageBox.information(self, "Success", message)
            print(f"Log: {message}")
        else:
            QMessageBox.critical(self, "Error", message)
        return success
    def run_extract_system_section(self):
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        source_dir = os.path.join(project_base, project_name, "forcefield")
        input_file = os.path.join(source_dir, "ligand.itp")
        target_vib_dir = os.path.join(project_base, project_name, "targets", "ligand_vib")
        output_file_vib = os.path.join(target_vib_dir, "topol.top")
        target_opt_dir = os.path.join(project_base, project_name, "targets", "ligand_optgeo")
        output_file_opt = os.path.join(target_opt_dir, "topol.top")
        split_topol.extract_system_section(input_file, output_file_vib)
        print(f"Generated: {output_file_vib}")
        try:
            shutil.copy(output_file_vib, output_file_opt)
            print(f"Copied topol.top to: {target_opt_dir}")
        except Exception as e:
            print(f"Failed to copy topol.top to ligand_optgeo: {str(e)}")
    def run_process_fb_itp(self):
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        forcefield_dir = os.path.join(project_base, project_name, "forcefield")
        input_file = os.path.join(forcefield_dir, "ligand.itp")
        output_file = os.path.join(forcefield_dir, "ligand_fb.itp")
        if os.path.exists(input_file):
            try:
                process_fb_itp.process_itp(input_file, output_file)
                print(f"Generated: {output_file}")
            except SystemExit:
                QMessageBox.warning(self, "Warning", "Error occurred in itp processing module.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to process itp:\n{str(e)}")
        else:
            print(f"Warning: {input_file} not found. Skipping fb itp generation.")
    def run_process_input_topol(self):
        step1_success = self.execute_expansion()
        if not step1_success:
            return
        self.run_extract_system_section()
        self.run_process_fb_itp()
    def run_process_input_pdb(self):
        input_pdb_file = self.coordinate_file_Edit.text().strip()
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        target_dir = os.path.join(project_base, project_name, "psi4_working")
        target_filename = "ligand.pdb"
        target_path = os.path.join(target_dir, target_filename)
        if not os.path.exists(input_pdb_file):
            print(f"Error: Source file {input_pdb_file} does not exist.")
            return
        try:
            shutil.copy(input_pdb_file, target_path)
            print(f"Copied {input_pdb_file} to {target_path}")
            self.run_gmx_pdb2gro(target_dir)
        except Exception as e:
            QMessageBox.critical(self, "Copy Error", f"Failed to copy coordinate file:\n{str(e)}")
    def run_gmx_pdb2gro(self, working_dir):
        print("Starting GMX conversion...")
        gmx_process = QProcess()
        gmx_process.setWorkingDirectory(working_dir)
        gmx_process.setProcessChannelMode(QProcess.MergedChannels)
        program = "gmx"
        arguments = [
            "editconf",
            "-f", "ligand.pdb",
            "-o", "../targets/ligand_vib/ligand.gro"
        ]
        gmx_process.start(program, arguments)
        gmx_process.waitForFinished()
        if gmx_process.exitStatus() == QProcess.NormalExit and gmx_process.exitCode() == 0:
            print("GMX editconf finished successfully.")
            output = gmx_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            print(output)
        else:
            error_msg = gmx_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            print(f"GMX editconf failed: {error_msg}")
            QMessageBox.warning(self, "GMX Error", f"Failed to convert pdb to gro:\n{error_msg}")
    def run_psi4_generation_file(self):
        val_memory = self.psi4_memory
        val_threads = self.psi4_cpu
        charge = self.lineEdit_charge.text().strip()
        multiplicity = self.lineEdit_Multiplicity.text().strip()
        basis = self.comboBox_basis.currentText().strip()
        method = self.comboBox_method.currentText().strip()
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        current_dir = os.getcwd()
        template_file = os.path.join(current_dir, "temp", "template.psi4")
        self.target_dir = os.path.join(project_base, project_name, "psi4_working")
        pdb_file = os.path.join(self.target_dir, "ligand.pdb")
        output_file = os.path.join(self.target_dir, "psi4.dat")
        success, msg=generate_psi4_dat.create_psi4_file(
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
        return success, msg
    def run_psi4(self):
        self.process.setWorkingDirectory(self.target_dir)
        self.process.start("psi4", ["psi4.dat"])
        self.progress_dialog = QProgressDialog("Calculating Psi4... Please wait.", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("Psi4 Status")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.kill_psi4_process)
        self.progress_dialog.show()
    def kill_psi4_process(self):
        if self.process.state() == QProcess.Running:
            self.process.kill()
            print("Process killed by user.")
    def on_process_output(self):
        data = self.process.readAllStandardOutput()
        stderr = self.process.readAllStandardError()
        if data:
            print(data.data().decode('utf-8', errors='ignore').strip())
        if stderr:
            print("ERR:", stderr.data().decode('utf-8', errors='ignore').strip())
    def on_process_finished_convert(self, exit_code, exit_status):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        if exit_status == QProcess.NormalExit and exit_code == 0:
            print("Psi4 calculation finished. Starting conversion...")
            psi4_output_file = os.path.join(self.target_dir, "psi4.out")
            if os.path.exists(psi4_output_file):
                try:
                    project_base = self.lineEdit_project_folder.text().strip()
                    project_name = self.lineEdit_project_name.text().strip()
                    destination_dir = os.path.join(project_base, project_name, "targets", "ligand_vib")
                    gro_file_path = os.path.join(destination_dir, "ligand.gro")
                    if os.path.exists(gro_file_path):
                        print(f"Updating coordinates in {gro_file_path}...")
                        update_success = update_coord.update_gro_with_psi4(psi4_output_file, gro_file_path)
                        if not update_success:
                            print("Warning: Coordinate update reported failure.")
                    else:
                        print(f"Warning: {gro_file_path} not found. Skipping coordinate update.")
                    output_vdata_path = os.path.join(destination_dir, "vdata_start.txt")
                    psi4out_convert_vdata.generate_vdata(psi4_output_file, output_vdata_path)
                    QMessageBox.information(self, "Success", f"Psi4 calculation and conversion finished!\nGenerated: {output_vdata_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Conversion Error", f"Psi4 finished, but data conversion failed:\n{str(e)}")
            else:
                QMessageBox.critical(self, "Error", f"Psi4 finished but output file not found:\n{psi4_output_file}")
        elif exit_status == QProcess.CrashExit:
             print("Psi4 process crashed or killed.")
        else:
            QMessageBox.critical(self, "Error", f"Psi4 failed with exit code: {exit_code}")
    def run_psi4_all(self):
        step1_success, _ = self.run_psi4_generation_file()
        if not step1_success:
            return
        self.run_psi4()
    def run_anifrq_generation(self):
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        if not project_base or not project_name:
            QMessageBox.warning(self, "Warning", "Please select Project Folder and Name first.")
            return False
        psi4_working_dir = os.path.join(project_base, project_name, "psi4_working")
        psi4_out_file = os.path.join(psi4_working_dir, "psi4.out")
        if not os.path.exists(psi4_out_file):
            QMessageBox.critical(self, "Error",
                f"psi4.out not found in:\n{psi4_working_dir}\n\n"
                "Please run the Psi4 calculation first.")
            return False
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            count, files = anifrq_all.generate_all_animations(psi4_out_file)
            QApplication.restoreOverrideCursor()
            print(f"Generated {count} animation files in {psi4_working_dir}")
            return True
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error", f"Failed to generate animations:\n{str(e)}")
            return False
    def open_vib_dialog(self):
        success = self.run_anifrq_generation()
        if success:
            try:
                project_base = self.lineEdit_project_folder.text().strip()
                project_name = self.lineEdit_project_name.text().strip()
                psi4_working_dir = os.path.join(project_base, project_name, "psi4_working")
                xyz_pattern = os.path.join(psi4_working_dir, "psi4.mode*.xyz")
                xyz_files = glob.glob(xyz_pattern)
                if not xyz_files:
                    print("Warning: No .xyz files found to convert to HTML.")
                    return
                for xyz_path in xyz_files:
                    generate_vib_html.save_vibration_fast(xyz_path, bohr_to_angstrom=False)
                print(f"Successfully converted files to HTML.")
                html_pattern = os.path.join(psi4_working_dir, "psi4.mode*.html")
                html_files = glob.glob(html_pattern)
                def natural_key(text):
                    return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]
                html_files.sort(key=natural_key)
                if not html_files:
                    QMessageBox.warning(self, "Warning", "XYZ files found but no HTML files were generated.")
                    return
                self.vib_dialog = VibLogicDialog(self, html_files=html_files)
                self.vib_dialog.show()
            except Exception as e:
                QMessageBox.warning(self, "HTML Conversion Error", f"Failed to generate or load HTML files:\n{str(e)}")
    def on_select_all_toggled(self, checked):
        self.lineEdit_bonds.setDisabled(checked)
        self.lineEdit_angles.setDisabled(checked)
    def run_process_user_params(self):
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        forcefield_dir = os.path.join(project_base, project_name, "forcefield")
        input_file = os.path.join(forcefield_dir, "ligand.itp")
        output_file = os.path.join(forcefield_dir, "ligand_fb_user.itp")
        bonds_text = self.lineEdit_bonds.text().strip()
        angles_text = self.lineEdit_angles.text().strip()
        if not bonds_text and not angles_text:
            return True
        success, msg, missing_bonds, missing_angles = process_user_params.generate_user_defined_itp(
            input_file, output_file, bonds_text, angles_text
        )
        if not success:
            QMessageBox.critical(self, "Error", f"Failed to process ITP file:\n{msg}")
            return False
        if missing_bonds or missing_angles:
            error_msg = "The following items were NOT found in ligand.itp:\n\n"
            if missing_bonds:
                error_msg += f"Bonds: {', '.join(missing_bonds)}\n"
            if missing_angles:
                error_msg += f"Angles: {', '.join(missing_angles)}\n"
            error_msg += "\nPlease check your ITP file."
            QMessageBox.warning(self, "Missing Atoms", error_msg)
            return False
        else:
            print(f"User ITP generated successfully: {output_file}")
            return True
    def run_remove_frequency(self):
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        if not project_base or not project_name:
            QMessageBox.warning(self, "Warning", "Please select Project Folder and Name first.")
            return False
        targets_ligand_vib_dir = os.path.join(project_base, project_name, "targets", "ligand_vib")
        input_file = os.path.join(targets_ligand_vib_dir, "vdata_start.txt")
        output_file = os.path.join(targets_ligand_vib_dir, "vdata.txt")
        remove_str = self.lineEdit_remove_frequency.text().strip()
        success, msg = remove_vib_modes.process_removal(input_file, output_file, remove_str)
        if success:
            print(f"Generated: {output_file}")
            return True
        else:
            QMessageBox.critical(self, "Error", msg)
            return False
    def run_extract_opt_geo(self):
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        psi4_working_dir = os.path.join(project_base, project_name, "psi4_working")
        psi4_out_path = os.path.join(psi4_working_dir, "psi4.out")
        target_geo_dir = os.path.join(project_base, project_name, "targets", "ligand_optgeo")
        xyz_out_path = os.path.join(target_geo_dir, "ligand.xyz")
        pdb_out_path = os.path.join(target_geo_dir, "ligand_optget.pdb")
        if not os.path.exists(psi4_out_path):
            print(f"Error: {psi4_out_path} not found. Skip geometry extraction.")
            return False
        coords = []
        try:
            with open(psi4_out_path, 'r') as f:
                lines = f.readlines()
            start_index = -1
            for i, line in enumerate(lines):
                if "Geometry (in Angstrom)" in line:
                    start_index = i
            if start_index != -1:
                current_idx = start_index + 1
                while current_idx < len(lines):
                    line = lines[current_idx].strip()
                    current_idx += 1
                    if not line: continue
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            symbol = parts[0]
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            coords.append((symbol, x, y, z))
                        except ValueError:
                            if len(coords) > 0: break
                            continue
                    elif len(coords) > 0:
                        break
            if not coords:
                print("Error: No coordinates extracted for XYZ.")
                return False
            with open(xyz_out_path, 'w') as f:
                f.write(f"{len(coords)}\n")
                f.write("Optimized geometry from Psi4\n")
                for atom in coords:
                    f.write(f"{atom[0]:<5} {atom[1]:12.6f} {atom[2]:12.6f} {atom[3]:12.6f}\n")
            print(f"Generated: {xyz_out_path}")
        except Exception as e:
            print(f"Failed to extract XYZ: {e}")
            return False
        print("Running obabel conversion...")
        babel_process = QProcess()
        program = "obabel"
        arguments = [xyz_out_path, "-O", pdb_out_path]
        babel_process.start(program, arguments)
        if not babel_process.waitForFinished(10000):
            print("Error: obabel conversion timed out.")
            return False
        if babel_process.exitCode() == 0:
            print(f"Successfully generated: {pdb_out_path}")
            try:
                with open(pdb_out_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                cryst_line = "CRYST1    0.000    0.000    0.000  90.00  90.00  90.00 P 1           1\n"
                if len(lines) >= 2:
                    lines.insert(2, cryst_line)
                else:
                    lines.append(cryst_line)
                with open(pdb_out_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"CRYST1 info inserted into the 3rd line of {pdb_out_path}")
                return True
            except Exception as e:
                print(f"Failed to insert CRYST1 line: {str(e)}")
                return False
        else:
            err = babel_process.readAllStandardError().data().decode()
            print(f"obabel failed: {err}")
            return False
    def generate_optgeo_options(self):
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        template_path = os.path.join(os.getcwd(), "temp", "temp.optgeo_options.txt")
        target_dir = os.path.join(project_base, project_name, "targets", "ligand_optgeo")
        output_path = os.path.join(target_dir, "optgeo_options.txt")
        if not os.path.exists(template_path):
            print(f"Error: Template not found at {template_path}")
            return False
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.replace("{bond_denom}", self.denom_bond)
            content = content.replace("{angle_denom}", self.denom_angle)
            content = content.replace("{dihedral_denom}", self.denom_dihedral)
            content = content.replace("{improper_denom}", self.denom_improper)
            os.makedirs(target_dir, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully generated: {output_path}")
            return True
        except Exception as e:
            print(f"Failed to generate optgeo_options.txt: {str(e)}")
            return False
    def run_full_workflow(self):
        print("Starting workflow...")
        if not self.run_process_user_params():
            print("Workflow stopped at User Params step.")
            return
        if not self.run_remove_frequency():
            print("Workflow stopped at Remove Frequency step.")
            return
        if not self.run_extract_opt_geo():
            print("Workflow stopped at convert optgeo_pdb step")
            return
        if not self.generate_optgeo_options():
            print("Workflow stopped at generate optgeo_options step")
        self.run_fb_vib()
    def run_fb_vib(self):
        project_base = self.lineEdit_project_folder.text().strip()
        project_name = self.lineEdit_project_name.text().strip()
        if not project_base or not project_name:
            print("Please create project folder first")
            return
        project_full_path = os.path.join(project_base, project_name)
        output_path = os.path.join(project_full_path, "vib.in")
        if self.checkBox_select_all.isChecked():
            val_forcefield = "ligand_fb.itp"
        else:
            val_forcefield = "ligand_fb_user.itp"
        fb_params = {
            "forcefield": val_forcefield,
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
            "weight": self.lineEdit_weight.text().strip(),
            "reassign_modes": self.comboBox_reassign_modes.currentText().strip(),
            "wavenumber_tol": self.lineEdit_wavenumber.text().strip()
        }
        try:
            generate_fb_vib(output_path, **fb_params)
            print(f"Success! Fb config generated:\n{output_path}")
            print(f"Used forcefield file: {val_forcefield}")
            self.vib_handler = VibOutputHandler(project_full_path)
            self.run_forcebalance_exec(project_full_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate config:\n{str(e)}")
    def run_forcebalance_exec(self, working_dir):
        self.fb_log_cache = ""
        command = "ForceBalance.py"
        args = ["vib.in"]
        print(f"Starting ForceBalance in: {working_dir}")
        self.fb_process.setWorkingDirectory(working_dir)
        self.fb_process.start(command, args)
        self.progress_dialog = QProgressDialog("Running ForceBalance... This may take a while.", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("ForceBalance Status")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.kill_fb_process)
        self.progress_dialog.show()
    def kill_fb_process(self):
        if self.fb_process.state() == QProcess.Running:
            self.fb_process.kill()
            print("ForceBalance process killed by user.")
    def on_fb_output(self):
        data = self.fb_process.readAllStandardOutput()
        stderr = self.fb_process.readAllStandardError()
        if data:
            text = data.data().decode('utf-8', errors='ignore')
            print(text.strip())
            self.fb_log_cache += text
            if self.vib_handler:
                self.vib_handler.parse_and_save(self.fb_log_cache)
        if stderr:
            text_err = stderr.data().decode('utf-8', errors='ignore')
            print("FB_ERR:", text_err.strip())
    def on_fb_finished(self, exit_code, exit_status):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        error_keywords = ["Traceback", "Error:", "CRITICAL", "exiting due to exception"]
        if exit_status == QProcess.NormalExit and exit_code == 0:
            found_error = False
            for kw in error_keywords:
                if kw in self.fb_log_cache:
                    found_error = True
                    break
            if found_error:
                QMessageBox.critical(self, "Error",
                    "ForceBalance has errors.\n\n"
                    "Please check the console output for 'Error'.")
            else:
                QMessageBox.information(self, "Success", "ForceBalance finished successfully!")
        elif exit_status == QProcess.CrashExit:
            print("ForceBalance process crashed or killed.")
        else:
            QMessageBox.critical(self, "Error", f"ForceBalance failed with exit code: {exit_code}")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindowLogic()
    main_window.show()
    sys.exit(app.exec_())
