#!/bin/bash
#SBATCH -J g1_b7
#SBATCH -p compute
#SBATCH -N 1
#SBATCH -c 64
#SBATCH -t 48:00:00
#SBATCH -o /scratch/pabitra/qcc/chem_shape/runs/g1_b7_%j.out
THR=60 LBU=1.0 LBI=3000 bash /scratch/pabitra/qcc/chem_shape/finishg1.sh inputs/adam_9x143x40.npz runs/g1_b7 7
