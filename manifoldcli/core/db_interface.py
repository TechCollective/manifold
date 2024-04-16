from abc import abstractmethod
from cement import Interface

class DBInterface(Interface):
    class Meta:
        interface = 'db_interface'

    @abstractmethod
    def add(self, device_obj):
        pass

    @abstractmethod
    def delete(self, device_obj):
        pass

    @abstractmethod
    def update(self, device_obj):
        pass

    @abstractmethod
    def run_hook(self, obj, source):
        pass
