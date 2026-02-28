import os
def save_dihedrals_to_itp(itp_path, dihedral_string, output_path=None):
    if not os.path.exists(itp_path):
        return False, f"Source file not found: {itp_path}"
    if not dihedral_string or not dihedral_string.strip():
        return False, "Dihedral string is empty"
    if output_path is None:
        output_path = itp_path
    target_dihedrals = []
    raw_groups = dihedral_string.split(';')
    for group in raw_groups:
        atoms = group.strip().split()
        if len(atoms) == 4:
            target_dihedrals.append(atoms)
    if not target_dihedrals:
        return False, "No valid dihedrals parsed from input"
    try:
        with open(itp_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return False, f"Read error: {str(e)}"
    new_lines = []
    is_dihedral_section = False
    modified_count = 0
    for line in lines:
        clean_line = line.strip()
        if clean_line.startswith('[') and clean_line.endswith(']'):
            section_name = clean_line[1:-1].strip().lower()
            is_dihedral_section = (section_name == 'dihedrals')
            new_lines.append(line)
            continue
        if is_dihedral_section and clean_line and not clean_line.startswith(';'):
            parts = clean_line.split()
            if len(parts) >= 4:
                file_atoms = parts[:4]
                is_match = False
                for target in target_dihedrals:
                    if file_atoms == target or file_atoms == target[::-1]:
                        is_match = True
                        break
                if is_match:
                    if "; PARM 5 6" not in line:
                        line = line.rstrip('\n') + " ; PARM 5 6\n"
                        modified_count += 1
        new_lines.append(line)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    except Exception as e:
        return False, f"Write error: {str(e)}"
    return True, f"Successfully created {output_path} (Modified {modified_count} lines)"
