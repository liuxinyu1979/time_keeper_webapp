
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO

def admin_plot_img(date_range, y_axis_lbls, vals_two_dim, plot_title):
    plt.rcParams.update({'font.size': 10})
    plt.style.use('grayscale')

    fig = Figure()
    axs = fig.add_subplot(1, 1, 1)
    # remove the year from yyyy-mm-dd
    date_range_no_year = [d[5:] for d in date_range]
    axs.imshow(vals_two_dim, cmap = 'Greens')
    # Show all ticks and label them with the respective list entries
    axs.set_xticks(np.arange(len(date_range_no_year)), labels=date_range_no_year)
    axs.set_yticks(np.arange(len(y_axis_lbls)), labels=y_axis_lbls)
    # Loop over data dimensions and create text annotations.
    for i in range(len(y_axis_lbls)):
        for j in range(len(date_range_no_year)):
            text = axs.text(j, i, vals_two_dim[i][j],
                        ha="center", va="center", color="r")
    axs.set_title(plot_title)  # Add a title to the axes.
    axs.legend()  # Add a legend.    
    axs.set_xticklabels(axs.get_xticklabels(), rotation=315, ha='right')

    pngImage = BytesIO()
    FigureCanvas(fig).print_png(pngImage)
    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    return pngImageB64String