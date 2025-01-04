import decimal
import json
import pprint


# Todo:  Set gauge percentages and gradient colours.

class Chart:
    """

    Installation
    ============

    The static folder must contain
        *   jquery-3.2.0.min.js
        *   moment.js
        *   The c3 folder

    Each page that want to display a chart must include :
            <!-- Charting scripts -->
            <script type=text/javascript src="{{  url_for('static', filename='jquery-3.2.0.min.js') }}"></script>
            <script src="{{ url_for('static',   filename='c3/c3.min.js')}}"></script>
            <script src="http://d3js.org/d3.v5.min.js" charset="utf-8"></script>
            <link href="{{ url_for('static',   filename='c3/c3.css')}}" rel="stylesheet"/>

    for flask, this is best put into base.html


    Use
    ===

    This class is modeled largely on the pronto file clibvhart.  There are quite a lot of differences but essentially it
    does the same thing.

    A chart object is instantiated with :

    thischart = Chart("Chart Title")

    A chart is made up of a group of values with an index number so the simplest method is to for a set of values
    use AddDataPoint (seriesname, index, value) - The series name is anything you want to call it.

    The miniumum required is some datapoints.  e.g.:
        for i,v in enumerate(thiswx.qnh):
            thischart.AddDataPoint('QNH',i,v)
    Along with the instantiation from above that is all that is required to get a functioning chart


    From here various attributes can be specified.
    The structure of the class is that there is a collection of objects that define things like the axis, series or
    datapoints (and a few others) and the main class contains a list object of each of these classes (emulating
    the pronto memory objects).

    Where an attribute is defined once at the chart level (such as "title" or "legend position") these are defined
    as PROPERTIES of the main chart object.  They are always camel case and they are set (for example) via:

    thischart.HideLegend = True

    Where an attribute is a property of a collection (such as series colour), there is a supporting function at the
    main chart object level to set the property.  Each of these functions start with either "Set" or "Add" and
    use camel case.  Each function specifies, as the first parameter, some kind of key and the second parameter
    is the value to be set.  For example:

    thischart.SetSeriesColour('Hours', "#45C3B4")

    When all the parameters for the chart have been defined, the json that is required for c3.js is retreived via:

    thischart.ChartJson

    To display the chart in HTML the following is needed :

    <div id="chart0"></div>
    <script>
        var chart0 = c3.generate({
            bindto: '#chart0',
            {{ chart0data|safe }}
        });
    </script>

    The there is more than one chart they can be dfined the same way within the script tags.

    If "onclick" is required then the script needs to start with the following function (i.e. after the script tag
    but before the first "var"):

    function clickprocess(chart,series,category,value) {
      console.log('got click:' + chart);
      }

    What you do with the click event is up to you.  A simple redirect to another page can be done with:

    function clickprocess(chart,series,category,value) {
      window.location = "/logbook/logbook/logbook_pages"
      }

    Passing some parameters might look like this:

    function clickprocess(chart,series,category,value) {
      console.log('got click:' + chart);
          window.location = "/myclick/" + chart + "/" + series + "/" + category
      }

    @bp.route('/myclick/<chart>/<series>/<category>', methods=['GET','POST'])
    def myclick(chart,series,category,value=None):
    print('I got a click with {}:{}:{}:{}'.format(chart,series,category,value))
    return redirect(url_for('testchart.chart1'))

    You will almost certainly need to store items in the session cookie during the round trip.
    You may well need the x-axis category list to determine which value the user clicked on:
    session['catlist'] = chart0.CategoryList


    """

    _valid_cht_type = ['line', 'spline', 'step', 'area', 'area-spline', 'area-step', 'bar', 'scatter', 'stanford',
                       'pie', 'donut', 'gauge']

    _predefined_label_format = [
        {'name': 'currency', 'fmt': '$,.2f'},  # Full number display with currency symbol and commas
        # Tidy compact format.  -1246.365 = -$1.1k - The "2" indicates the number of numbers before or after the dp.
        {'name': 'compact$', 'fmt': "$.2s"},
        {'name': 'compact', 'fmt': ".2s"},  # like compact dollar without the $
        {'name': 'percent', 'fmt': ',.2%'},  # 2dp multiply by 100 and have trailing percent
        {'name': 'scientific', 'fmt': '.2e'}  # 2dp multiply by 100 and have trailing percent
    ]

    class ChartError(Exception):
        pass

    class __collectionsparent:

        """
        The collections that are defined in the main class are a list of the specified object.
        e.g. a List of Series Objects or a list of Axis objects.
        Each object inherits from this class which basically just provides a place to put
        code common to every series object.
        """

        @staticmethod
        def _isstr(para):
            if para is None:
                return False
            if not isinstance(para, str):
                return False
            return True

        @staticmethod
        def _isint(para):
            if para is None:
                return False
            if not isinstance(para, int):
                return False
            return True

        @staticmethod
        def _isbool(para):
            if para is None:
                return False
            if not isinstance(para, bool):
                return False
            return True

        @staticmethod
        def _islist(para):
            if para is None:
                return False
            if not isinstance(para, list):
                return False
            return True

        @staticmethod
        def _isnum(para):
            if para is None:
                return False
            if not isinstance(para, (int, float, decimal.Decimal)):
                return False
            return True

    class DataPoint(__collectionsparent):

        def __init__(self, series, index, value):
            self.__series = None
            self.__index = None
            self.__value = None
            self.__colour = None
            # force value settings through setters to ensure data validation:
            self.series = series
            self.index = index
            self.value = value

        @property
        def series(self):
            return self.__series

        @series.setter
        def series(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid Series')
            self.__series = value

        @property
        def index(self):
            return self.__index

        @index.setter
        def index(self, value):
            if not self._isint(value):
                raise TypeError('Invalid Index')
            self.__index = value

        @property
        def value(self):
            return self.__value

        @value.setter
        def value(self, value):
            if not self._isnum(value):
                raise TypeError('Invalid Value')
            self.__value = value

        @property
        def colour(self):
            return self.__colour

        @colour.setter
        def colour(self, colour):
            if not self._isstr(colour):
                raise TypeError('Invalid colour')
            if len(colour) != 7:
                raise AttributeError('Colour Code does not look correct')
            if colour[0] != "#":
                raise AttributeError('Colour Code does not look correct')
            self.__colour = colour

    class Series(__collectionsparent):

        def __init__(self, series, axis='y', chttype=None, colour=None):
            self.__series = None
            self.__axis = None
            self.__chttype = None
            self.__colour = None
            self.__datalabelformat = None
            self.__legendname = None  # This name will override the name that appears in the legend.
            self.__legendhide = False
            # force defaulted attributes through setters:
            self.series = series
            self.axis = axis
            if chttype is not None:
                self.chttype = chttype
            # Colour can be none during instantiation:
            if colour is not None:
                self.colour = colour

        @property
        def series(self):
            return self.__series

        @series.setter
        def series(self, value):
            if not self._isstr(value):
                raise TypeError("Invalid Series")
            self.__series = value

        @property
        def axis(self):
            return self.__axis

        @axis.setter
        def axis(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid Axis')
            if value not in ['x', 'y', 'y2']:
                raise AttributeError('Invalid value for axis')
            self.__axis = value

        @property
        def chttype(self):
            return self.__chttype

        @chttype.setter
        def chttype(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid Chart Type for Series')
            if value not in Chart._valid_cht_type:
                raise AttributeError('Invalid Chart type value for axis')
            self.__chttype = value

        @property
        def datalabelformat(self):
            return self.__datalabelformat

        @datalabelformat.setter
        def datalabelformat(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid DataLabel format for series - not a string')
            if value in [f['name'] for f in Chart._predefined_label_format]:
                self.__datalabelformat = [f['fmt'] for f in Chart._predefined_label_format if f['name'] == value][0]
            else:
                # it's all over to you to get it right.
                self.__datalabelformat = value

        @property
        def colour(self):
            return self.__colour

        @colour.setter
        def colour(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid Colour')
            self.__colour = value

        @property
        def legendname(self):
            return self.__legendname

        @legendname.setter
        def legendname(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid  Legend Name')
            self.__legendname = value

        @property
        def legendhide(self):
            return self.__legendhide

        @legendhide.setter
        def legendhide(self, value):
            if not self._isbool(value):
                raise TypeError('Invalid  Legend Hide')
            self.__legendhide = value


    class Axis(__collectionsparent):

        def __init__(self, name):
            self.__name = ''
            self.__show = True
            self.__label = ''
            self.__minimum = None
            self.__maximum = None
            self.__tick_culling = False
            self.__tick_rotate = 0
            self.__tick_count = 0
            self.__datatype = ''
            self.__format = None
            # apply via setter
            self.name = name
            if name == 'x':
                self.datatype = 'category'

        @property
        def name(self):
            return self.__name

        @name.setter
        def name(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid name')
            self.__name = value

        @property
        def show(self):
            return self.__show

        @show.setter
        def show(self, value):
            if not self._isbool(value):
                raise TypeError('Invalid Show')
            self.__show = value

        @property
        def label(self):
            return self.__label

        @label.setter
        def label(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid Label')
            self.__label = value

        @property
        def minimum(self):
            return self.__minimum

        @minimum.setter
        def minimum(self, value):
            if not self._isnum(value):
                raise TypeError('Invalid Minimum')
            self.__minimum = value

        @property
        def maximum(self):
            return self.__maximum

        @maximum.setter
        def maximum(self, value):
            if not self._isnum(value):
                raise TypeError('Invalid Minimum')
            self.__maximum = value

        @property
        def tick_culling(self):
            return self.__tick_culling

        @tick_culling.setter
        def tick_culling(self, value):
            if not self._isbool(value):
                raise TypeError('Invalid tick_culling')
            self.__tick_culling = value

        @property
        def tick_rotate(self):
            return self.__tick_rotate

        @tick_rotate.setter
        def tick_rotate(self, value):
            if not self._isint(value):
                raise TypeError('Invalid tick_rotate')
            if value < 0 or value > 360:
                raise AttributeError('Tick rotate must be between 0 and 360')
            self.__tick_rotate = value

        @property
        def tick_count(self):
            return self.__tick_count

        @tick_count.setter
        def tick_count(self, value):
            if not self._isint(value):
                raise TypeError('Invalid tick_count')
            self.__tick_count = value

        @property
        def datatype(self):
            return self.__datatype

        @datatype.setter
        def datatype(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid Label')
            value = value.lower()
            if value not in ['category', 'timeseries', 'indexed']:
                raise AttributeError('Value for datatype must be one of category, timeseries or indexed')
            self.__datatype = value

        @property
        def format(self):
            return self.__format

        @format.setter
        def format(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid format for axis - not a string')
            if value in [f['name'] for f in Chart._predefined_label_format]:
                self.__format = [f['fmt'] for f in Chart._predefined_label_format if f['name'] == value][0]
            else:
                # it's all over to you to get it right.
                self.__format = value

    class XSeries(__collectionsparent):

        def __init__(self, index, label='', colour=None):
            self.__index = 0
            self.__label = ''
            # Todo : Not sure about colour at this stage
            self.__colour = None
            # Force setting through setter
            self.index = index
            self.label = label

        @property
        def index(self):
            return self.__index

        @index.setter
        def index(self, value):
            if not self._isint(value):
                raise TypeError('Invalid index')
            self.__index = value

        @property
        def label(self):
            return self.__label

        @label.setter
        def label(self, value):
            if not self._isstr(value):
                raise TypeError('Invalid Label')
            self.__label = value

        # Todo: Colour....

    class Group(__collectionsparent):

        # The group collection is a list
        # in c3.js, there is a suggestion that you can have more than one grouping but only
        # the first in the group is processed, so this is a waste of time.

        def __init__(self, name):
            # The name is really irrelevant.  It is not used in the chart definition, it is merely
            # used to give a name to the group so that we can say thischart.AddSeriesGroup(name, series-name)

            self.name = name
            self.__serieslist = []

        @property
        def name(self):
            return self.__name

        @name.setter
        def name(self, value):
            if not self._isstr(value):
                raise TypeError('The name provided is not a string.')
            self.__name = value

        @property
        def serieslist(self):
            return self.__serieslist

        @serieslist.setter
        def serieslist(self, value):
            if not self._islist(value):
                raise TypeError('Series list is not a list')
            self.__serieslist = value

        def AddSeriesToList(self, value):
            if not self._isstr(value):
                raise TypeError('Passed name is not a string')
            self.__serieslist.append(value)

    class Gridline(__collectionsparent):

        def __init__(self, axis, value, text, position, y2=False):
            self.__axis = None
            self.__value = None
            self.__text = None
            self.__textposition = None
            self.__y2 = False
            self.axis = axis
            self.value = value
            if text is None:
                text = ''
            self.text = text
            self.position = position
            self.y2 = y2

        @property
        def axis(self):
            return self.__axis

        @axis.setter
        def axis(self, value):
            if not self._isstr(value):
                raise TypeError('Axis is not a valid string')
            if value not in ['x', 'y']:
                raise AttributeError('Invalid Axis Supplied.  Must be x or y')
            self.__axis = value

        @property
        def value(self):
            return self.__value

        @value.setter
        def value(self, value):
            if not self._isnum(value):
                raise TypeError('Value is not a valid number {}'.format(value))
            self.__value = value

        @property
        def text(self):
            return self.__text

        @text.setter
        def text(self, value):
            if not self._isstr(value):
                raise TypeError('Text is not a valid string')
            self.__text = value

        @property
        def textposition(self):
            return self.__textposition

        @textposition.setter
        def textposition(self, value):
            if not self._isstr(value):
                raise TypeError('Text Position is not a valid string')
            self.__textposition = value

        @property
        def y2(self):
            return self.__y2

        @y2.setter
        def y2(self, value):
            if not self._isbool(value):
                raise TypeError('Y2 is not a valid Boolean')
            self.__y2 = value

    @classmethod
    def dict_merge(cls, dct, merge_dct):
        """
        This is a vital routine.  The chart is json.  It is internally represented
        as a dictionary.  In order to add elements to the dictionary, virtually randomly,
        we need a method of accumulating and merging the dictionary.  This is it.

        Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
        updating only top-level keys, dict_merge recurses down into dicts nested
        to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
        ``dct``.
        :param dct: dict onto which the merge is executed
        :param merge_dct: dct merged into dct
        :return: None
        """
        for k, v in merge_dct.items():
            if (k in dct and isinstance(dct[k], dict) and isinstance(merge_dct[k], dict)):  # noqa
                cls.dict_merge(dct[k], merge_dct[k])
            else:
                dct[k] = merge_dct[k]

    def __init__(self, title=None):
        if title is None:
            self.Title = 'Chart'
        else:
            self.Title = title
        # Default varialble
        self.__axis = []  # List of axis objects
        self.__series = []  # list of series objects.
        self.__data = []  # list of datapoint objects
        self.__x_series = []  # list of XSeries Objects
        self.__format_object = []  # list of FormatOjbect objects.
        self.__groups = []  # list of group objects.
        self.__gridlines = []  # list of gridline objects
        self.__chart_type = 'line'  # default value if not set
        self.__zoom_allow = False
        self.__zoom_rescale = False
        self.__zoom_show_subchart = False
        self.__pointradius = None
        self.__showpoints = True
        self.__height = None
        self.__width = None
        self.__hidelegend = False
        self.__legendposition = 'bottom'
        # chart level properties
        self.__showdatapointlabels = False
        self.__gauge_percentage_calculated = False
        self.__barwidthtickratio = None
        # Todo:  Stacked bars, format object

    def __str__(self):
        return self.__title

    # setters and getters

    @property
    def Title(self):
        return self.__title

    @Title.setter
    def Title(self, value):
        if value is None:
            raise AttributeError("Title cannot be set to None")
        if not isinstance(value, str):
            raise AttributeError("Title is not a string variable")
        self.__title = value

    @property
    def ShowDataPointLabels(self):
        return self.__showdatapointlabels

    @ShowDataPointLabels.setter
    def ShowDataPointLabels(self, value):
        if not self.__isbool(value):
            raise TypeError("Show Data Point Labels Value invalid")
        self.__showdatapointlabels = value

    @property
    def ChartType(self):
        return (self.__chart_type)

    @ChartType.setter
    def ChartType(self, value):
        if value is None:
            raise AttributeError("chart Type cannot be set to None")
        if not isinstance(value, str):
            raise AttributeError("Chart Type is not a string variable")
        if value not in self._valid_cht_type:
            raise AttributeError("Invalid Chart Type")
        self.__chart_type = value

    @property
    def DataPoints(self):
        return self.__datapoints

    @property
    def ChartJson(self):
        return self.__getChart()

    @property
    def ZoomAllow(self):
        return self.__zoom_allow

    @ZoomAllow.setter
    def ZoomAllow(self, value):
        if not self.__isbool(value):
            raise TypeError("Invalid Boolean value for zoom")
        self.__zoom_allow = value

    @property
    def ZoomRescale(self):
        return self.__zoom_rescale

    @ZoomRescale.setter
    def ZoomRescale(self, value):
        if not self.__isbool(value):
            raise TypeError("Invalid Boolean value for zoom")
        self.__zoom_rescale = value

    @property
    def ZoomShowSubChart(self):
        return self.__zoom_show_subchart

    @ZoomShowSubChart.setter
    def ZoomShowSubChart(self, value):
        if not self.__isbool(value):
            raise TypeError("Invalid Boolean value for zoom")
        self.__zoom_show_subchart = value

    @property
    def Height(self):
        return self.__height

    @Height.setter
    def Height(self, value):
        if not self.__isint(value):
            raise TypeError('Height must be an integer')
        self.__height = value

    @property
    def Width(self):
        return self.__width

    @Width.setter
    def Width(self, value):
        if not self.__isint(value):
            raise TypeError('Width must be an integer')
        self.__width = value

    @property
    def HideLegend(self):
        return self.__hidelegend

    @HideLegend.setter
    def HideLegend(self, value):
        if not self.__isbool(value):
            raise TypeError("Hide Legend Value invalid")
        self.__hidelegend = value

    @property
    def LegendPosition(self):
        return self.__legendposition

    @LegendPosition.setter
    def LegendPosition(self, value):
        if not self.__isstr(value):
            raise TypeError(" Legend Position Value invalid")
        value = value.lower()
        if value not in ['bottom', 'right', 'inset']:
            raise AttributeError("Specified value for legend position must be bottom, right or inset")
        self.__legendposition = value

    @property
    def PointRadius(self):
        return self.__pointradius

    @PointRadius.setter
    def PointRadius(self, value):
        if not self.__isint(value):
            raise TypeError('Invalid value for point radius')
        self.__pointradius = value

    @property
    def ShowPoints(self):
        return self.__showpoints

    @ShowPoints.setter
    def ShowPoints(self,value):
        if not self.__isbool(value):
            raise TypeError('Invalid Value for Show Data Points')
        self.__showpoints = value

    @property
    def BarWidthTickRatio(self):
        return self.__barwidthtickratio

    @BarWidthTickRatio.setter
    def BarWidthTickRatio(self, value):
        if not self.__isnum(value):
            raise TypeError('Invalid Bar Width Type Ratio')
        if value < 0.01 or value > 2:
            raise AttributeError('Bar width as a ratio of tick spacing is out of bounds')
        self.__barwidthtickratio = value

    @property
    def CategoryList(self):
        """
        :return:  Returns a list (in index order) of all the labels used in the x axis
        """
        return [c.label for c in self.__x_series]

    @property
    def IndexList(self):
        """
        :return: a list of unique index values used in the chart.
        """
        return list({ i for i in [dp.index for dp in self.__data]})

    # -----------------------------------------------------------------------------------------
    # Private Methods
    # -----------------------------------------------------------------------------------------

    def __getChart(self):
        #  json.dumps returns data with lots of double quotes (both to dictionary key names and data items.
        #  This does not bother C3.  It copes just fine.
        #  The html includes a "bindto" element in order to determine where on the screen to put the chart.
        #  therefore the json in the html already contains a leading '{' and trailing '}' with this data
        #  wedged in between.  Therefore we need to remove these beginning and ending braces within this code.
        return self.__cleanjson(json.dumps(self.__getChartDict(), default=str)[1:-1])

    def __getChartDict(self):
        if len(self.__data) <= 0:
            return None

        if not self.__validate_chart():
            raise self.ChartError('Invalid Chart')
        chart = {}
        data = {}
        if self.__showdatapointlabels:
            self.dict_merge(data, {'labels': True})
        data['columns'] = []

        # Just be a tad careful: 'AXES' with an s is part of 'data' and determines which axis data is presented
        # whereas 'AXIS' with an i is part of the chart and determines attributes of the axis.
        # set the axes to an empty dictionary so we can set values as required during processing
        data['axes'] = {}
        # set the axis to an empty dictionary so we can set values as required during processing
        chart['axis'] = {}
        # Make sure there are keys for x and y:
        self.dict_merge(chart, {'axis': {'y': {'show': True}}})
        self.dict_merge(chart, {'axis': {'x': {'show': True}}})
        if len([x for x in self.__series if x.axis == 'y2']) != 0:
            self.dict_merge(chart, {'axis': {'y2': {'show': True}}})

        # todo : need to be sure we read these lists in index order.
        # if we have a timeseries chart, then we need to add the x axis into the columns list.
        for a in self.__axis:
            if a.name == 'x':
                if a.datatype in ['timeseries', 'indexed']:
                    self.dict_merge(data, {'x': 'x'})
                    thisseries = ['x'] + [l.label for l in self.__x_series]
                    data['columns'].append(thisseries)
            if a.minimum is not None:
                self.dict_merge(chart, {'axis': {a.name: {'min': a.minimum}}})
            if a.maximum is not None:
                self.dict_merge(chart, {'axis': {a.name: {'max': a.maximum}}})
        for s in self.__series:
            # add the series
            thisseries = []
            thisseries.append(s.series)  # add the series name.
            # now add the values
            # we need to pad out any index values that start less than one.
            seriesdplist = [dp for dp in self.__data if dp.series == s.series]
            # get the max index value
            for i in range(seriesdplist[-1].index + 1):
                # does i exist in the list?
                if len([l for l in seriesdplist if l.index == i]) > 0:
                    thisseries.append([k for k in seriesdplist if k.index == i][0].value)
                else:
                    thisseries.append('null')
            # finally add thisseres to columns:
            data['columns'].append(thisseries)
            data['axes'][s.series] = s.axis
            # make sure we display the y2 axis if selected:
        if self.ChartType is None:
            data['type'] = 'bar'
        else:
            data['type'] = self.ChartType
        # Add any series types
        data['types'] = {}
        for s in self.__series:
            if s.chttype is not None:
                data['types'][s.series] = s.chttype
            if s.datalabelformat is not None:
                self.dict_merge(data, {
                    'labels': {'show': True, 'format': {s.series: "d3.format('" + s.datalabelformat + "')"}}})
        if self.ChartType == 'gauge':
            # add some default colours to give a gradient between 1 and 100
            # red is closest to zero and green closest to 100
            if len(self.__series) == 1:
                # if len([g for g in self.__series if g.colour is not None]) == 0:
                colours = ['#E51406', '#CC280C', '#B33C12', '#9A5018', '#81651E', '#677924', '#4E8D2A', '#35A130',
                           '#1CB536', '#03CA3D']
                threshold = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                chart['color'] = {'pattern': colours, 'threshold': {'values': threshold}}
            chart['gauge'] = {'label': 'show', 'expand': True}
        #
        # Now all the other bits
        #
        # if len(self.__x_series) != 0:
        # #     # todo : chart validate - there needs to be an x-sereis for every index
        #     self.dict_merge(chart, {'axis': {'x': {'type': 'category', 'categories': [l.label for l in self.__x_series]}   }})
        xaxisfound = False
        for a in self.__axis:
            if a.name == 'x':
                if a.datatype == 'timeseries':
                    self.dict_merge(chart, {'axis': {'x': {'type': 'timeseries', 'tick': {'format': '%Y-%m-%d'}}}})
                    xaxisfound = True
                elif a.datatype == 'indexed':
                    self.dict_merge(data, {'x': 'x', 'columns': [['x'] + [l.label for l in self.__x_series]]})
                    self.dict_merge(chart, {'axis': {'x': {'type': 'indexed'}}})
                    xaxisfound = True
        if not xaxisfound:
            # Custom X axis label
            self.dict_merge(chart,
                            {'axis': {'x': {'type': 'category', 'categories': [l.label for l in self.__x_series]}}})
            # self.dict_merge(chart,
            #                 {'axis': {'x': {'type': 'category', 'tick': { 'values': [l.label for l in self.__x_series]}}}})
        # Other axis Attributes:
        for thisaxis in self.__axis:
            if thisaxis.label is not None:
                if thisaxis.name == 'x':
                    self.dict_merge(chart, {
                        'axis': {thisaxis.name: {'label': {'text': thisaxis.label, 'position': 'inner-center'}}}})
                    # TODO: This is the last thing I added to make the category labels work for splines.
                    #  Didn't seem to make much difference.
                    self.dict_merge(chart, {
                        'axis': {thisaxis.name: {'type': 'category'}}})
                else:
                    self.dict_merge(chart, {
                        'axis': {thisaxis.name: {'label': {'text': thisaxis.label, 'position': 'inner-top'}}}})
            if thisaxis.tick_rotate != 0:
                self.dict_merge(chart, {'axis': {thisaxis.name: {'tick': {'rotate': thisaxis.tick_rotate}}}})
            if thisaxis.tick_count != 0:
                self.dict_merge(chart, {'axis': {thisaxis.name: {'tick': {'count': thisaxis.tick_count}}}})
            self.dict_merge(chart, {'axis': {thisaxis.name: {'tick': {'culling': thisaxis.tick_culling}}}})
            # The following is most important to stop the words wrapping in the x axis:
            self.dict_merge(chart, {'axis': {thisaxis.name: {'tick': {'multiline': False}}}})
            if thisaxis.format is not None:
                self.dict_merge(chart, {'axis': {'y': {'tick': {'format': "d3.format('" + thisaxis.format + "')"}}}})
        # Chart Title
        if self.ChartType == 'donut':
            self.dict_merge(chart, {'donut': {'title': self.Title}})
        else:
            chart['title'] = {'text': self.Title, 'show': True, 'position': 'top-center'}
        if self.__zoom_allow:
            self.dict_merge(chart, {'zoom': {"enabled": "true"}})
            if self.ZoomRescale:
                self.dict_merge(chart, {'zoom': {'rescale': 'true'}})
            if self.ZoomShowSubChart:
                # Note:  I cannot make the suppression of the x axis on the subchart work.
                self.dict_merge(chart, {'subchart': {'show': 'true', 'axis': {'x': {'show': 'False'}}}})
        # Add the data to the chart
        if self.__pointradius is not None:
            self.dict_merge(chart, {'point': {"r": self.__pointradius}})
        self.dict_merge(chart, {'point':{"show": self.__showpoints}})

        # deal with any groups - typically stacked bars, but you can stack a scatter on top of a bar.
        if len(self.__groups) > 0:
            data['groups'] = []
            for g in self.__groups:
                data['groups'].append(g.serieslist)

        # Check the Bar Width - This a ratio to the tick spacing - 0.5 is 50% width
        if self.__barwidthtickratio is not None:
            chart['bar'] = {'width': {'ratio': self.__barwidthtickratio}}
        # add any colour elments
        if self.__chartseriescolour() is not None:
            self.dict_merge(data, self.__chartseriescolour())
        # add any Legend Names elments
        if self.__chartserieslegendnames() is not None:
            self.dict_merge(data, self.__chartserieslegendnames())

        # Add any specific Colours
        if self.__chartdatapointcolours() is not None:
            self.dict_merge(data, self.__chartdatapointcolours())

        # merge the function into data
        self.dict_merge(data, self.__chartdataonclick())
        # Add the data dictionary to the chart.
        chart['data'] = data

        # check if gridlines have been specified
        if len(self.__gridlines) > 0:
            # add the gridlines dictionary to the chart
            chart['grid'] = self.__chartgridlinesdict()

        if self.__chartsize() is not None:
            chart['size'] = self.__chartsize()

        # legend position is always defined so add it.
        self.dict_merge(chart, {'legend': {'position': self.LegendPosition}})
        # optionally hide it.
        if self.__hidelegend:
            self.dict_merge(chart, {'legend': {'hide': True}})
        else:
            # check if there are any series that might be hidden
            if len(self.__charthideselectedserieslegend()) > 0:
                self.dict_merge(chart, {'legend': self.__charthideselectedserieslegend()})

        # This is the default list of colours that c3.js applies to each data series.
        # It does not matter that the list is longer than the number of series, it will just use them in order.
        # chart['color'] = {'pattern': ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a', '#d62728',
        #                               '#ff9896', '#9467bd', '#c5b0d5', '#8c564b', '#c49c94', '#e377c2', '#f7b6d2',
        #                               '#7f7f7f', '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5']}

        # Tooltips
        if self.__charttooltip() is not None:
            self.dict_merge(chart, self.__charttooltip())
        # for l in self.__x_series:
        #     print(l.label)
        return chart

    #  -----------------------------------------------------------------------------------------------
    #  Sub methods of chart dict.  These must all start with __chart.....
    #  -----------------------------------------------------------------------------------------------

    def __chartdatapointcolours(self):
        '''
            This function needs to determine the colours for a range of datapoints.  This is not
            supported directly by c3.  We have to provide a function that will look something like

          data: {
            x: 'x',
            columns:
                [
              ['x', 'Category1', 'Category2'],
              ['value', 300, 400]
              ],

            type: 'bar',

            color: function(inColor, data) {
                var colors = ['#FABF62', '#ACB6DD'];
                if(data.index !== undefined) {
                    return colors[data.index];
                }

                return inColor;
            }
        },
        :return: A dictionary starting with {color:....
        '''
        # This Code only applies if a colour has been defined for a datapoint somewhere.
        if len([d for d in self.__data if d.colour is not None]) == 0:
            return None
        color = {}
        functionstring = 'function(Colour,data) {'
        # reintstate the following three lines to add some console logging for debugging purposes.
        # functionstring = " ".join([functionstring,
        #                             'console.log( \' ID: \' + data.id + \' index:\' + data.index + \' Colour:\' + Colour);'
        #                            ])
        # data.id will return the name of the series.
        # data.index will return the index
        # data.value will return the value.
        # Make a big if statement for each dp colour

        # Be jolly careful with the quotes.  We cannot use double quotes in this string because the function
        # that cleans the json will use that as an end-of-function marker.  So we must use single quotes
        # when we want a quote in the string.  This is done with \'
        for dp in [d for d in self.__data if d.colour is not None]:
            functionstring = " ".join([functionstring,
                                       'if (data.id == ',
                                       '\'' + dp.series.strip() + '\'',
                                       ' && data.index == ',
                                       str(dp.index),
                                       ') { return ',
                                       '\'' + dp.colour + '\'',
                                       '}; '
                                       ])
        functionstring = " ".join([functionstring,
                                   'return Colour;}'
                                   ])
        # Todo : reintstate guage colours......
        return {'color': functionstring}

    def __charttooltip(self):
        if self.ChartType not in ['donut', 'pie']:
            return None
        functionstring = "function (value,ratio,id,index) {return value;}"
        return {'tooltip': {'format': {'value': functionstring}}}

    def __chartdataonclick(self):
        functionstring = "function (d,element) {"
        functionstring = " ".join([functionstring,
                                   "console.log(this.element.id, d.id,d.index,d.value);",
                                   "console.log(chart0.data.colors());",
                                   "console.log(chart0.categories());",
                                   # Should work (below) but doesn't appear to.
                                   "console.log(this.internal.config.axis_x_categories[d.index]);",
                                   "clickprocess(this.element.id, d.id,d.index,d.value)",
                                   "}"
                                   ])
        return {'onclick': functionstring}

    def __charthideselectedserieslegend(self):
        '''
            Will return a list of series names for which the legend will be hidden.
        :return: A LIST of dictionaries that will be incorporated into the legend node of the dictionary
        '''
        hidelist = []
        if len([s for s in self.__series if s.legendhide]) > 0:
            for thisseries in [s for s in self.__series if s.legendhide]:
                hidelist.append(thisseries.series)
            return {'hide': hidelist}
        else:
            return hidelist

    def __chartserieslegendnames(self):
        """
            determines the names that appear in the legend.  This is useful when you want a different
            label in the legend compared with the internal name given to the series.
        :return: A Dictionary of legend names.
        """
        names = {}
        if len([s for s in self.__series if s.legendname is not None]) > 0:
            for thisseries in [s for s in self.__series if s.legendname is not None]:
                names[thisseries.series] = thisseries.legendname
            return {'names': names}
        else:
            return None

    def __chartseriescolour(self):
        """
            The chart has overall colours defined by the 'Color' node.
            This function provides the colours that are overwritten by the series
        :return: A dictionary of colours.
        """
        colours = {}
        if len([s for s in self.__series if s.colour is not None]) > 0:
            for thisseries in [s for s in self.__series if s.colour is not None]:
                colours[thisseries.series] = thisseries.colour
            return {'colors': colours}
        else:
            return None

    def __chartsize(self):
        """
            Returns the size node to be added to the chart
            Users may specify either the height, width or both
        :return: A DICTIONARY of size node1
        """
        if self.Height is not None or self.Width is not None:
            size = {}
            if self.Height is not None:
                size['height'] = self.Height
            if self.Width is not None:
                size['width'] = self.Width
            return size
        else:
            return None

    def __chartgridlinesdict(self):
        """
            Determine any specified grid lines either vertical or horizontal.
            Note that a grid line for the y2 axis is specified as 'y' but has node of 'axis' set to 'y2'
                ... Bizarre, but that's what c3.js needs.
        :return: A Dictionary containing a list of grid lines for x and y.
        """
        gridlines = {}
        for gridaxis in ['x', 'y']:
            # Are there any grid lines for this axis?
            if len([gl for gl in self.__gridlines if gl.axis == gridaxis]) > 0:
                # if so loop through them:
                lines = []
                for g in [gl for gl in self.__gridlines if gl.axis == gridaxis]:
                    oneline = {}
                    oneline['value'] = g.value
                    if g.text is not None:
                        oneline['text'] = g.text
                    if g.textposition is not None:
                        oneline['position'] = g.textposition
                    if g.y2:
                        oneline['axis'] = 'y2'
                    # add to the list
                    lines.append(oneline)
                # add the grid
                gridlines[gridaxis] = {'lines': lines}
        # add the gridlines dictionary to the chart
        return gridlines

    #  -----------------------------------------------------------------------------------------------
    #  debugging methods
    #  -----------------------------------------------------------------------------------------------

    def _PrintChartDict(self):
        print("Chart Dictionary")
        print("================")
        pprint.pprint(self.__getChartDict())

    def _PrintChartJson(self):
        print("Chart Json")
        print("==========")
        print(json.dumps(self.__getChartDict(), indent=2, ))

    def _SaveChartDict(self, filename):
        with open(filename, 'w') as filename:
            pprint.pprint(self.__getChartDict(), filename)

    def _SaveChartJson(self, filename):
        with open(filename, 'w') as outfile:
            outfile.write(
                self.__cleanjson(json.dumps(self.__getChartDict(), default=str, indent=2, sort_keys=True)[1:-1]))
            # json.dump(self.__getChartDict(), outfile, indent=4)

    #  -----------------------------------------------------------------------------------------------
    #  Chart Validator
    #  -----------------------------------------------------------------------------------------------

    def __validate_chart(self):
        """
        The routine validates all the internal variables and lists that contain chart data.
        An error is raised if invalid.  The function returns true if it makes it to the end.
        :return: boolean
        """
        # Datapoint count
        if len(self.__data) <= 0:
            raise self.ChartError("There is no data for the chart")
        if len(self.__series) <= 0:
            raise self.ChartError("There must be at least one series defined")
        # Axes Count
        if len(self.__axis) > 3:
            raise self.ChartError("The chart contains more three axes")
        for a in self.__axis:
            if not isinstance(a, self.Axis):
                raise self.ChartError("The axis list contains an object that is not an Axis")
            if a.name not in ['x', 'y', 'y2']:
                raise self.ChartError("There is an axis that is not x,y, or y2")
        if self.ChartType in ['donut', 'pie', 'gauge'] and len([d for d in self.__series if d.axis == 'y2']) > 0:
            raise self.ChartError('Y2 Axes are not supported on donut, pie or gauges')
        # {} braces gives us a SET.  i.e. UNIQUE values only.  In this case we may have more than one series with
        # the same chart type, but we only want it once.  AND we want it in a list so make the set a list
        charttypes = list({s.chttype for s in self.__series if s.chttype is not None})
        if self.ChartType is not None:
            if self.ChartType not in charttypes:
                charttypes.append(self.ChartType)
        # we now have a complete list of the different chart types that might have been used in any series, so now
        # can check - if anything is a donut, pie or gauge, then they ALL must be one of those (i.e. there cannot
        # be any different ones
        if len([c for c in charttypes if c in ['donut', 'pie', 'gauge']]) > 0 and len(charttypes) != 1:
            raise self.ChartError("When guages, pies or donuts are used, there cannot be any other types.")
        # For each datapoint check there is a series
        for d in self.__data:
            if d.series not in [s.series for s in self.__series]:
                raise self.ChartError("There are datapoints for which no series is defined.")

        #
        # # for each datapoint that has at least one colour defined, ensure all other datapoints have a colour
        # # (If colour is being used they must be defined for all datapoints in a series)
        # for seriesname in [dp.series for dp in self.__data if dp.colour is not None]:
        #     # we may end up processing the same series multiple times, but who cares?
        #     # check we have colour for all datapoints
        #     if len([dp for dp in self.__data if dp.series == seriesname and dp.colour is None]) > 0:
        #         # There was at least one datapoint in the series that is none.
        #         raise self.ChartError('There is a series in which some colours have been defined but not for every point in the series.')

        # Remaining code requires the objects to be sorted
        self.__sort_lists()
        # There does NOT  need to be a datapoint for every index value.

        # If there is a set of x axis defined  (XSeries) make sure there is one for each index value.
        # todo : complete the rest.  Follow clibvchart.spl
        #
        return True

    def __sort_lists(self):
        """ This routines sorts the various internal lists correctly"""
        self.__axis.sort(key=lambda x: x.name)
        self.__data.sort(key=lambda x: (x.series, x.index))
        self.__x_series.sort(key=lambda x: x.index)
        self.__series.sort(key=lambda x: x.series)

    # ---------------------------------------------------------------------------------
    #   Testing and debugging
    # ---------------------------------------------------------------------------------

    def _testchartjson(self, chartno):
        if chartno is None:
            chartno = 1
        chart = {}
        if chartno == 1:
            # series1 = ['Whse01', 5, 10, 15, 20, 15, 10, 5]
            # series2 = ['Whse03', 8, 16, 30, 40, 30, 8, 7]
            series1 = ['Whse01', -5574.35, 110547.68, 15857.25478, 20956.23, 15254.58, -1145.7145, 5658.235478]
            series2 = ['Whse03', 8475, 16147, 30158, 40547, 30475, 8124, 7542]
            columns = []
            columns.append(series1)
            columns.append(series2)
            # d3.format(".0%")(0.123);  // rounded percentage, "12%"
            # d3.format("($.2f")(-3.5); // localized fixed-point currency, "(£3.50)"
            # d3.format("+20")(42);     // space-filled and signed, "                 +42"
            # d3.format(".^20")(42);    // dot-filled and centered, ".........42........."
            # d3.format(".2s")(42e6);   // SI-prefix with two significant digits, "42M"
            # d3.format("#x")(48879);   // prefixed lowercase hexadecimal, "0xbeef"
            # d3.format(",.2r")(4223);  // grouped thousands with two significant digits, "4,200"
            formatter = "d3.format('$.2s')"  # This is $333k
            formatter = "d3.format('$,.2f')"  # Full dollars with comma and 2 dp
            formatter = "d3.format('$,')"  # full dollars, commas and floating poing after dp
            formatter = "d3.format(',.2%')"  # full dollars, commas and floating poing after dp
            formatter = "d3.format('.2s')"  # compact without dollars
            formatter = "d3.format('.2e')"  # scientific

            chart['data'] = {'type': 'spline', 'columns': columns, 'labels': {'show': True, 'format': {
                'Whse01': formatter}}}
            chart['Title'] = {'text': 'Chart  1'}
            self.dict_merge(chart, {'axis': {'y': {'tick': {'format': formatter}}}})
        elif chartno == 2:
            data = {}
            data['columns'] = [['data', 60], ['data2', 120]]
            data['type'] = 'donut'
            chart['data'] = data
            chart['Title'] = {'text': 'Chart  2'}
            chart['sub-Title'] = {'text': 'A Subtitle', 'show': True, 'position': 'top-left'}

        filename = '/tmp/testchartdict' + str(chartno) + '.txt'
        with open(filename, 'w') as filename:
            pprint.pprint(chart, filename)
        filename = '/tmp/testchartjsoni_dumps' + str(chartno) + '.json'
        with open(filename, 'w') as outfile:
            outfile.write('just dumps\n')
            outfile.write(json.dumps(chart))
            outfile.write('\nstrip first and last dumps\n')
            outfile.write(json.dumps(chart)[1:-1])
            outfile.write('\nCleaned\n')
            outfile.write(self.__cleanjson(json.dumps(chart)[1:-1]))

        thisjson = json.dumps(chart)[1:-1]
        thisjson = self.__cleanjson(thisjson)
        filename = '/tmp/testchartjson' + str(chartno) + '.json'
        with open(filename, 'w') as outfile:
            outfile.write(thisjson)
        # json.dump(chart, outfile, indent=4)
        # return json.dumps(chart).strip('"')[1:-1]
        # return thisjson[1:-1]
        return thisjson

    def __cleanjson(self, json):
        """
        There is problem with the json from dumps....
        Where we have functions defined then we need to remove the leading and  trailing quotes around the function
        definitions.   One of these starts with d3.format where we are using the standard d3.format function
        to format numbers on the graph.
        The other is when we want to incorporate java functions for colours.
        :type json: object
        :return:
        """
        # left_to_process = json
        # rtn = ''
        # nextstart = left_to_process.find('"d3.format')
        # while nextstart >= 0:
        #     # Remove the first double quote
        #     rtn += left_to_process[0:nextstart]  # everythong up to the double quote
        #     left_to_process = left_to_process[nextstart + 1:] # everthing to the right of the double quote
        #     # now look for the ending one
        #     closingquotepos = left_to_process.find('"')
        #     if closingquotepos < 0:
        #         raise self.ChartError('Problem cleaning the json for d3.format')
        #     rtn += left_to_process[:closingquotepos ]
        #     left_to_process = left_to_process[closingquotepos + 1:]
        #     # Now look for the next one...
        #     nextstart = left_to_process.find('"d3.format')
        # rtn += left_to_process
        rtn = self.__removedoublequotes(json, '"d3.format')
        rtn = self.__removedoublequotes(rtn, '"function')
        return rtn

    def __removedoublequotes(self, string, startingwith):
        left_to_process = string
        rtn = ''
        nextstart = left_to_process.find(startingwith)
        while nextstart >= 0:
            # Remove the first double quote
            rtn += left_to_process[0:nextstart]  # everythong up to the double quote
            left_to_process = left_to_process[nextstart + 1:]  # everthing to the right of the double quote
            # now look for the ending one
            closingquotepos = left_to_process.find('"')
            if closingquotepos < 0:
                raise self.ChartError('Problem cleaning the json for d3.format')
            rtn += left_to_process[:closingquotepos]
            left_to_process = left_to_process[closingquotepos + 1:]
            # Now look for the next one...
            nextstart = left_to_process.find(startingwith)
        rtn += left_to_process
        return rtn

    @staticmethod
    def __removechar(string, position):
        return string[:position] + string[position + 1]

    # -----------------------------------------------------------------------------------------
    # Public Methods
    # -----------------------------------------------------------------------------------------

    def AddDataPoint(self, series, index, value):
        # create and validate a point.
        thispoint = self.DataPoint(series, index, value)

        if self.__gauge_percentage_calculated:
            raise self.ChartError('Data point cannot be added after gauge perecentage calculated')
        # Add the series if not there
        if series not in [d.series for d in self.__series]:
            self.__series.append(self.Series(series))
        # Now add the datapoint
        # check if this combination of series and index exists in the __data list.
        # We use list comprenhension to build a list of items.  In this case it is a list of d.series
        # but it doesn't matter which value we use, we only need to check the LENGTH of the list.
        if len([d.series for d in self.__data if d.series == series and d.index == index]) > 0:
            #  there should only be one....
            # (so we enumerate the list and get list of offsets, then we take the first one (and ignore any others)
            # and update the value of that datapoint....  See the "[0]" after the list comprehension
            self.__data[[offset for offset, obj in enumerate(self.__data)
                         if obj.series == series and obj.index == index][0]].value += value
        else:
            self.__data.append(self.DataPoint(series, index, value))

    def GetDataPointValue(self, series, index):
        """
        The purpose of this routine is allow the caller to interrogate the value at a datapoint.
        The caller may not know this.  They may have made many calls to the adddatapoint function
        but not totalled the value.  They may then want to make some decsions on colour based on the value.
        :param series:
        :param index:
        :return: Value.
        """
        val = 0
        if len([d for d in self.__data if d.series == series and d.index == index]) > 0:
            for dp in [d for d in self.__data if d.series == series and d.index == index]:
                val += dp.value
        return val

    def GetIndexPointValue(self,index,axis):
        """
        Get the total value of all the series at this index
        This is useful because it would appear that c3 does a poor job of determining the
        max value of the y axis if you are using grouped series.
        :param index:
        :return: Value
        """
        val = 0
        maxval = 0
        # start by just looking at the data points for all series at this index
        for s in [ser for ser in self.__series if ser.axis == axis]:
            for d in [dp for dp in self.__data if dp.index == index and dp.series == s.series]:
                if d.value > maxval:
                    maxval = d.value
        # what about grouped ones?
        # Wade through all the groups (usually only one)
        for g in self.__groups:
            # get a totoal of all series that are in a series group at this index point
            totalval = 0
            for s in g.serieslist:
                # sum the value of all the datapoints
                for thisseries in [ts for ts in self.__series if ts.series == s]:
                    if thisseries.axis == axis:
                        totalval += self.GetDataPointValue(thisseries.series,index)
            # now check if they are bigger than the current max value
            if totalval > maxval:
                maxval = totalval
        return maxval

    def SetDataPointColour(self, series, index, colour):
        # check if this combination of series and index exists in the __data list.
        # We use list comprenhension to build a list of items.  In this case it is a list of d.series
        # but it doesn't matter which value we use, we only need to check the LENGTH of the list.
        if len([d.series for d in self.__data if d.series == series and d.index == index]) > 0:
            #  there should only be one....
            # (so we enumerate the list and get list of offsets, then we take the first one (and ignore any others)
            # and update the value of that datapoint....  See the "[0]" after the list comprehension
            self.__data[[offset for offset, obj in enumerate(self.__data)
                         if obj.series == series and obj.index == index][0]].colour = colour
        else:
            raise self.ChartError('No Datapoint for Series and Index when assigning colour')

    #  -----------------------------------------------------------------------------------------------
    #  Series Functions
    #  -----------------------------------------------------------------------------------------------

    def SetSeriesChartType(self, series, charttype):
        if not self.__isstr(series):
            raise TypeError("Invalid Series")
        if not self.__isstr(charttype):
            raise TypeError("Invalid Chart Type")
        charttype = charttype.lower()
        if charttype not in self._valid_cht_type:
            raise AttributeError("Chart Type Invalid")
        # check and add.update...
        if series not in [s.series for s in self.__series]:
            self.__series.append(self.Series(series))
        self.__series[self.__getoffsetbyattr(self.__series, 'series', series)].chttype = charttype

    def SetSeriesAxis(self, series, axis):
        if not self.__isstr(series):
            raise TypeError('Invalid series')
        if not self.__isstr(axis):
            raise TypeError('Invalid Axis')
        axis = axis.lower()
        if axis not in ['x', 'y', 'y2']:
            raise AttributeError('Axis Invalid')
        # add / update
        if series not in [s.series for s in self.__series]:
            self.__series.append(self.Series(series, axis))
        self.__series[self.__getoffsetbyattr(self.__series, 'series', series)].axis = axis

    def SetSeriesColour(self, series, colour):
        if not self.__isstr(series):
            raise TypeError('Invalid series')
        # add / update
        if series not in [s.series for s in self.__series]:
            self.__series.append(self.Series(series))
        self.__series[self.__getoffsetbyattr(self.__series, 'series', series)].colour = colour

    def SetSeriesLegendName(self, series, legendname):
        if not self.__isstr(series):
            raise TypeError('Invalid series')
        # add / update
        if series not in [s.series for s in self.__series]:
            self.__series.append(self.Series(series))
        self.__series[self.__getoffsetbyattr(self.__series, 'series', series)].legendname = legendname

    def SetSeriesLegendHide(self, series, legendhide):
        if not self.__isstr(series):
            raise TypeError('Invalid series')
        # add / update
        if series not in [s.series for s in self.__series]:
            self.__series.append(self.Series(series))
        self.__series[self.__getoffsetbyattr(self.__series, 'series', series)].legendhide = legendhide

    def SetSeriesDataLabelFormat(self, series, datalabelformat):
        if not self.__isstr(series):
            raise TypeError('Invalid series')
        if not self.__isstr(datalabelformat):
            raise TypeError('Invalid data label format')
        # add / update
        if series not in [s.series for s in self.__series]:
            self.__series.append(self.Series(series))
        self.__series[self.__getoffsetbyattr(self.__series, 'series', series)].datalabelformat = datalabelformat

    def SetSeriesShowDataPoint(self, series, showdatapoint):
        if not self.__isstr(series):
            raise TypeError('Invalid series')
        if not self.__isbool(showdatapoint):
            raise TypeError('Invalid showdatapoint (should be boolean)')
        # add / update
        if series not in [s.series for s in self.__series]:
            self.__series.append(self.Series(series))
        self.__series[self.__getoffsetbyattr(self.__series, 'series', series)].showdatapoint = showdatapoint



    #  -----------------------------------------------------------------------------------------------
    #  Axes Functions
    #  -----------------------------------------------------------------------------------------------

    # TODO : make them all look like this:.....

    def SetCategoryValue(self, index, label):
        # Verity input
        if not self.__isint(index):
            raise TypeError('Invlaid Index (not an integer)')
        if not self.__isstr(label):
            raise TypeError('Invalid Label (not a string)')
        # check for value in list and add new or update....
        if index not in [l.index for l in self.__x_series]:
            self.__x_series.append(self.XSeries(index, label))
        self.__x_series[self.__getoffsetbyattr(self.__x_series, 'index', index)].label = label

    def SetAxisDataType(self, axis, type):
        # Validate and deal with case
        if not self.__isstr(axis):
            raise TypeError('Invalid Axis')
        axis = axis.lower()
        if axis not in ['y', 'y2', 'x']:
            raise AttributeError('Axis has invalid value')
        if not self.__isstr(type):
            raise TypeError('Invalid data type')
        type = type.lower()
        if type not in ['category', 'timeseries', 'indexed']:
            raise AttributeError('Type must be one of category, timeseries or indexed.')
        # update or add....
        if axis not in [l.name for l in self.__axis]:
            self.__axis.append(self.Axis(axis))
        self.__axis[self.__getoffsetbyattr(self.__axis, 'name', axis)].datatype = type

    def SetAxisLabel(self, axis, label):
        # Validate and deal with case
        if not self.__isstr(axis):
            raise TypeError('Invalid Axis')
        axis = axis.lower()
        if axis not in ['y', 'y2', 'x']:
            raise AttributeError('Axis has invalid value')
        if not self.__isstr(label):
            raise TypeError('Invalid Label')
        # update or add....
        if axis not in [l.name for l in self.__axis]:
            self.__axis.append(self.Axis(axis))
        self.__axis[self.__getoffsetbyattr(self.__axis, 'name', axis)].label = label

    def SetAxisTickRotate(self, axis, rotate):
        if not self.__isstr(axis):
            raise TypeError('Invalid Axis')
        axis = axis.lower()
        if axis not in ['y', 'y2', 'x']:
            raise AttributeError('Axis has invalid value')
        if not self.__isint(rotate):
            raise TypeError('Invalid rotate')
        # update or add....
        if axis not in [l.name for l in self.__axis]:
            self.__axis.append(self.Axis(axis))
        self.__axis[self.__getoffsetbyattr(self.__axis, 'name', axis)].tick_rotate = rotate

    def SetAxisTickCulling(self, axis, tick_culling):
        if not self.__isstr(axis):
            raise TypeError('Invalid Axis')
        axis = axis.lower()
        if axis not in ['y', 'y2', 'x']:
            raise AttributeError('Axis has invalid value')
        # update or add....
        if axis not in [l.name for l in self.__axis]:
            self.__axis.append(self.Axis(axis))
        self.__axis[self.__getoffsetbyattr(self.__axis, 'name', axis)].tick_culling = tick_culling

    def SetAxisTickCount(self, axis, tick_count):
        if not self.__isstr(axis):
            raise TypeError('Invalid Axis')
        axis = axis.lower()
        if axis not in ['y', 'y2', 'x']:
            raise AttributeError('Axis has invalid value')
        # update or add....
        if axis not in [l.name for l in self.__axis]:
            self.__axis.append(self.Axis(axis))
        self.__axis[self.__getoffsetbyattr(self.__axis, 'name', axis)].tick_count = tick_count

    def SetAxisFormat(self, axis, formatcode):
        if not self.__isstr(axis):
            raise TypeError('Invalid Axis')
        axis = axis.lower()
        if axis not in ['y', 'y2', 'x']:
            raise AttributeError('Axis has invalid value')
        # update or add....
        if axis not in [l.name for l in self.__axis]:
            self.__axis.append(self.Axis(axis))
        self.__axis[self.__getoffsetbyattr(self.__axis, 'name', axis)].format = formatcode

    def SetAxisMin(self, axis, minimum):
        if not self.__isstr(axis):
            raise TypeError('Invalid Axis')
        axis = axis.lower()
        if axis not in ['y', 'y2', 'x']:
            raise AttributeError('Axis has invalid value')
        if not self.__isnum(minimum):
            raise TypeError("Supplied Axis Minimum is not a number")
        # update or add....
        if axis not in [l.name for l in self.__axis]:
            self.__axis.append(self.Axis(axis))
        self.__axis[self.__getoffsetbyattr(self.__axis, 'name', axis)].minimum = minimum

    def SetAxisMax(self, axis, maximum):
        if not self.__isstr(axis):
            raise TypeError('Invalid Axis')
        axis = axis.lower()
        if axis not in ['y', 'y2', 'x']:
            raise AttributeError('Axis has invalid value')
        if not self.__isnum(maximum):
            raise TypeError("Supplied Axis Minimum is not a number")
        # update or add....
        if axis not in [l.name for l in self.__axis]:
            self.__axis.append(self.Axis(axis))
        self.__axis[self.__getoffsetbyattr(self.__axis, 'name', axis)].maximum = maximum

    # ------------------------------------------------------------------------------------------
    # Series Groupings
    # ------------------------------------------------------------------------------------------

    def AddSeriesGroup(self, grpname, seriesname):
        if not self.__isstr(grpname):
            raise TypeError('Invalid Group Name')
        if seriesname not in [s.series for s in self.__series]:
            raise AttributeError('The series name does not exist')
        # update or add....
        if grpname not in [l.name for l in self.__groups]:
            self.__groups.append(self.Group(grpname))
        self.__groups[self.__getoffsetbyattr(self.__groups, 'name', grpname)].AddSeriesToList(seriesname)

    # ------------------------------------------------------------------------------------------
    # Grid Lines
    # ------------------------------------------------------------------------------------------

    def AddGridLine(self, axis, value, text=None, position=None, y2=False):
        self.__gridlines.append(self.Gridline(axis, value, text, position, y2))

    # ------------------------------------------------------------------------------------------
    # Some Chart functions to help the user....
    # ------------------------------------------------------------------------------------------

    # def SetMaxYAxis(self):
    #     """
    #     There seems to be a problem scaling the Y axis when grouped Axes are used.
    #     This function sets the max Yaxis to 5% above the maximum values.
    #     No Data should be added to the chart after this has been called.
    #     :return:
    #     """
    #     maxyused = 0
    #     maxindex = 0
    #     # start by checking each series
    #     for d in self.__data:
    #         if d.value > maxyused:
    #             maxyused = d.value
    #         if d.index > maxindex:
    #             maxindex = d.index
    #     # now check if any are grouped
    #     for g in self.__groups:
    #         for i in range(maxindex):
    #             totalforgroupi = 0
    #             for s in [sl for sl in self.__series if sl.series in g.serieslist]:
    #                 for d in [dp for dp in self.__data if d.series == s.series and d.index == i]:
    #                     totalforgroupi += d.value
    #         if totalforgroupi > maxyused:
    #             maxyused = totalforgroupi
    #     # now we now the max value for y
    #     self.SetAxisMax("y",maxyused)






    # ------------------------------------------------------------------------------------------
    # Some useful functions to help the user....
    # ------------------------------------------------------------------------------------------

    def hex_to_rgb(self, colour_hex):
        # Must be in hex with leading "#"
        if not self.__isstr(colour_hex):
            raise TypeError("Hex cannot be none")
        if len(colour_hex) != 7:
            raise TypeError("Hex value must be 7 characters long")
        if colour_hex[0] != '#':
            raise TypeError("Hex value must start with hash symbol")
        return tuple(int(colour_hex[i:i + 2], 16) for i in (1, 3, 5))

    def rgb_to_hex(self, red, green, blue):
        if not self.__isint(red):
            raise TypeError("Red value is not an integer")
        if red < 0 or red > 255:
            raise AttributeError("Red is not withing the range 0 - 255")
        if not self.__isint(green):
            raise TypeError("green value is not an integer")
        if green < 0 or green > 255:
            raise AttributeError("green is not withing the range 0 - 255")
        if not self.__isint(blue):
            raise TypeError("blue value is not an integer")
        if blue < 0 or blue > 255:
            raise AttributeError("blue is not withing the range 0 - 255")
        return "#" + format(red, '02x') + format(green, '02x') + format(blue, '02x')

    def complementary_colour_hex(self, hexcode):
        # A Complementary colour is the colour that when mixed with the original colour returns grey.
        rgb = self.hex_to_rgb(hexcode)
        return self.rgb_to_hex(255 - rgb[0], 255 - rgb[1], 255 - rgb[2])

    # ------------------------------------------------------------------------------------------
    # Private Methods
    # ------------------------------------------------------------------------------------------

    @staticmethod
    def __getoffsetbyattr(objlist, attr, value):
        """
        Return the offset of a list of ojects.  There may be more that one attr that matches value.
        Only the first one is returned.
        :param objlist: this is a list of objects
        :param attr: This is an attribute of an opject (i.e. a property)
        :param value: This is the value of that attribute we are looking for.
        :return: None - not in the list.  The offset.
        """
        if len([offset for offset, obj in enumerate(objlist) if getattr(obj, attr) == value]) == 0:
            return None
        for o in [offset for offset, obj in enumerate(objlist) if getattr(obj, attr) == value]:
            # Just return the first one....
            return o

    @staticmethod
    def __isstr(para):
        if para is None:
            return False
        if not isinstance(para, str):
            return False
        return True

    @staticmethod
    def __isint(para):
        if para is None:
            return False
        if not isinstance(para, int):
            return False
        return True

    @staticmethod
    def __isbool(para):
        if para is None:
            return False
        if not isinstance(para, bool):
            return False
        return True

    @staticmethod
    def __isnum(para):
        if para is None:
            return False
        if not isinstance(para, (int, float, decimal.Decimal)):
            return False
        return True
