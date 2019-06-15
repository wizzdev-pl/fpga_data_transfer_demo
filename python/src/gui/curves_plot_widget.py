import pyqtgraph as pg


from PySide2 import QtCore
#from .plot_data_source import PlotData


class GraphicWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)

        self._plot = self.addPlot(row=0, col=0, colspan=3)
        x_axis = self._plot.getAxis('bottom')
        x_axis.setLabel(text='time', unitPrefix='s')
        x_axis.enableAutoSIPrefix(True)
        self.setBackground('w')

    def setDownsampling(self, ds, auto, mode):
        self._plot.setDownsampling(ds, auto, mode)

    def plot_data(self, data_to_plot, min_time):
        self._max_x = data_to_plot['time'][-1]
        self._plot.setXRange(min_time, self._max_x, padding=0)

        plotted_curves = self._plot.listDataItems()

        time = data_to_plot['time']
        values = data_to_plot['values']
        #channel_number = i
        #channel_name = "Channel_{}".format(i+1)
        channel_name = "Data"
        if len(time) < 2:
            return  # skip empty and single points channels

        if len(plotted_curves) != 0:
            plotted_curves[0].setData(time, values, name=channel_name)
            #plotted_curves[0].channel_id = channel_number

        else:
            curve = self._plot.plot(time, values,
                                    clickable=True, name=channel_name,
                                    connect="finite")

            #curve.channel_id = channel_number
            curve.channel_name = channel_name
            curve.is_selected = False
            pen = pg.mkPen(color=(0,0,200), width=3)
            curve.setPen(pen)
