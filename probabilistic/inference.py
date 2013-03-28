import database
import copy
import random
import math


def sample(computation, iters):
	"""
	Sample from a probabilistic computation for some
	number of iterations.

	This uses vanilla, single-variable trace MH
	TODO: Implement other inference backends.
	"""

	# Analytics
	proposalsMade = 0
	proposalsAccepted = 0

	# Run computation to populate the database
	# with an initial trace
	assert(database.getCurrentDatabase() == None)	# No nested query support
	database.newDatabase()
	currsamp = database.getCurrentDatabase().traceUpdate(computation)

	# Bail early if the computation is deterministic
	if database.getCurrentDatabase().numVars() == 0:
		return [currsamp for i in range(iters)]


	# MH inference loop
	samps = [currsamp]
	i = 0
	while i < iters:

		i += 1

		rvdb = database.getCurrentDatabase()

		# Make proposal for a randomly-chosen variable
		name, var = rvdb.chooseVariableRandomly()
		propval = var.erp._proposal(var.val, var.params)
		forwardPropLogProb = var.erp._logProposalProb(var.val, propval, var.params)
		reversePropLogProb = var.erp._logProposalProb(propval, var.val, var.params)

		# Copy the database, make the proposed change, and update the trace
		currdb = rvdb
		propdb = copy.deepcopy(rvdb)
		database.setCurrentDatabase(propdb)
		vrec = propdb.getRecord(name)
		vrec.val = propval
		vrec.logprob = vrec.erp._logprob(vrec.val, vrec.params)
		retval = propdb.traceUpdate(computation)

		# Accept or reject the proposal
		acceptThresh = propdb.logprob - currdb.logprob + reversePropLogProb - forwardPropLogProb
		if math.log(random.random()) < acceptThresh:
			proposalsAccepted += 1
			currsamp = retval
		else:
			database.setCurrentDatabase(currdb)
		proposalsMade += 1
		samps.append(currsamp)

	database.setCurrentDatabase(None)

	print "Acceptance ratio: {0}".format(float(proposalsAccepted)/proposalsMade)
	return samps