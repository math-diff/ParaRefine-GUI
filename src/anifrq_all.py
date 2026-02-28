#!/usr/bin/env python
from __future__ import division
from builtins import range
import os, sys
import numpy as np
from forcebalance.molecule import Molecule
from forcebalance.readfrq import read_frq_gen
def ensure_angstrom_units(xyz):
    if len(xyz) < 2:
        return xyz
    diff = xyz[:, np.newaxis, :] - xyz[np.newaxis, :, :]
    dists = np.linalg.norm(diff, axis=-1)
    np.fill_diagonal(dists, np.inf)
    min_dists = np.min(dists, axis=1)
    avg_min_dist = np.mean(min_dists)
    if avg_min_dist > 2.0:
        print(f"  [Unit Check] Detected Bohr units (Avg bond len: {avg_min_dist:.2f}). Converting to Angstroms...")
        return xyz * 0.52917721067
    else:
        print(f"  [Unit Check] Detected Angstrom units (Avg bond len: {avg_min_dist:.2f}). No conversion needed.")
        return xyz
def generate_all_animations(fout):
    if not os.path.exists(fout):
        raise FileNotFoundError(f"File not found: {fout}")
    print(f"Reading frequency data from: {fout}")
    frqs, modes, intens, elem, xyz = read_frq_gen(fout)
    xyz = ensure_angstrom_units(xyz)
    num_modes = len(frqs)
    generated_files = []
    print(f"Total modes found: {num_modes}. Starting generation...")
    for modenum in range(1, num_modes + 1):
        M = Molecule()
        M.elem = elem[:]
        M.xyzs = []
        xmode = modes[modenum - 1]
        if M.na > 0:
            norm_factor = np.linalg.norm(xmode)
            if norm_factor > 1e-6:
                xmode /= (norm_factor / np.sqrt(M.na))
            xmode *= 0.3
        spac = np.linspace(0, 1, 101)
        disp = np.concatenate((spac, spac[::-1][1:], -1*spac[1:], -1*spac[::-1][1:-1]))
        for i in disp:
            M.xyzs.append(xyz + i * xmode.reshape(-1, 3))
        M.comms = ['Vibrational Mode %i Frequency %.3f Displacement %.3f' %
                   (modenum, frqs[modenum-1], disp[i]*0.3)
                   for i in range(len(M))]
        output_filename = os.path.splitext(fout)[0] + '.mode%03i.xyz' % modenum
        M.write(output_filename)
        generated_files.append(output_filename)
        if modenum == 1 or modenum % 10 == 0:
            print(f"Generated: {output_filename}")
    return num_modes, generated_files
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python anifrq.py psi4.out [mode_number]")
        sys.exit(1)
    fout = sys.argv[1]
    if len(sys.argv) >= 3:
        modenum = int(sys.argv[2])
        if modenum == 0:
            raise RuntimeError("Start mode number from one, please")
        frqs, modes, intens, elem, xyz = read_frq_gen(fout)
        xyz = ensure_angstrom_units(xyz)
        print(f"Warning: Single mode generation in CLI is simplified. Please use generate_all_animations for full features.")
    else:
        generate_all_animations(fout)
