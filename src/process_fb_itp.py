import re
import argparse
import os
import sys
def remove_comment(line):
    return line.split(';')[0].strip()
def process_itp(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: 文件 '{input_path}' 不存在。")
        sys.exit(1)
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    has_bondtypes = '[ bondtypes ]' in content or '[bondtypes]' in content
    has_angletypes = '[ angletypes ]' in content or '[angletypes]' in content
    current_section = None
    processed_lines = []
    molecule_name = "UNKNOWN"
    atom_dict = {}
    bond_type_to_ref_indices = {}
    angle_type_to_ref_indices = {}
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        stripped = line.strip()
        original_line = line.rstrip('\n')
        header_match = re.match(r'^\s*\[\s*(\w+)\s*\]', stripped)
        if header_match:
            current_section = header_match.group(1).lower()
            processed_lines.append(line)
            continue
        if not stripped or stripped.startswith(';'):
            processed_lines.append(line)
            continue
        data_part = remove_comment(stripped)
        cols = data_part.split()
        suffix = ""
        if current_section == "moleculetype":
            if len(cols) >= 1 and molecule_name == "UNKNOWN":
                molecule_name = cols[0]
        elif current_section == "atoms":
            if len(cols) >= 2:
                atom_dict[cols[0]] = cols[1]
        elif current_section == "bondtypes" and has_bondtypes:
            if "; PARM" not in original_line:
                suffix = " ; PARM 3 4"
        elif current_section == "angletypes" and has_angletypes:
            if "; PARM" not in original_line:
                suffix = " ; PARM 4 5"
        elif current_section == "bonds" and not has_bondtypes:
            if len(cols) >= 2:
                id_i, id_j = cols[0], cols[1]
                if id_i in atom_dict and id_j in atom_dict:
                    t_i, t_j = atom_dict[id_i], atom_dict[id_j]
                    type_key = tuple(sorted((t_i, t_j)))
                    if type_key not in bond_type_to_ref_indices:
                        suffix = " ; PARM 3 4"
                        bond_type_to_ref_indices[type_key] = f"{id_i}.{id_j}"
                    else:
                        ref = bond_type_to_ref_indices[type_key]
                        suffix = f" ; RPT 3 BONDSB:{molecule_name}-{ref} 4 BONDSK:{molecule_name}-{ref} /RPT"
        elif current_section == "angles" and not has_angletypes:
            if len(cols) >= 3:
                id_i, id_j, id_k = cols[0], cols[1], cols[2]
                if id_i in atom_dict and id_j in atom_dict and id_k in atom_dict:
                    t_i, t_j, t_k = atom_dict[id_i], atom_dict[id_j], atom_dict[id_k]
                    type_key = (t_i, t_j, t_k) if t_i < t_k else (t_k, t_j, t_i)
                    if type_key not in angle_type_to_ref_indices:
                        suffix = " ; PARM 4 5"
                        angle_type_to_ref_indices[type_key] = f"{id_i}.{id_j}.{id_k}"
                    else:
                        ref = angle_type_to_ref_indices[type_key]
                        suffix = f" ; RPT 4 ANGLESB:{molecule_name}-{ref} 5 ANGLESK:{molecule_name}-{ref} /RPT"
        if "; PARM" in original_line or "; RPT" in original_line:
            processed_lines.append(original_line + '\n')
        else:
            processed_lines.append(original_line + suffix + '\n')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)
    print(f"处理成功！输出文件: {output_path}")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    out = args.output if args.output else os.path.splitext(args.input_file)[0] + "_mod.itp"
    process_itp(args.input_file, out)
