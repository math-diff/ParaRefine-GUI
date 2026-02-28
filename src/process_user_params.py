import os
def detect_style_and_parse(input_str, expected_parts):
    if not input_str:
        return [], 'dot'
    if '-' in input_str:
        sep = '-'
        style = 'dash'
    elif ',' in input_str:
        sep = ','
        style = 'comma'
    else:
        sep = '.'
        style = 'dot'
    targets = []
    groups = input_str.split(';')
    for group in groups:
        group = group.strip()
        if not group:
            continue
        parts = [p.strip() for p in group.split(sep)]
        if len(parts) == expected_parts:
            targets.append(tuple(parts))
    return targets, style
def match_atoms(line_parts, target_tuple):
    if len(line_parts) < len(target_tuple):
        return False
    current_atoms = tuple(line_parts[:len(target_tuple)])
    return current_atoms == target_tuple or current_atoms == target_tuple[::-1]
def generate_user_defined_itp(input_path, output_path, bonds_input, angles_input):
    target_bonds, bond_style = detect_style_and_parse(bonds_input, 2)
    target_angles, angle_style = detect_style_and_parse(angles_input, 3)
    if bond_style == 'dash':
        b_parm = "3 4"
        def b_rpt(m, r): return f"3 BONDSB:{m}-{r} 4 BONDSK:{m}-{r}"
    elif bond_style == 'comma':
        b_parm = "3"
        def b_rpt(m, r): return f"3 BONDSB:{m}-{r}"
    else:
        b_parm = "4"
        def b_rpt(m, r): return f"4 BONDSK:{m}-{r}"
    if angle_style == 'dash':
        a_parm = "4 5"
        def a_rpt(m, r): return f"4 ANGLESB:{m}-{r} 5 ANGLESK:{m}-{r}"
    elif angle_style == 'comma':
        a_parm = "4"
        def a_rpt(m, r): return f"4 ANGLESB:{m}-{r}"
    else:
        a_parm = "5"
        def a_rpt(m, r): return f"5 ANGLESK:{m}-{r}"
    found_bonds = set()
    found_angles = set()
    if not os.path.exists(input_path):
        return False, "Input file not found", [], []
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    molecule_name = "UNKNOWN"
    atom_dict = {}
    bond_type_to_ref = {}
    angle_type_to_ref = {}
    new_lines = []
    current_section = None
    for line in lines:
        stripped = line.strip()
        original_line = line.rstrip('\n')
        final_line = original_line
        if stripped.startswith('[') and stripped.endswith(']'):
            current_section = stripped[1:-1].strip().lower()
            new_lines.append(line)
            continue
        if not stripped or stripped.startswith(';'):
            new_lines.append(line)
            continue
        data_part = stripped.split(';')[0].strip()
        cols = data_part.split()
        if current_section == "moleculetype":
            if len(cols) >= 1 and molecule_name == "UNKNOWN":
                molecule_name = cols[0]
        elif current_section == "atoms":
            if len(cols) >= 2:
                atom_dict[cols[0]] = cols[1]
        elif current_section == "bonds":
            if len(cols) >= 2:
                is_target = False
                for b_tup in target_bonds:
                    if match_atoms(cols, b_tup):
                        found_bonds.add(b_tup)
                        is_target = True
                        break
                if is_target:
                    id_i, id_j = cols[0], cols[1]
                    if id_i in atom_dict and id_j in atom_dict:
                        type_key = tuple(sorted((atom_dict[id_i], atom_dict[id_j])))
                        if type_key not in bond_type_to_ref:
                            if "; PARM" not in final_line and "; RPT" not in final_line:
                                final_line += f" ; PARM {b_parm}"
                            bond_type_to_ref[type_key] = f"{id_i}.{id_j}"
                        else:
                            ref = bond_type_to_ref[type_key]
                            if "; PARM" not in final_line and "; RPT" not in final_line:
                                final_line += f" ; RPT {b_rpt(molecule_name, ref)} /RPT"
                    else:
                        if "; PARM" not in final_line: final_line += f" ; PARM {b_parm}"
        elif current_section == "angles":
            if len(cols) >= 3:
                is_target = False
                for a_tup in target_angles:
                    if match_atoms(cols, a_tup):
                        found_angles.add(a_tup)
                        is_target = True
                        break
                if is_target:
                    id_i, id_j, id_k = cols[0], cols[1], cols[2]
                    if id_i in atom_dict and id_j in atom_dict and id_k in atom_dict:
                        t_i, t_j, t_k = atom_dict[id_i], atom_dict[id_j], atom_dict[id_k]
                        type_key = (t_i, t_j, t_k) if t_i < t_k else (t_k, t_j, t_i)
                        if type_key not in angle_type_to_ref:
                            if "; PARM" not in final_line and "; RPT" not in final_line:
                                final_line += f" ; PARM {a_parm}"
                            angle_type_to_ref[type_key] = f"{id_i}.{id_j}.{id_k}"
                        else:
                            ref = angle_type_to_ref[type_key]
                            if "; PARM" not in final_line and "; RPT" not in final_line:
                                final_line += f" ; RPT {a_rpt(molecule_name, ref)} /RPT"
                    else:
                        if "; PARM" not in final_line: final_line += f" ; PARM {a_parm}"
        new_lines.append(final_line + '\n')
    b_sep = '-' if bond_style=='dash' else (',' if bond_style=='comma' else '.')
    a_sep = '-' if angle_style=='dash' else (',' if angle_style=='comma' else '.')
    missing_bonds = [f"{b[0]}{b_sep}{b[1]}" for b in target_bonds if b not in found_bonds]
    missing_angles = [f"{a_sep.join(a)}" for a in target_angles if a not in found_angles]
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True, "Success", missing_bonds, missing_angles
    except Exception as e:
        return False, str(e), [], []
