import os
import re
class FBOutputHandler:
    def __init__(self, project_path):
        self.output_base = os.path.join(project_path, "dih.tmp", "ligand_dih")
        self.history_data = []
    def strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    def parse_and_save(self, full_text):
        clean_text = self.strip_ansi(full_text)
        iter_matches = re.findall(r"Iteration\s+(\d+):", clean_text)
        if not iter_matches:
            return
        current_iter_num = int(iter_matches[-1])
        iter_dir = os.path.join(self.output_base, f"iter_{current_iter_num:04d}")
        if not os.path.exists(iter_dir):
            os.makedirs(iter_dir, exist_ok=True)
        float_pattern = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
        target_score = 0.0
        reg_score = 0.0
        total_score = 0.0
        total_gradient = 0.0
        target_regex = fr"ligand_dih\s+\S+\s+\S+\s+({float_pattern})"
        target_matches = re.findall(target_regex, clean_text)
        if target_matches:
            target_score = float(target_matches[-1])
        reg_regex = fr"Regularization\s+\S+\s+\S+\s+({float_pattern})"
        reg_matches = re.findall(reg_regex, clean_text)
        if reg_matches:
            reg_score = float(reg_matches[-1])
        total_regex = fr"Total\s+({float_pattern})"
        total_matches = re.findall(total_regex, clean_text)
        if total_matches:
            total_score = float(total_matches[-1])
        grad_regex = fr"^\s*\d+\s+\S+\s+\S+\s+({float_pattern})"
        grad_matches = re.findall(grad_regex, clean_text, re.MULTILINE)
        if grad_matches:
            total_gradient = float(grad_matches[-1])
        current_data = [current_iter_num, target_score, reg_score, total_score, total_gradient]
        exists = False
        for i, h in enumerate(self.history_data):
            if h[0] == current_iter_num:
                self.history_data[i] = current_data
                exists = True
                break
        if not exists:
            self.history_data.append(current_data)
            self.history_data.sort(key=lambda x: x[0])
        score_file_name = f"score-{current_iter_num:04d}.data"
        score_file_path = os.path.join(iter_dir, score_file_name)
        try:
            with open(score_file_path, 'w', encoding='utf-8') as f:
                f.write(f"{'Iteration':<12} {'Target':<15} {'Regularization':<15} {'Total':<15} {'Gradient':<15}\n")
                f.write("-" * 75 + "\n")
                for row in self.history_data:
                    f.write(f"{row[0]:<12d} {row[1]:<15.5e} {row[2]:<15.5e} {row[3]:<15.5e} {row[4]:<15.5e}\n")
        except Exception as e:
            print(f"Error writing score file: {e}")
        gradient_sections = clean_text.split("Total Gradient")
        if len(gradient_sections) > 1:
            last_section = gradient_sections[-1]
            lines = last_section.splitlines()
            grad_details = []
            detail_pattern = re.compile(fr"^\s*\d+\s+\[\s*({float_pattern})\s*\]\s*:\s*(.+)$")
            for line in lines:
                line = line.strip()
                if "-----" in line:
                    if grad_details:
                        break
                    else:
                        continue
                match = detail_pattern.match(line)
                if match:
                    val_str = match.group(1)
                    label_str = match.group(2).strip()
                    grad_details.append((val_str, label_str))
            if grad_details:
                grad_file_name = f"grad-{current_iter_num:04d}.data"
                grad_file_path = os.path.join(iter_dir, grad_file_name)
                try:
                    with open(grad_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"{'Gradient Value':<20} {'Parameter Label'}\n")
                        f.write("-" * 50 + "\n")
                        for val, label in grad_details:
                            f.write(f"{val:<20} {label}\n")
                except Exception as e:
                    print(f"Error writing grad file: {e}")
        return score_file_path
