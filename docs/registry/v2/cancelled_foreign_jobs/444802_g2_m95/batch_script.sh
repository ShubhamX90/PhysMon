#!/bin/bash
#SBATCH -J g2_m95
#SBATCH -p compute
#SBATCH -N 1
#SBATCH -c 64
#SBATCH -t 24:00:00
#SBATCH -o /scratch/pabitra/qcc/chem_shape/runs/g2_m95_%j.out
cd /scratch/pabitra/qcc/chem_shape
export DFTHC_DATA=/scratch/pabitra/qcc/proj/google-verifiable-quantum-circuit-compilation JAX_PLATFORMS=cpu DFTHC_STARTER=/scratch/pabitra/qcc/chem_shape/starter
/scratch/pabitra/envs/qcomp/bin/python -u dfthc_refit/experiments/adam_train.py inputs/merge_9x95x40.npz runs/g2_m95 --steps 200000 --lr 3e-4 --lr-final 1e-5 --kappa 5e-5 --report 10000 --save 50000
