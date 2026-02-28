import os
import re
from pathlib import Path
from typing import Tuple, Union
def create_psi4_file(
    charge: int,
    multiplicity: int,
    basis_set: str,
    method: str,
    memory: str,
    threads: int,
    template_path: Union[str, Path],
    output_path: Union[str, Path],
    pdb_path: Union[str, Path]
) -> Tuple[bool, str]:
    template_p = Path(template_path)
    output_p = Path(output_path)
    pdb_p = Path(pdb_path)
    try:
        if not template_p.exists():
            return False, f"Not found template file: {template_p}"
        if not pdb_p.exists():
            return False, f"Not found PDB file: {pdb_p}"
        coords_lines = []
        atom_name_pattern = re.compile(r'([a-zA-Z]+)')
        with open(pdb_p, 'r', encoding='utf-8') as pdb:
            for line in pdb:
                if line.startswith(("ATOM", "HETATM")):
                    try:
                        x = line[30:38].strip()
                        y = line[38:46].strip()
                        z = line[46:54].strip()
                        element = line[76:78].strip()
                        if not element:
                            atom_name = line[12:16].strip()
                            match = atom_name_pattern.search(atom_name)
                            element = match.group(1) if match else atom_name
                        element = element.capitalize()
                        coords_lines.append(f"{element:<4} {x:>12} {y:>12} {z:>12}")
                    except (IndexError, ValueError):
                        continue
        if not coords_lines:
            return False, "No valid ATOM/HETATM records found inside the PDB file."
        coordinates_str = "\n".join(coords_lines)
        content = template_p.read_text(encoding='utf-8')
        replacements = {
            "{CHARGE}": str(charge),
            "{MULTIPLICITY}": str(multiplicity),
            "{BASIS_SET}": str(basis_set),
            "{METHOD}": str(method),
            "{MEMORY_SIZE}": str(memory),
            "{THREAD_CPU}": str(threads),
            "{COORDINATES}": coordinates_str
        }
        for key, value in replacements.items():
            content = content.replace(key, value)
        if output_p.parent:
            output_p.parent.mkdir(parents=True, exist_ok=True)
        output_p.write_text(content, encoding='utf-8')
        return True, f"Psi4 input file generated: {output_p.name}"
    except Exception as e:
        return False, f"Error processing {pdb_p.name}: {str(e)}"
