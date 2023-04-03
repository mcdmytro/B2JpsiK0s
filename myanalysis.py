#!/usr/bin/env python3

import sys
import basf2 as b2
import modularAnalysis as ma
import stdV0s
import variables.collections as vc
from variables import variables as vm
import variables.utils as vu

# Get input file number from the command line
filenumber = sys.argv[1]

# Create path
main = b2.Path()

# Load input data from mdst/udst file
ma.inputMdstList(filelist=[b2.find_file(f"starterkit/2021/1111540100_eph3_BGx0_{filenumber}.root", "examples")],path=main)

# Fill final state particle lists
ma.fillParticleList("e+:uncorrected", "electronID > 0.1 and dr < 0.5 and abs(dz) < 2 and thetaInCDCAcceptance", path=main)
stdV0s.stdKshorts(path=main)

# Bremstrahlung correction
vm.addAlias("goodFWDGamma", "passesCut(clusterE>0.075 and clusterReg==1)")
vm.addAlias("goodBRLGamma", "passesCut(clusterE>0.050 and clusterReg==2)")
vm.addAlias("goodBWDGamma", "passesCut(clusterE>0.100 and clusterReg==3)")
vm.addAlias("goodGamma", "passesCut(goodBWDGamma or goodBRLGamma or goodBWDGamma)")
ma.fillParticleList("gamma:brems", "goodGamma", path=main)
ma.correctBrems("e+:corrected", "e+:uncorrected", "gamma:brems", path=main)

# Combine final state particles to form composite particles
ma.reconstructDecay("J/psi:ee -> e+:corrected e-:corrected ?addbrems", cut="dM < 0.11", path=main)

# Combine J/psi and KS candidates to form B0 candidates
ma.reconstructDecay(
    "B0 -> J/psi:ee K_S0:merged",
    cut="Mbc>5.2 and abs(deltaE)<0.15",
    path=main
)

# Perform MC matching
ma.matchMCTruth("B0", path=main)

# Build the ROE object and apply a mask on it
ma.buildRestOfEvent('B0', fillWithMostLikely=True, path = main)
track_based_cuts = "thetaInCDCAcceptance and pt > 0.075 and dr < 5 and abs(dz) < 10"
ecl_based_cuts = "thetaInCDCAcceptance and E > 0.05"
roe_mask = ("my_mask", track_based_cuts, ecl_based_cuts)
ma.appendROEMasks("B0", [roe_mask], path=main)

#
#    Define which variable to export to the output file (ntuple)
#

# vm.addAlias("ep_E","daughter(0, daughter(0, E))") # a way to define an alias for a particular variable

# Adding B0 variables
std_vars = vc.kinematics + vc.mc_kinematics + vc.mc_truth
all_vars = std_vars + vc.deltae_mbc

# Add ROE variables
roe_kinematics = ["roeE()", "roeM()", "roeP()", "roeMbc()", "roeDeltae()"]
roe_multiplicities = ["nROE_Charged()", "nROE_Photons()", "nROE_NeutralHadrons()"]
all_vars += roe_kinematics + roe_multiplicities

# Adding masked ROE variables
for name in roe_kinematics + roe_multiplicities:
    all_vars += [name[:-2] + "(my_mask)"]

# Adding final state particles' variables
fs_vars = vc.pid + vc.track + vc.track_hits + std_vars
vm.addAlias("isBremsCorrected", "extraInfo(bremsCorrected)")
all_vars += vu.create_aliases_for_selected(
    fs_vars + ["isBremsCorrected"], 
    "B0 -> [J/psi -> ^e+ ^e-] [K_S0 -> ^pi+ ^pi-]",
    prefix=["ep", "em", "pip", "pim"]
)

# Adding intermediate particles' variables
interm_vars = vc.inv_mass + std_vars
all_vars += vu.create_aliases_for_selected(interm_vars, "B0 -> ^J/psi ^K_S0", prefix=["Jpsi", "K0s"])

# Bremnsstrahlung correction variables
vm.addAlias("Jpsi_M_uncorrected", "daughter(0, daughterCombination(M,0:0,1:0))")
vm.addAlias("withBremsCorrection",
            "passesCut(passesCut(ep_isBremsCorrected == 1) or passesCut(em_isBremsCorrected == 1))")
all_vars += ["Jpsi_M_uncorrected", "withBremsCorrection"]

# Add variables in CMS for all particles
cmskinematics = vu.create_aliases(vc.kinematics, "useCMSFrame({variable})", "CMS")
all_vars += vu.create_aliases_for_selected(
    cmskinematics, 
    "^B0 -> [^J/psi -> ^e+ ^e-] [^K_S0 -> ^pi+ ^pi-]",
    prefix=["B0", "Jpsi", "ep", "em", "K0s", "pip", "pim"])

# Export reconstruction result in a root file
ma.variablesToNtuple(
    "B0",
    variables=all_vars,
    filename="B2JpsiK0s.root",
    treename="tree",
    path=main,
)

# Start the event loop (actually start processing things)
b2.process(main)

# Print out the summary
print(b2.statistics)