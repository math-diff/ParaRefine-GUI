import py3Dmol
import os
import re
def save_vibration_fast(xyz_file, output_html=None, bohr_to_angstrom=False):
    base_name = os.path.splitext(xyz_file)[0]
    if output_html is None:
        output_html = base_name + ".html"
    if not os.path.exists(xyz_file):
        print(f"Error: File {xyz_file} not found.")
        return None
    with open(xyz_file, 'r') as f:
        lines = f.readlines()
    processed_lines = []
    BOHR_TO_ANGSTROM_FACTOR = 0.52917721067
    freq_display = "Frequency: N/A"
    if len(lines) > 1:
        match = re.search(r'Freq(?:uency)?[:\s]+([-\d\.]+)', lines[1], re.IGNORECASE)
        if match:
            freq_display = f"Frequency: <b>{match.group(1)}</b> cm<sup>-1</sup>"
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        try:
            num_atoms = int(line.split()[0])
            processed_lines.append(lines[i])
            i += 1
        except ValueError:
            processed_lines.append(lines[i])
            i += 1
            continue
        if i < len(lines):
            processed_lines.append(lines[i])
            i += 1
        for _ in range(num_atoms):
            if i < len(lines):
                parts = lines[i].strip().split()
                if len(parts) >= 4:
                    element = re.sub(r'\d+', '', parts[0])
                    try:
                        coords = [float(p) for p in parts[1:4]]
                        x, y, z = coords
                        if bohr_to_angstrom:
                            x *= BOHR_TO_ANGSTROM_FACTOR
                            y *= BOHR_TO_ANGSTROM_FACTOR
                            z *= BOHR_TO_ANGSTROM_FACTOR
                        new_line = f"{element:<4} {x:>12.6f} {y:>12.6f} {z:>12.6f}\n"
                        processed_lines.append(new_line)
                    except ValueError:
                        processed_lines.append(lines[i])
                else:
                    processed_lines.append(lines[i])
                i += 1
    xyz_data = "".join(processed_lines)
    view = py3Dmol.view(width='100%', height='100vh')
    view.addModelsAsFrames(xyz_data, 'xyz')
    view.setStyle({'stick': {'radius': 0.1}, 'sphere': {'scale': 0.25}})
    view.animate({'loop': 'backAndForth', 'interval': 20})
    view.zoomTo()
    html_content = view._make_html()
    custom_html = f"""
    <style>
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
        #freq-info {{
            position: absolute; top: 10px; left: 10px; z-index: 100;
            background-color: rgba(255, 255, 255, 0.8); padding: 5px 10px;
            border-radius: 5px; font-family: Arial, sans-serif; font-size: 16px;
            border: 1px solid #ccc; pointer-events: none;
        }}
    </style>
    <div id="freq-info">{freq_display}</div>
    """
    final_content = custom_html + html_content
    with open(output_html, 'w') as f:
        f.write(final_content)
    print(f"Generated HTML visualization: {output_html}")
    return output_html
