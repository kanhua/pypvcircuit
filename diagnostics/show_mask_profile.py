import matplotlib.pyplot as plt
import skimage.io as sio
import numpy as np

mask_filepath = '../private_data/Mask_profile_20181016.png'

contact_mask = sio.imread(mask_filepath, as_gray=True)

orig_vals = np.unique(contact_mask)

# [  0  60 100 110 120 255]

for idx, val in enumerate(orig_vals):
    all_idx = np.nonzero(contact_mask == val)

    contact_mask[all_idx] = idx

plt.imshow(contact_mask, cmap='Set3')
plt.savefig("mask_profile.png")
plt.show()
