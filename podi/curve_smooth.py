#!/usr/bin/env python


# region

import pandas as pd
from scipy.interpolate import interp1d
import numpy as np

# endregion


def curve_smooth(data, sr):

    xnew = np.linspace(
        data.columns.values.astype(int).min(),
        data.columns.values.astype(int).max(),
        sr,
    )

    curve = data.apply(
        lambda x: interp1d(data.columns.values.astype(int), x, kind="cubic"),
        axis=1,
    )
    curve = curve.apply(lambda x: x(xnew))

    curve2 = []

    for i in range(0, len(curve.index)):
        curve2 = pd.DataFrame(curve2).append((pd.DataFrame(curve[curve.index[i]]).T))

    curve2 = pd.DataFrame(curve2.set_index(curve.index))

    curve2.columns = np.linspace(
        data.columns.values.astype(int).min(),
        data.columns.values.astype(int).max(),
        sr,
    ).astype(int)

    xnew = np.linspace(
        data.columns.values.astype(int).min(),
        data.columns.values.astype(int).max(),
        data.columns.values.astype(int).max()
        - data.columns.values.astype(int).min()
        + 1,
    ).astype(int)

    curve2 = (
        pd.DataFrame(columns=xnew, index=curve2.index)
        .combine_first(curve2)
        .astype(float)
        .interpolate(method="quadratic", axis=1)
    )

    return curve2
