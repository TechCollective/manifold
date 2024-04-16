import json
import pprint
import six
from datetime import datetime, timedelta

class AlertObject:
    swagger_types = {
        'alert_type': 'str',
        'source_db': 'str',
        'start_timestamp': 'str',
        'last_timestamp': 'str',
        'devices': 'list[DeviceObject]',
        'company_db': 'DeviceObject',
        'title_append': 'str',
        'useful_information': 'str'
    }
   
    attribute_map = {
        'alert_type': 'id',
        'source_db': 'id',
        'start_timestamp': 'str',
        'last_timestamp': 'str',
        'devices': 'DeviceObject',
        'company_db': 'CompanyObject',
        'title_append': 'str',
        'useful_information': 'str',
   }
    def __init__(self, alert_type=None, source_db=None, start_timestamp=None, last_timestamp=None, devices=None, company_db=None, title_append=None, useful_information=None ):
        self._alert_type = None
        self._source_db = None
        self._start_timestamp = None
        self._last_timestamp = None
        self._devices = None
        self._company_db = None
        self._title_append = None
        self._useful_information = None
        
        if alert_type is not None:
            self.alert_type = alert_type
        if source_db is not None:
            self.source_db = source_db
        if start_timestamp is not None:
            self.start_timestamp = start_timestamp
        if last_timestamp is not None:
            self.last_timestamp = last_timestamp
        if devices is not None:
            self.devices = devices
        if company_db is not None:
            self._company_db = company_db
        if title_append is not None:
            self._title_append = title_append
        if useful_information is not None:
            self._useful_information = useful_information

    @property
    def alert_type(self):
        return self._alert_type
    
    @alert_type.setter
    def alert_type(self, alert_type):
        self._alert_type = alert_type

    @property
    def source_db(self):
        return self._source_db
    
    @source_db.setter
    def source_db(self, source_db):
        self._source_db = source_db

    @property
    def start_timestamp(self):
        return self._start_timestamp
    
    @start_timestamp.setter
    def start_timestamp(self, start_timestamp):
        self._start_timestamp = start_timestamp

    @property
    def last_timestamp(self):
        return self._last_timestamp
    
    @last_timestamp.setter
    def last_timestamp(self, last_timestamp):
        self._last_timestamp = last_timestamp

    @property
    def devices(self):
        return self._devices
    
    @devices.setter
    def devices(self, devices):
        self._devices = devices

    @property
    def company_db(self):
        return self._company_db
    
    @company_db.setter
    def company_db(self, company_db):
        self._company = company_db

    @property
    def title_append(self):
        return self._title_append
    
    @title_append.setter
    def title_append(self, title_append):
        self._title_append = title_append

    @property
    def useful_information(self):
        return self._useful_information
    
    @useful_information.setter
    def useful_information(self,useful_information):
        self._useful_information = useful_information

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(AlertObject, dict):
            for key, value in self.items():
                result[key] = value

        return result


    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())
