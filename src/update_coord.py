import os
def update_gro_with_psi4(psi4_out_path, gro_file_path):
    coords = []
    try:
        with open(psi4_out_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Psi4 output file not found: {psi4_out_path}")
        return False
    start_index = -1
    for i, line in enumerate(lines):
        if "Geometry (in Angstrom)" in line:
            start_index = i
    if start_index != -1:
        current_idx = start_index + 1
        while current_idx < len(lines):
            line = lines[current_idx].strip()
            current_idx += 1
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                try:
                    x = float(parts[1]) / 10.0
                    y = float(parts[2]) / 10.0
                    z = float(parts[3]) / 10.0
                    coords.append((x, y, z))
                except ValueError:
                    if len(coords) > 0:
                        break
                    continue
            elif len(coords) > 0:
                break
    else:
        print(f"Error: Could not find geometry in {psi4_out_path}")
        return False
    if not coords:
        print("Error: No coordinates extracted from Psi4 output.")
        return False
    try:
        with open(gro_file_path, 'r') as f:
            gro_lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Gro file not found: {gro_file_path}")
        return False
    try:
        num_atoms_gro = int(gro_lines[1].strip())
        if len(coords) != num_atoms_gro:
            print(f"Warning: Atom count mismatch! Psi4 extracted: {len(coords)}, Gro says: {num_atoms_gro}")
    except ValueError:
        print("Warning: Could not parse atom count from gro file header.")
    new_gro_lines = []
    new_gro_lines.append(gro_lines[0])
    new_gro_lines.append(gro_lines[1])
    atom_start_line = 2
    for i in range(len(coords)):
        line_idx = atom_start_line + i
        if line_idx >= len(gro_lines) - 1:
            break
        original_line = gro_lines[line_idx]
        x, y, z = coords[i]
        prefix = original_line[:20]
        new_line = f"{prefix}{x:11.6f}{y:11.6f}{z:11.6f}\n"
        new_gro_lines.append(new_line)
    new_gro_lines.append(gro_lines[-1])
    try:
        with open(gro_file_path, 'w') as f:
            f.writelines(new_gro_lines)
        print(f"Successfully updated coordinates in {gro_file_path} (Precision: .6f)")
        return True
    except Exception as e:
        print(f"Failed to write gro file: {e}")
        return False
