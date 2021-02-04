#!/usr/bin/python

"""
Fits the a and b parameters of a saturation-scaled logistic function to the time series of adoption data saved in the input CSV file. Can be called as: `python ./estimate_logistic_params.py <CSVFILEPATH>`
Note that the CSV file should contain two columns,one called 't' that contains the time-step data and one called 'Nt' that contains the adoption values at those time steps.To run the test on a simulated dataset, change the variable 'test' near the top of this file from False to True, then call as: `python ./estimate_logistic_params.py`
"""

from scipy.optimize import Bounds, differential_evolution
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys

######
# TODO
# 1. decide if/how best to rescale the time data (perhaps by centering, since currently centered on zero)

# 2. decide if/how best to transform the adoption data (since for now I have assumed it is expressed as instantaneous levels of total adoption, whereas the methodology slides mention that it should be expressed as percent change


############
# set params

# adoption saturation value
M = 1  # percent

# set number of workers to use
n_workers = 8

# code-testing flag
test = False


###########
# functions


def make_logistic_fn(t, M):
    """
    This is a closure around the saturation-scaled logistic function
    (i.e. a function that takes the time-step vector (t)
    and the saturation level (M) as arguments and returns a new function that,
    when called and fed the values of a and b, returns the Nt time series)
    """

    def logistic_fn(a, b):
        # the logistic function
        Nt = M * ((np.exp(a + (b * t))) / (1 + np.exp(a + (b * t))))
        return Nt

    return logistic_fn


def make_sse_fn(t, Nt, M):
    """
    This is a closure around the SSE function for a given pair of
    a and b estimates
    (i.e. a function that takes the time and adoption data series (t and Nt)
     and the M value as arguments and returns a new function that,
     when called and fed the a and b parameter estimates,
     returns the sum of squared errors between the true adoption data series and
     the adoption data series calculated using these parameter estimates)
    This is the function to be minimized by the call to
    scipy.optimize.differential_evolution.
    """

    def sse_fn(params):
        a = params[0]
        b = params[1]
        # calculate the Nt estimated data values using the params
        logistic_fn = make_logistic_fn(t, M)
        Nt_est = logistic_fn(a, b)
        # calculate the sum of squared errors between those estimated values
        # and the true values
        err = Nt - Nt_est
        sse = np.sum(err ** 2)
        return sse

    return sse_fn


def estimate_params(t, Nt, M):
    """
    This is the main function that, when given the time steps (t),
    the adoption values matching those time steps (Nt), and the M value (M),
    will use scipy.optimize.differential_evolution to calculate the a and b
    values that minimize the SSE between Nt and the adoption values fitted
    using the logistic function.
    Returns a, b, and the SSE at those values.
    """

    # make the SSE fn, which needs to be minimized
    sse_fn = make_sse_fn(t, Nt, M)
    # set the bounds
    bounds = Bounds([0, 0], [1, 1])
    # minimize the SSE function and return the result
    result = differential_evolution(sse_fn, bounds)
    # workers=n_workers, updating='deferred')
    return (result.x[0], result.x[1], result.fun)


################
# test the code?

if test:
    # generate data to test this out
    a = 0.001
    b = 0.1
    M = 1
    t = np.arange(-100, 100, 1)
    Nt = logistic_fn = make_logistic_fn(t, M)(a, b)
    # add some jitter to Nt
    Nt_jitt = Nt + np.random.normal(0, 0.2, len(Nt))

    # estimate the params and compare them
    a_fit, b_fit, sse = estimate_params(t, Nt_jitt, M)
    print(
        (
            "\nREAL VALUES:\n\ta=%0.3f\tb=%0.3f\n\n"
            "ESTIMATES:\n\ta=%0.3f\tb=%0.3f\n\n"
            "SSE: %0.3f\n\n"
        )
        % (a, b, a_fit, b_fit, sse)
    )

    # plot the real data and the estimated data, to test it out
    fig = plt.figure()
    plt.plot(t, Nt, color="black")
    plt.scatter(t, Nt_jitt, c="black")
    # calculate the fitted curve
    Nt_fit = make_logistic_fn(t, M)(a_fit, b_fit)
    plt.plot(t, Nt_fit, color="red")
    plt.xlabel("t")
    plt.ylabel("N(t)")
    fig.show()


###############################
# else, fit values to a dataset

else:
    # get the name of the tabular file to read in
    filename = sys.argv[1]
    print("\n\nLOADING DATA TO BE FITTED FROM FILE: %s\n\n" % filename)
    # read in the table
    df = pd.read_csv(filename)
    # get the t and Nt data
    t = df.t
    Nt = df.Nt
    # run the estimate and return the result
    a_fit, b_fit, sse = estimate_params(t, Nt, M)
    print("\na: %0.3f\nb: %0.3f\n" % (a_fit, b_fit))

    # plot the real data and the estimated data, to test it out
    fig = plt.figure()
    plt.scatter(t, Nt, c="black")
    # calculate the fitted curve
    Nt_fit = make_logistic_fn(t, M)(a_fit, b_fit)
    plt.plot(t, Nt_fit, color="red")
    plt.xlabel("t")
    plt.ylabel("N(t)")
    fig.show()

    input("\n\nRESULTING CURVE IS PLOTTED\n\n<Enter> to exit.\n\n")
