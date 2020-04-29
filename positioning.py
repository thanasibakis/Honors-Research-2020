import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import seaborn as sns; sns.set()
from helpers import *

data = pd.read_csv("mari-bowing-data/variable-speed.csv") \
    .pipe(prepare_position_data)

pca_matrix, pca_data = PCA(data, "x", "y", "z")

eig1 = pca_matrix[:, 0]
xyz = data[["x", "y", "z"]].to_numpy()
projection = project_3D_to_2D(xyz, eig1)



fig, axes = plt.subplots(5, 3)

plot_row(axes, 0, data, "lax", "lay", "laz")
plot_row(axes, 1, data, "vx", "vy", "vz")
plot_row(axes, 2, data, "x", "y", "z")
plot_row(axes, 3, data, "d")
plot_row(axes, 4, pca_data, "PC1", "PC2", "PC3")
plt.show()

sns.scatterplot(projection[:, 0], projection[:, 1])
plt.show()