import argparse
import numpy as np
import matplotlib.pyplot as plt


ALPHA = 0.9
NORMALIZATION = (1 + ALPHA) / 2


def declutter(cir: np.ndarray, alpha: float = ALPHA, normalization: float = NORMALIZATION) -> np.ndarray:
    decBase = cir[0]
    res = np.empty_like(cir)

    for i in range(cir.shape[0]):
        res[i] = normalization * (cir[i] - decBase)
        decBase = alpha * decBase + (1-alpha) * cir[i]

    return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='declutter visualization',
        description='See the effect of the decluttering algorithm on SR250Mate radar images',
    )

    parser.add_argument(
        'filename',
        type=str,
        help='Which dataset file to open'
    )

    parser.add_argument(
        '--max-samples',
        type=int,
        help='Select how many time sample to visualize',
        default=620
    )

    parser.add_argument(
        '--max-bins',
        type=int,
        help='Select how many bins to visualize',
        default=30
    )

    args = parser.parse_args()
    max_bins = args.max_bins
    max_samples = args.max_samples

    # controllo che effettivamente sia un file prodotto dal sensore SR250Mate
    raw = np.load(args.filename)
    assert(raw.ndim == 2)
    assert(raw.shape[1] == 120)
    assert(raw.dtype == np.complex64)

    abs = np.abs(raw)
    out = declutter(abs)

    # voglio mettere l'asse dei tempi in secondi
    # so che ogni sample è 1/fps = 1/20 di secondo
    bins = np.arange(raw.shape[1])
    seconds = np.arange(raw.shape[0]) / 20

    # questo mi serve per plottare i dati come un pcolormesh
    XX, YY = np.meshgrid(seconds, bins)

    fig, ax = plt.subplots(2,1)
    ax[0].pcolormesh(XX[:max_bins, :max_samples], YY[:max_bins, :max_samples], abs.T[:max_bins, :max_samples])
    ax[0].set_title('Original')

    ax[1].pcolormesh(XX[:max_bins, :max_samples], YY[:max_bins, :max_samples], out.T[:max_bins, :max_samples])
    ax[1].set_title('Declutter')
    ax[1].set_xlabel('seconds')

    plt.tight_layout()
    plt.show()
