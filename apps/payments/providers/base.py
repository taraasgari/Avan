from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentStartResult:
    reference: str
    redirect_url: str


class PaymentProvider(ABC):
    """Gateway contract. Checkout logic must depend on this interface, never one vendor SDK."""

    @abstractmethod
    def start(self, *, amount: int, order_id: str, callback_url: str) -> PaymentStartResult:
        raise NotImplementedError

    @abstractmethod
    def verify(self, *, reference: str, amount: int) -> bool:
        raise NotImplementedError
