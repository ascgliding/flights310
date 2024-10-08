from requests import post
from datetime import datetime, timedelta
from dateutil import tz
import pytz
import json

# you must register for use of the api at the metservice website.
# see secure note in lastpass.


class MetService():

    '''
    This class accesses and returns forecasts from the metservice.
    Instantiate the class with no parameters or a single parameter containing a list of the variables
    you want to return (see __available_variables).
    The set the APIkey.
    Finally call get_current with the parameters of longitude, latitude
        optionally :
            "savefilename": you can store the returned json in a file
            "interval" : The time between readings in hours (eg. 2 will return readings every two hours)
                the default is hourly
            "reading_count" : the number of readings you want returned.

    There exists the :"get_current_file" method which can be called if get_current has previously been
    called with the filename parameter.  This is really intended mostly for debugging.

    After calling "get_current" you can then access each the returned values as properties of the object.

    '''


    __available_variables = [
        {"api_name": "air.humidity.at-2m","human_name":"Surface Humidity","uom":"Percent" },
        {"api_name": "air.temperature.at-2m", "human_name": "Surface Temp", "uom": "Celcius"},
        {"api_name": "air.pressure.at-sea-level", "human_name": "QNH", "uom": "Hpa"},
        {"api_name": "air.visibility", "human_name": "Visibility", "uom": "Km"},
        {"api_name": "atmosphere.convective.potential.energy", "human_name": "CAPE", "uom": "joule Per Kilogram"},
        {"api_name": "cloud.base.height", "human_name": "Cloud Base", "uom": "feet"},
        {"api_name": "cloud.cover", "human_name": "Cloud Cover", "uom": "percent"},
        {"api_name": "precipitation.rate", "human_name": "Rain", "uom": "mm/hr"},
        {"api_name": "wind.direction.at-10m", "human_name": "Wind Direction", "uom": "degrees"},
        {"api_name": "wind.direction.at-100m", "human_name": "Wind Direction 300'", "uom": "degrees"},
        {"api_name": "wind.speed.at-10m", "human_name": "Wind Speed", "uom": "knots"},
        {"api_name": "wind.speed.at-100m", "human_name": "Wind Speed 300'", "uom": "knots"},
        {"api_name": "wind.speed.gust.at-10m", "human_name": "Gust", "uom": "knots"},
    ]

    class MetServiceException(Exception):
        pass

    def __init__(self,variables=[]):
        if len(variables) == 0:
            # self.__variables = ["air.temperature.at-2m",
            #          "air.pressure.at-sea-level",
            #          "cloud.base.height",
            #          "cloud.cover",
            #          "wind.direction.at-10m",
            #          "wind.speed.at-10m"]
            self.__variables = [v['api_name'] for v in self.__available_variables]
        else:
            self.__variables = variables
            self.__validate_variables_list(self.__variables)
        self.__current_values = {}
        self.__json = None
        self.__acct_login = ''
        self.__api_key = ''
        self.__api_units_used = 0
        self.__utc = []
        self.__local = []

    def __validate_variables_list(self,vlist):
        if not isinstance(vlist,list):
           raise self.MetServiceException("Passed variables is not a list")
        for v in vlist:
            if v not in [v['api_name'] for v in self.__available_variables]:
                raise self.MetServiceException("Invalid Variable in passed list")

    @property
    def AcctLogin(self):
        return self.__acct_login

    @AcctLogin.setter
    def AcctLogin(self,value):
        if value is None:
            raise self.MetServiceException('Login cannot be None')
        if not isinstance(value,str):
            raise self.MetServiceException('Login must be a string')
        self.__acct_login = value

    @property
    def ApiKey(self):
        return self.__api_key

    @ApiKey.setter
    def ApiKey(self,value):
        if value is None:
            raise self.MetServiceException('API Key cannot be None')
        if not isinstance(value,str):
            raise self.MetServiceException('API Key must be a string')
        self.__api_key = value

    @property
    def latitude(self):
        return self.__latitude

    @property
    def longitude(self):
        return self.__longitude

    @property
    def CurrentValues(self):
        return self.__current_values

    @property
    def wind_speed(self):
        return self.__current_values["wind.speed.at-10m"]

    @property
    def wind_direction(self):
        return self.__current_values["wind.direction.at-10m"]

    @property
    def wind_gust(self):
        return self.__current_values["wind.speed.gust.at-10m"]

    @property
    def cloud_base(self):
        return self.__current_values["cloud.base.height"]

    @property
    def visibility(self):
        return self.__current_values["air.visibility"]

    @property
    def humidity(self):
        return self.__current_values[ "air.humidity.at-2m"]

    @property
    def cape(self):
        return self.__current_values["atmosphere.convective.potential.energy"]

    @property
    def cloud_cover(self):
        return self.__current_values["cloud.cover"]

    @property
    def precipitation_rate(self):
        return self.__current_values["precipitation.rate"]

    @property
    def qnh(self):
        if  "air.pressure.at-sea-level" in self.__current_values:
            return self.__current_values[ "air.pressure.at-sea-level"]
        else:
            return 0


    @property
    def temperature(self):
        if  "air.temperature.at-2m" in self.__current_values:
            return self.__current_values["air.temperature.at-2m"]
        else:
            return 0

    def human_name(self,measure):
        thedict =  next((d for d in self.__available_variables if d['api_name'] == measure),None)
        if thedict:
            return thedict['human_name']
        else:
            return None

    def api_name(self,measure):
        thedict =  next((d for d in self.__available_variables if d['human_name'] == measure),None)
        if thedict:
            return thedict['api_name']
        else:
            return None


    def uom(self,measure):
        thedict =  next((d for d in self.__available_variables if d['api_name'] == measure),None)
        if thedict:
            return thedict['uom']
        else:
            return None
        #
        # if measure in ["air.humidity.at-2m","cloud.cover"]:
        #     return "percent"
        # elif measure in ["air.temperature.at-2m"]:
        #     return "celcius"
        # elif measure in ["air.pressure.at-sea-level"]:
        #     return "hpa"
        # elif measure in ["air.visibility"]:
        #     return "metres"
        # elif measure in ["atmosphere.convective.potential.energy"]:
        #     return "joule Per Kilogram"
        # elif measure in ["cloud.base.height"]:
        #     return "feet"
        # elif measure in ["precipitation.rate"]:
        #     return "mm per hr"
        # elif measure in ["wind.direction.at-10m","wind.direction.at-100m"]:
        #     return "degress"
        # elif measure in [
        #         "wind.speed.at-10m",
        #         "wind.speed.at-100m",
        #         "wind.speed.gust.at-10m"]:
        #     return "knots"



    @property
    def ForecastTimeUtc(self):
        return self.__utc

    @property
    def ForecastTimeLocal(self):
        return self.__local

    @property
    def APIUnitsUsed(self):
        return self.__api_units_used


    def get_current(self,longitude,latitude, savefilename=None,interval=1,reading_count=0):  # eg. 174.7842 -37.7935
        # validate:
        if longitude is None:
            raise self.MetServiceException("Longitude cannot be None")
        if type(longitude) not in [int,float]:
            raise self.MetServiceException("Longitude is not a number")
        if longitude < 165 or longitude > 178:
            raise self.MetServiceException("Longitude must be between 165 and 178 for NZ")
        if latitude is None:
            raise self.MetServiceException("latitude cannot be None")
        if type(latitude) not in [int,float]:
            raise self.MetServiceException("latitude is not a number")
        if latitude > -34 or latitude <  -48:
            raise self.MetServiceException("latitude must be between -34 and -38 for NZ")
        if savefilename is not None:
            if not isinstance(savefilename,str):
                raise self.MetServiceException("Save file name must be a string if sepcified")
        if type(interval) not in [int, float]:
            raise self.MetServiceException("Hours from now must be a number ({} is {})".format(interval,type(interval)))
        if type(reading_count) not in [int]:
            raise self.MetServiceException("Hours from now must be a number ({} is {})".format(reading_count,type(reading_count)))
        if reading_count < 0 or reading_count > 24:
            raise self.MetServiceException("Reading count must be between 0 and 24")

        resp = post(
            "https://forecast-v2.metoceanapi.com/point/time",
            headers={"x-api-key": self.ApiKey},
            json={
                "points": [{
                    "lon": longitude,
                    "lat": latitude
                }],
                "variables": self.__variables,
                "time": {
                    "from": "{:%Y-%m-%dT%H:%M:%SZ}".format(datetime.utcnow()),
                    "interval": "{:.0f}h".format(interval),
                    "repeat": reading_count - 1 #0
                }
            }
        )

        if resp.status_code != 200:
            raise self.MetServiceException("{}: {}".format(resp.status_code, resp.text))

        self.__api_units_used += len(self.__variables)

        if savefilename is not None:
            with open(savefilename, 'w') as outfile:
                outfile.write(
                    json.dumps(resp.json(), default=str, indent=2, sort_keys=True)
                )
        # self.__json = json.loads(resp.text)
        self.__json = resp.json()
        self.__extract_json(interval)
        #
        # print(json.dumps(resp.json(), indent=1))

    def get_current_file(self, filename,interval=1):  # eg. 174.7842 -37.7935
        # USe this for debugging....
        # You will first need to call get_current and save the file somewhere,
        # then use this to open the file and process it as if it were retreived by the API
        # Savees using up valuable API calls.
        f = open(filename)
        self.__json = json.load(f)
        self.__extract_json(interval)
        #

    def debug(self):
        self.__extract_json()

    def __extract_json(self,hoursfromnow=None):
        if self.__json is None:
            raise self.MetServiceException('No Json to extract')
            # debugging..... find the json
            # f = open("/tmp/metservice.json")
            # self.__json = json.load(f)
        # The json is just a dictionary

        # here is the main bit...
        # self.__variables is the list of variables that we have asked for.
        self.__longitude = float(self.__json['dimensions']['point']['data'][0]['lon'])
        self.__latitude = float(self.__json['dimensions']['point']['data'][0]['lat'])
        utczone = tz.gettz('UTC')
        to_zone = tz.gettz('Pacific/Auckland')
        self.__utc=[]
        for d in self.__json['dimensions']['time']['data']:
            thisdate = datetime.strptime(d,'%Y-%m-%dT%H:%M:%SZ')
            thisdate.replace(tzinfo=utczone)
            self.__utc.append(thisdate)
            self.__local.append(pytz.utc.localize(thisdate).astimezone(to_zone))
        #     self.__utc.append(datetime.strptime(self.__json['dimensions']['time']['data'][0], '%Y-%m-%dT%H:%M:%SZ')
        # self.__utc = self.__utc.replace(tzinfo=utczone)
        # if type(hoursfromnow) in [int,float]:
        #     self.__utc = self.__utc + timedelta(hours=hoursfromnow)
        # self.__local = self.__utc.astimezone(to_zone)
        for v in self.__variables:
            # if a variable exists in the returning data from json
            if v in self.__json['variables']:
                # then add a dictionary item to the dict of current values:
                thislist = []
                for onevalue in self.__json['variables'][v]['data']:
                    # if onevalue.isnull:
                    #     thislist.append(0)
                    # else:
                    if onevalue is None:
                        thislist.append(0)
                    else:
                        thislist.append(onevalue)
                self.__current_values[v] = thislist
                # if self.__current_values[v] is None:
                #     self.__current_values[v] = 0
        #
        # # temp conversions
        for v in ["air.temperature.at-2m" ]:
            if self.__current_values.get(v):
                newlist = []
                for onevalue in self.__current_values[v]:
                    newlist.append(self.celcius(onevalue))
                self.__current_values[v] = newlist
        # # PRessure conversion
        for v  in ["air.pressure.at-sea-level"]:
            if self.__current_values.get(v):
                newlist = []
                for onevalue in self.__current_values[v]:
                    newlist.append(self.hpa(onevalue))
                self.__current_values[v] = newlist
        # # height conversions
        for v in ["cloud.base.height"]:
            if self.__current_values.get(v):
                newlist = []
                for onevalue in self.__current_values[v]:
                    newlist.append(self.feet(onevalue))
                self.__current_values[v] = newlist
        # # Distance Conversions
        for v in ["air.visibility"]:
            if self.__current_values.get(v):
                newlist = []
                for onevalue in self.__current_values[v]:
                    newlist.append(round(onevalue /1000,1))
                self.__current_values[v] = newlist
        #     if v in self.__current_values:
        #         self.__current_values[v] = round(self.__current_values[v] / 1000,1)
        # # Speed Conversions
        for v in ["wind.speed.at-10m",
                 "wind.speed.at-100m",
                 "wind.speed.gust.at-10m"]:
            if self.__current_values.get(v):
                newlist = []
                for onevalue in self.__current_values[v]:
                    newlist.append(self.knots(onevalue))
                self.__current_values[v] = newlist
        for v in ["cloud.cover",
                "precipitation.rate",
                "wind.direction.at-10m"]:
            if self.__current_values.get(v):
                newlist = []
                for onevalue in self.__current_values[v]:
                    newlist.append(round(onevalue,0))
                self.__current_values[v] = newlist

    @staticmethod
    def celcius(kelvin):
        return round(kelvin-273.15,1)

    @staticmethod
    def feet(metres):
        return round(metres * 3.28084,0)

    @staticmethod
    def knots(metrespersecond):
        return round(metrespersecond * 1.94384,0)

    @staticmethod
    def hpa(pa):
        return round(pa/100,1)

    @staticmethod
    def inmercury(pa):
        return pa / 3386.39




