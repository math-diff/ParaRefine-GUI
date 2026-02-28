import os
def save_lj_itp(itp_file_path, output_file_path, sigma_input_str, epsilon_input_str):
    if not os.path.exists(itp_file_path):
        return False, f"File not found: {itp_file_path}"
    try:
        with open(itp_file_path, 'r') as f:
            lines = f.readlines()
        atom_id_to_type = {}
        in_atoms_section = False
        for line in lines:
            clean_line = line.strip()
            if clean_line.startswith('[') and clean_line.endswith(']'):
                section_name = clean_line[1:-1].strip()
                if section_name == 'atoms':
                    in_atoms_section = True
                else:
                    in_atoms_section = False
                continue
            if in_atoms_section and clean_line and not clean_line.startswith(';'):
                parts = clean_line.split()
                if len(parts) >= 2:
                    atom_id = parts[0]
                    atom_type = parts[1]
                    atom_id_to_type[atom_id] = atom_type
        def parse_input(input_str):
            if not input_str:
                return set()
            return set(x.strip() for x in input_str.split(';') if x.strip())
        sigma_ids = parse_input(sigma_input_str)
        epsilon_ids = parse_input(epsilon_input_str)
        sigma_types = set(atom_id_to_type[aid] for aid in sigma_ids if aid in atom_id_to_type)
        epsilon_types = set(atom_id_to_type[aid] for aid in epsilon_ids if aid in atom_id_to_type)
        new_lines = []
        in_atomtypes_section = False
        for line in lines:
            clean_line = line.strip()
            if clean_line.startswith('[') and clean_line.endswith(']'):
                section_name = clean_line[1:-1].strip()
                if section_name == 'atomtypes':
                    in_atomtypes_section = True
                else:
                    in_atomtypes_section = False
                new_lines.append(line)
                continue
            if in_atomtypes_section and clean_line and not clean_line.startswith(';'):
                parts = clean_line.split()
                if len(parts) > 0:
                    current_type = parts[0]
                    tags_to_add = []
                    if current_type in sigma_types:
                        tags_to_add.append("5")
                    if current_type in epsilon_types:
                        tags_to_add.append("6")
                    if tags_to_add:
                        suffix_nums = " ".join(tags_to_add)
                        suffix = f" ; PARM {suffix_nums}"
                        new_line = line.rstrip('\n') + suffix + "\n"
                        new_lines.append(new_line)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        with open(output_file_path, 'w') as f:
            f.writelines(new_lines)
        return True, f"Successfully created {os.path.basename(output_file_path)}"
    except Exception as e:
        return False, f"Error processing file: {str(e)}"
