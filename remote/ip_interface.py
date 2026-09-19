from abc import ABC, abstractmethod
from typing import Tuple


class IpLocationLookup(ABC):
    @abstractmethod
    def lookup_location(ips: list[str]) -> dict[str, Tuple[float, float]]:
        pass
