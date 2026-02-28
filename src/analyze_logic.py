import os, re
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QScrollArea, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import plot_score, plot_grad, plot_rmsd
import plot_vib, plot_dih_energy
import plot_den_hvap
class AnalyzeLogic:
    def select_analyze_score_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "./",
            "data Files (*.data);;All Files (*)"
        )
        if file_path:
            self.lineEdit_Score.setText(file_path)
    def select_analyze_grad_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "./",
            "data Files (*.data);;All Files (*)"
        )
        if file_path:
            self.lineEdit_Grad.setText(file_path)
    def select_analyze_rmsd_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "./",
            "data Files (*.data);;All Files (*)"
        )
        if file_path:
            self.lineEdit_rmsd.setText(file_path)
    def select_analyze_vib_mode_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "./",
            "data Files (*.data);;All Files (*)"
        )
        if file_path:
            self.lineEdit_vibration_mode.setText(file_path)
    def select_analyze_energy_diff_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "./",
            "txt Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.lineEdit_energy_difference.setText(file_path)
    def select_analyze_density_hvap_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "./",
            "data Files (*.data);;All Files (*)"
        )
        if file_path:
            self.lineEdit_density_hvap.setText(file_path)
    def run_plot(self):
        score_path = self.lineEdit_Score.text().strip()
        grad_path = self.lineEdit_Grad.text().strip()
        rmsd_path = self.lineEdit_rmsd.text().strip()
        vib_path = self.lineEdit_vibration_mode.text().strip()
        energy_diff_path = self.lineEdit_energy_difference.text().strip()
        density_hvap_path = self.lineEdit_density_hvap.text().strip()
        if not any([score_path, grad_path, rmsd_path, vib_path, energy_diff_path, density_hvap_path]):
            QMessageBox.warning(self, "Warning", "Please select at least one file path.")
            return
        if score_path and os.path.exists(score_path):
            try:
                print(f"Plotting Score: {score_path}")
                plot_score.plot_and_save(score_path)
            except Exception as e:
                QMessageBox.critical(self, "Score Plot Error", str(e))
        if grad_path and os.path.exists(grad_path):
            try:
                print(f"Plotting Grad: {grad_path}")
                plot_grad.plot_gradient(grad_path)
            except Exception as e:
                QMessageBox.critical(self, "Grad Plot Error", str(e))
        if rmsd_path and os.path.exists(rmsd_path):
            try:
                data_dir = os.path.dirname(rmsd_path)
                save_path = os.path.join(data_dir, 'bond_angle_rmsd.png')
                print(f"Plotting RMSD: {rmsd_path}")
                plot_rmsd.plot_molecular_data(rmsd_path, output_filename=save_path)
                print(f"RMSD plot saved to: {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "RMSD Plot Error", f"Failed to plot RMSD:\n{str(e)}")
        if vib_path and os.path.exists(vib_path):
            try:
                data_dir = os.path.dirname(vib_path)
                basename = os.path.basename(vib_path)
                match = re.search(r'(\d+)', basename)
                if match:
                    index = match.group(1)
                    save_name = f"vib-difference-{index}.png"
                else:
                    save_name = "vib-difference.png"
                save_path = os.path.join(data_dir, save_name)
                print(f"Plotting Vibration: {vib_path}")
                print(f"Saving to: {save_path}")
                plot_vib.plot_difference_bar(vib_path, save_path)
            except Exception as e:
                QMessageBox.critical(self, "Vib Plot Error", f"Failed to plot Vibration:\n{str(e)}")
        if energy_diff_path and os.path.exists(energy_diff_path):
            try:
                data_dir = os.path.dirname(energy_diff_path)
                save_path = os.path.join(data_dir, 'dih_energy.png')
                print(f"Plotting Energy Difference: {energy_diff_path}")
                print(f"Saving to: {save_path}")
                plot_dih_energy.plot_energy(energy_diff_path, save_path)
            except Exception as e:
                QMessageBox.critical(self, "Energy Plot Error", f"Failed to plot Energy Difference:\n{str(e)}")
        if density_hvap_path and os.path.exists(density_hvap_path):
            try:
                print(f"Plotting Density & Hvap: {density_hvap_path}")
                data_dir = os.path.dirname(density_hvap_path)
                save_path = os.path.join(data_dir, 'density_hvap.png')
                print(f"Saving to: {save_path}")
                plot_den_hvap.plot_data(density_hvap_path, output_filename=save_path)
            except Exception as e:
                QMessageBox.critical(self, "Density Plot Error", f"Failed to plot Density & Hvap:\n{str(e)}")
