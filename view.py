import numpy as np
import matplotlib.pyplot as plt
import exrutils

rgb, temp = exrutils.read_dual_image("out/image.exr")

fig, axes = plt.subplots(1,2)

axes[0].imshow(temp, cmap="inferno", origin="lower")
axes[1].imshow(rgb.astype(np.float32))
plt.show()