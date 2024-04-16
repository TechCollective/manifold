import pprint
import re  # noqa: F401
import six

class MacAddressObject(object):
    swagger_types = {
        'mac_address': 'str'
    }

    def __init__(self, mac_address=None):
        self._mac_address = None
    
        if mac_address is not None:
            self.mac_address = mac_address
    
    @property
    def mac_address(self):
        return self._mac_address
    @mac_address.setter
    def mac_address(self, mac_address):
        self._mac_address = mac_address

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
        if issubclass(MacAddressObject, dict):
            for key, value in self.items():
                result[key] = value

        return result 

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, MacAddressObject):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other

class MacAddressListObject(object):
    swagger_types = {
        'results': 'list[MacAddress]',
        'total_count': 'int'
    }

    def __init__(self, results=None, total_count=None):
        self._results = None
        self._total_count = None

        if results is not None:
            self.results = results
        if total_count is not None:
            self.total_count = total_count

    @property
    def results(self):
        return self._results

    @results.setter
    def results(self, results):
        self._results = results
        self._total_count = len(results)

    @property
    def total_count(self):
        return self._total_count

    @total_count.setter
    def total_count(self, total_count):
        self._total_count = total_count

    def add_result(self, mac_address):
        self._results.append(mac_address)
        self._total_count = len(self._results)

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
        if issubclass(MacAddressListObject, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, MacAddressListObject):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other

class IPAddressObject(object):
    swagger_types = {
        'ip_address': 'str'
    }

    def __init__(self, ip_address=None):
        self._ip_address = None
    
        if ip_address is not None:
            self.ip_address = ip_address
    
    @property
    def ip_address(self):
        return self._ip_address
    @ip_address.setter
    def ip_address(self, ip_address):
        self._ip_address = ip_address

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
        if issubclass(IPAddressObject, dict):
            for key, value in self.items():
                result[key] = value

        return result 

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, IPAddressObject):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other

class IPAddressListObject(object):
    swagger_types = {
        'results': 'list[IPAddress]',
        'total_count': 'int'
    }

    def __init__(self, results=None, total_count=None):
        self._results = None
        self._total_count = None

        if results is not None:
            self.results = results
        if total_count is not None:
            self.total_count = total_count

    @property
    def results(self):
        return self._results
    @results.setter
    def results(self, results):
        self._results = results

    @property
    def total_count(self):
        return self._total_count

    @total_count.setter
    def total_count(self, total_count):
        self._total_count = total_count

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
        if issubclass(IPAddressListObject, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, IPAddressListObject):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other

class DeviceObject(object):
    swagger_types = {
        'name': 'str', 
        'description': 'str',
        'serial': 'str',
        'manufacturer': 'str',
        'model': 'str',
        'install_date': 'str',
        'ip_address': 'list[IPAddress]',
        'mac_address': 'list[MacAddress]',
        'company': 'str'
    }

    def __init__(self, name=None, description=None, serial=None, manufacturer=None, model=None, install_date=None, ip_address=None, mac_address=None, company=None):
        self._name = None
        self._description = None
        self._serial = None
        self._manufacturer = None
        self._model = None
        self._install_date = None
        self._ip_address = None
        self._mac_address = None
        self._company = None

        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if serial is not None:
            self.serial = serial    
        if manufacturer is not None:
            self.manufacturer = manufacturer 
        if model is not None:
            self.model = model    
        if install_date is not None:
            self.install_date = install_date
        if ip_address is not None:
            self.ip_address = ip_address
        if mac_address is not None:
            self.mac_address = mac_address
        if company is not None:
            self.company = company

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, name):
        self._name = name
    
    @property
    def description(self):
        return self._description
    @description.setter
    def description(self, description):
        self._description = description

    @property
    def serial(self):
        return self._serial
    @serial.setter
    def serial(self, serial):
        self._serial = serial

    @property
    def manufacturer(self):
        return self._manufacturer
    @manufacturer.setter
    def manufacturer(self, manufacturer):
        self._manufacturer = manufacturer

    @property
    def model(self):
        return self._model
    @model.setter
    def model(self, model):
        self._model = model

    @property
    def install_date(self):
        return self._install_date
    @install_date.setter
    def install_date(self, install_date):
        self._install_date = install_date

    @property
    def ip_address(self):
        return self._ip_address
    @ip_address.setter
    def ip_address(self, ip_address):
        self._ip_address = ip_address

    @property
    def mac_address(self):
        return self._mac_address
    @mac_address.setter
    def mac_address(self, mac_address):
        self._mac_address = mac_address

    @property
    def company(self):
        return self._company
    @company.setter
    def company(self, company):
        self._company = company

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
        if issubclass(DeviceObject, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, DeviceObject):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other