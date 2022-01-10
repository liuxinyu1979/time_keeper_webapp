
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO

def heatmap_plot_img(date_range, y_axis_lbls, vals_two_dim, plot_title):
    plt.rcParams.update({'font.size': 10})
    plt.style.use('grayscale')

    fig = Figure()
    axs = fig.add_subplot(1, 1, 1)
    # remove the year from yyyy-mm-dd
    date_range_no_year = date_range

    if len(date_range[0]) >= 3:
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
    axs.set_xticklabels(axs.get_xticklabels(), rotation=315, ha='left')

    pngImage = BytesIO()
    FigureCanvas(fig).print_png(pngImage)
    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    return pngImageB64String


def time_bucket_bar_plot_img(date_range, values, y_lbl, graph_title, legend_txt):
    plt.rcParams.update({'font.size': 10})
    plt.style.use('grayscale')
    width = 0.2
    fig = Figure()
    axs = fig.add_subplot(1, 1, 1)
    # remove the year from yyyy-mm-dd
    date_range_no_year = [d[5:] for d in date_range]
 
    axs.bar(date_range_no_year, values, width, label=legend_txt, color=(0.8, 0.2, 0.2, 0.5))  
    axs.bar_label(axs.containers[0])
    axs.set_ylabel(y_lbl, fontsize=10)  # Add a y-label to the axes.
    axs.set_title(graph_title)  # Add a title to the axes.
    axs.legend()  # Add a legend.  
    axs.xaxis.set_ticks(date_range_no_year)
    axs.set_xticklabels(date_range_no_year, rotation=315, ha='left')

    pngImage = BytesIO()
    FigureCanvas(fig).print_png(pngImage)
    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    return pngImageB64String



def time_bucket_double_bar_plot_img(date_range, vals1, vals2, y_lbl, graph_title, legend_txt1, legend_txt2):
    plt.rcParams.update({'font.size': 10})
    plt.style.use('grayscale')
    width = 0.2
    fig = Figure()
    axs = fig.add_subplot(1, 1, 1)
    # remove the year from yyyy-mm-dd
    date_range_no_year = [d[5:] for d in date_range]
 
    ind = np.arange(len(date_range)) 
    width = 0.2
    axs.bar(ind, vals1, width, label=legend_txt1, color=(0.8, 0.2, 0.2, 0.5))  # Plot some data on the axes.
    axs.bar(ind+width, vals2, width, label=legend_txt2,color=(0.2, 0.2, 0.8, 0.5))  # Plot more data on the axes...    
    axs.set_xticks(ind + width / 2, date_range)
    axs.set_ylabel(y_lbl, fontsize=5)  # Add a y-label to the axes.
    axs.set_title(graph_title)  # Add a title to the axes.
    axs.legend()  # Add a legend.  
    axs.set_xticklabels(date_range_no_year, rotation=315, ha='left')

    pngImage = BytesIO()
    FigureCanvas(fig).print_png(pngImage)
    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    return pngImageB64String