class LJOutputHandler:
    def __init__(self, project_path):
        self.output_base = os.path.join(project_path, "lj.tmp", "ligand_liquid")
        self.history_phys = []
        self.history_scores = []
        self.current_iter_dir_name = None
    def strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    def parse_and_save(self, full_text):
        clean_text = self.strip_ansi(full_text)
        dir_matches = re.findall(r"ligand_liquid/(iter_\d+)/", clean_text)
        if dir_matches:
            self.current_iter_dir_name = dir_matches[-1]
        if not self.current_iter_dir_name:
            return
        current_num = int(self.current_iter_dir_name.replace("iter_", ""))
        search_start = clean_text.rfind("ligand_liquid Density (kg m^-3)")
        if search_start == -1: return
        current_content = clean_text[search_start:]
        f = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
        d_match = re.search(fr"Density \(kg m\^-3\).*?atm\s+({f})\s+({f})\s+\+-\s+{f}\s+({f})", current_content, re.DOTALL)
        h_match = re.search(fr"Enthalpy of Vaporization \(kJ mol\^-1\).*?atm\s+({f})\s+({f})\s+\+-\s+{f}\s+({f})", current_content, re.DOTALL)
        d_obj_m = re.search(fr"Density\s+({f})\s+{f}\s+{f}", current_content)
        h_obj_m = re.search(fr"Enthalpy of Vaporization\s+({f})\s+{f}\s+{f}", current_content)
        ll_match = re.search(fr"ligand_liquid\s+({f})\s+{f}\s+{f}", current_content)
        reg_match = re.search(fr"Regularization\s+({f})\s+{f}\s+{f}", current_content)
        total_m = re.search(fr"Objective Function Breakdown.*?Total\s+({f})", current_content, re.DOTALL)
        if d_match and h_match and total_m:
            grad_val = 0.0
            step_m = re.findall(fr"^\s*(\d+)\s+{f}\s+{f}\s+({f})\s+{f}", clean_text, re.MULTILINE)
            if step_m:
                grad_val = float(step_m[-1][1])
            self._update_history(self.history_phys, [
                current_num,
                float(d_match.group(1)), float(d_match.group(2)), float(d_match.group(3)),
                float(h_match.group(1)), float(h_match.group(2)), float(h_match.group(3))
            ])
            self._update_history(self.history_scores, [
                current_num,
                float(d_obj_m.group(1)) if d_obj_m else 0.0,
                float(h_obj_m.group(1)) if h_obj_m else 0.0,
                float(ll_match.group(1)) if ll_match else 0.0,
                float(reg_match.group(1)) if reg_match else 0.0,
                float(total_m.group(1)),
                grad_val
            ])
            iter_dir = os.path.join(self.output_base, self.current_iter_dir_name)
            os.makedirs(iter_dir, exist_ok=True)
            self._write_phys_file(current_num, iter_dir)
            self._write_score_file(current_num, iter_dir)
            self._save_gradient_details(current_content, current_num, iter_dir)
            return os.path.join(iter_dir, f"score-{current_num:04d}.data")
        return None
    def _update_history(self, history_list, data):
        for i, row in enumerate(history_list):
            if row[0] == data[0]:
                history_list[i] = data
                return
        history_list.append(data)
        history_list.sort(key=lambda x: x[0])
    def _write_phys_file(self, num, iter_dir):
        path = os.path.join(iter_dir, f"density-hvap-{num:04d}.data")
        header = f"{'Iter':<6} {'Dens_Ref':<12} {'Dens_Calc':<12} {'Dens_Delta':<10} {'Hvap_Ref':<12} {'Hvap_Calc':<12} {'Hvap_Delta':<10}\n"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(header + "-"*85 + "\n")
            for r in self.history_phys:
                f.write(f"{r[0]:<6d} {r[1]:<12.3f} {r[2]:<12.3f} {r[3]:<10.3f} {r[4]:<12.3f} {r[5]:<12.3f} {r[6]:<10.3f}\n")
    def _write_score_file(self, num, iter_dir):
        path = os.path.join(iter_dir, f"score-{num:04d}.data")
        header = f"{'Iter':<6} {'Dens_Obj':<12} {'Hvap_Obj':<12} {'LiqLiq':<12} {'Reg':<10} {'Total':<12} {'Grad':<12}\n"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(header + "-"*85 + "\n")
            for r in self.history_scores:
                f.write(f"{r[0]:<6d} {r[1]:<12.4e} {r[2]:<12.4e} {r[3]:<12.4e} {r[4]:<10.4e} {r[5]:<12.4e} {r[6]:<12.4e}\n")
    def _save_gradient_details(self, current_content, num, iter_dir):
        grad_sections = current_content.split("Total Gradient")
        if len(grad_sections) > 1:
            lines = grad_sections[-1].splitlines()
            grad_details = []
            p = re.compile(r"^\s*\d+\s+\[\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\]\s*:\s*(.+)$")
            for line in lines:
                if "-----" in line and grad_details: break
                match = p.match(line)
                if match: grad_details.append((match.group(1), match.group(2).strip()))
            if grad_details:
                with open(os.path.join(iter_dir, f"grad-{num:04d}.data"), 'w', encoding='utf-8') as f:
                    f.write(f"{'Gradient Value':<20} {'Parameter Label'}\n" + "-"*50 + "\n")
                    for v, l in grad_details: f.write(f"{v:<20} {l}\n")
