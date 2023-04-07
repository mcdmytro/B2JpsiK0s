import basf2 as b2
import generators as gen
import simulation as sim
import reconstruction as rec
import mdst

# Crating a path
main = b2.Path()

# Setting productoin parameters
main.add_module('EventInfoSetter', evtNumList=[10], expList=[0])

# Adding events' generator
gen.add_evtgen_generator(
    finalstate='signal',
    signaldecfile=b2.find_file('B2JpsiK0s.dec'),
    path=main
)

# Simulating detector response and the L1 trigger
sim.add_simulation(path=main)

# Performing tracks reconstruction
rec.add_reconstruction(path=main)

# Storing reconstructed data
mdst.add_mdst_output(filename='B2JpsiK0s_mdst_out.root', path=main)

# Process the steering path
b2.process(path=main)

# Print out the summary
print(b2.statistics)