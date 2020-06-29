from abc import ABC, abstractmethod

class Exchange(ABC):
    def __init__(self):
        self.name = 'BaseExchange'
    
    @abstractmethod
    def get_historical_value(self, stock, start, end):
        pass