import os
import re
class VibOutputHandler:
    def __init__(self, project_full_path):
        self.output_base = project_full_path
        self.history_scores = []
        self.history_rmsd = []
    def strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    def parse_and_save(self, full_text):
        clean_text = self.strip_ansi(full_text)
        iter_headers = list(re.finditer(r"Iteration\s+(\d+):", clean_text))
        if not iter_headers:
            return
        last_match = iter_headers[-1]
        curr_iter = int(last_match.group(1))
        current_block = clean_text[last_match.start():]
        f_pat = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
        if "ligand_optgeo" in current_block and "RMSD   denom" in current_block:
            parts = current_block.split("RMSD   denom")
            if len(parts) > 1:
                table_content = parts[-1].split("-----------------")[0]
                rmsd_re = fr"^\s*([a-zA-Z_]+[a-zA-Z0-9_\-]*)\s+({f_pat})\s+({f_pat})\s+({f_pat})\s+({f_pat})\s+({f_pat})\s+({f_pat})\s+({f_pat})\s+({f_pat})\s+({f_pat})"
                match = re.search(rmsd_re, table_content, re.MULTILINE)
                if match:
                    rmsd_file = os.path.join(self.output_base, f"rmsd-{curr_iter:04d}.data")
                    with open(rmsd_file, 'w', encoding='utf-8') as f:
                        f.write(f"{'System':<15} {match.group(1)}\n")
                        f.write("-" * 45 + "\n")
                        f.write(f"{'Type':<15} {'RMSD':<12} {'Denom':<12}\n")
                        f.write(f"{'Bonds':<15} {match.group(2):<12} {match.group(3):<12}\n")
                        f.write(f"{'Angles':<15} {match.group(4):<12} {match.group(5):<12}\n")
                        f.write(f"{'Dihedrals':<15} {match.group(6):<12} {match.group(7):<12}\n")
                        f.write(f"{'Impropers':<15} {match.group(8):<12} {match.group(9):<12}\n")
                    self._update_rmsd_history([curr_iter, match.group(2), match.group(4), match.group(6), match.group(8)])
                    history_file = os.path.join(self.output_base, "rmsd-history.data")
                    with open(history_file, 'w', encoding='utf-8') as f:
                        f.write(f"{'Iter':<6} {'Bonds':<12} {'Angles':<12} {'Dihedrals':<12} {'Impropers':<12}\n")
                        f.write("-" * 60 + "\n")
                        for row in self.history_rmsd:
                            f.write(f"{row[0]:<6d} {row[1]:<12} {row[2]:<12} {row[3]:<12} {row[4]:<12}\n")
        if "Frequencies (wavenumbers)" in current_block:
            sections = current_block.split("Frequencies (wavenumbers)")
            vib_body = sections[-1].split("----------------------------------------------------------------------------")[0]
            vib_rows = re.findall(fr"^\s*(\d+)\s+({f_pat})\s+({f_pat})\s+({f_pat})\s+({f_pat})", vib_body, re.MULTILINE)
            if vib_rows:
                vib_file = os.path.join(self.output_base, f"vib-{curr_iter:04d}.data")
                with open(vib_file, 'w', encoding='utf-8') as f:
                    f.write(f"{'Mode':<8} {'Reference':<15} {'Calculated':<15} {'Difference':<15} {'Ref(dot)Calc':<12}\n")
                    f.write("-" * 75 + "\n")
                    for r in vib_rows:
                        f.write(f"{r[0]:<8} {r[1]:<15} {r[2]:<15} {r[3]:<15} {r[4]:<12}\n")
        opt_find = re.findall(fr"ligand_optgeo\s+{f_pat}\s+{f_pat}\s+({f_pat})", current_block)
        vib_find = re.findall(fr"ligand_vib\s+{f_pat}\s+{f_pat}\s+({f_pat})", current_block)
        reg_find = re.findall(fr"Regularization\s+{f_pat}\s+{f_pat}\s+({f_pat})", current_block)
        tot_find = re.findall(fr"Total\s+({f_pat})", current_block)
        grad_find = re.findall(fr"^\s*{curr_iter}\s+{f_pat}\s+{f_pat}\s+({f_pat})", current_block, re.MULTILINE)
        if tot_find:
            s_opt = opt_find[-1] if opt_find else "0.0"
            s_vib = vib_find[-1] if vib_find else "0.0"
            s_reg = reg_find[-1] if reg_find else "0.0"
            s_tot = tot_find[-1]
            s_grad = grad_find[-1] if grad_find else "N/A"
            self._update_score_history([curr_iter, s_opt, s_vib, s_reg, s_tot, s_grad])
            score_file = os.path.join(self.output_base, f"score-{curr_iter:04d}.data")
            with open(score_file, 'w', encoding='utf-8') as f:
                f.write(f"{'Iter':<6} {'ligand_optgeo':<18} {'ligand_vib':<18} {'Regularization':<18} {'Total':<18} {'|grad|':<15}\n")
                f.write("-" * 105 + "\n")
                for r in self.history_scores:
                    f.write(f"{r[0]:<6d} {r[1]:<18} {r[2]:<18} {r[3]:<18} {r[4]:<18} {r[5]:<15}\n")
        if "Total Gradient" in current_block:
            grad_parts = current_block.split("Total Gradient")
            detail_p = re.compile(fr"^\s*(\d+)\s+\[\s*({f_pat})\s*\]\s*:\s*(.+)$")
            grad_res = []
            for line in grad_parts[-1].splitlines():
                if "----" in line and grad_res: break
                m = detail_p.match(line)
                if m: grad_res.append((m.group(2), m.group(3).strip()))
            if grad_res:
                grad_file = os.path.join(self.output_base, f"grad-{curr_iter:04d}.data")
                with open(grad_file, 'w', encoding='utf-8') as f:
                    f.write(f"{'Value':<20} {'Parameter Label'}\n")
                    f.write("-" * 60 + "\n")
                    for v_val, l_lab in grad_res:
                        f.write(f"{v_val:<20} {l_lab}\n")
    def _update_rmsd_history(self, new_row):
        for i, row in enumerate(self.history_rmsd):
            if row[0] == new_row[0]:
                self.history_rmsd[i] = new_row
                return
        self.history_rmsd.append(new_row)
        self.history_rmsd.sort(key=lambda x: x[0])
    def _update_score_history(self, new_row):
        for i, row in enumerate(self.history_scores):
            if row[0] == new_row[0]:
                self.history_scores[i] = new_row
                return
        self.history_scores.append(new_row)
        self.history_scores.sort(key=lambda x: x[0])
