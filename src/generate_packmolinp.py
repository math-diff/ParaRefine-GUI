import os
ATOMIC_WEIGHTS = {
    'H': 1.008, 'HE': 4.003, 'LI': 6.941, 'BE': 9.012, 'B': 10.811,
    'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'NE': 20.180,
    'NA': 22.990, 'MG': 24.305, 'AL': 26.982, 'SI': 28.086, 'P': 30.974,
    'S': 32.065, 'CL': 35.453, 'K': 39.098, 'AR': 39.948, 'CA': 40.078,
    'SC': 44.956, 'TI': 47.867, 'V': 50.942, 'CR': 51.996, 'MN': 54.938,
    'FE': 55.845, 'CO': 58.933, 'NI': 58.693, 'CU': 63.546, 'ZN': 65.38,
    'GA': 69.723, 'GE': 72.64, 'AS': 74.922, 'SE': 78.96, 'BR': 79.904,
    'KR': 83.798, 'RB': 85.468, 'SR': 87.62, 'Y': 88.906, 'ZR': 91.224,
    'I': 126.904
}
def generate_packmol_input(pdb_path, density_str, template_path, output_path):
    mw = 0.0
    if not os.path.exists(pdb_path):
        return False, f"PDB file not found: {pdb_path}"
    try:
        with open(pdb_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    parts = line.strip().split()
                    if not parts:
                        continue
                    element = parts[-1].upper()
                    element_clean = ''.join([i for i in element if not i.isdigit()])
                    weight = ATOMIC_WEIGHTS.get(element_clean, 0.0)
                    if weight == 0.0:
                        print(f"Warning: Element '{element}' weight not found, assuming 0.")
                    mw += weight
    except Exception as e:
        return False, f"Error reading PDB: {str(e)}"
    if mw <= 0.1:
        return False, "Calculated molecular weight is too small or zero."
    box_volume = 30.0 * 30.0 * 30.0
    try:
        density = float(density_str)
    except ValueError:
        return False, "Invalid density value. Please enter a number."
    num_molecules = int(round((density * box_volume * 6.022e-4) / mw))
    print(f"DEBUG: MW={mw:.2f}, Density={density}, Vol={box_volume}, N={num_molecules}")
    if not os.path.exists(template_path):
        return False, f"Template file not found: {template_path}"
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        new_content = content.replace("{number}", str(num_molecules))
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        return False, f"Error writing Packmol input: {str(e)}"
    return True, f"MW: {mw:.2f} g/mol\nMolecules: {num_molecules}\nSaved to: {output_path}"
