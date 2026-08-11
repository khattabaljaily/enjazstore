from abc import ABC, abstractmethod

from .models import Payment


class PaymentGatewayError(Exception):
    """Raised when a gateway can't be reached, or rejects a request."""


class BasePaymentGateway(ABC):
    """Contract every payment gateway must implement.

    Order and cart logic only ever talk to this interface, never to a
    concrete gateway, so a different gateway can be dropped in later without
    touching the rest of the codebase.
    """

    code = None
    label = None

    # Gateways that send the customer to a hosted payment page set this so
    # the checkout view redirects there instead of going straight to the
    # confirmation page.
    redirect_required = False

    @abstractmethod
    def initiate_payment(self, order) -> Payment:
        """Create (or return) the Payment record for an order."""
        raise NotImplementedError

    @abstractmethod
    def verify_payment(self, payment: Payment) -> bool:
        """Confirm whether a payment has actually gone through."""
        raise NotImplementedError


class BankTransferGateway(BasePaymentGateway):
    """Manual bank transfer — Bank of Khartoum, via the Bankak app.

    The customer transfers the order total themselves and uploads a receipt
    screenshot at checkout (see Payment.receipt_image). That leaves the
    Payment PENDING until a staff member reviews the receipt in the
    dashboard and confirms it — verify_payment() is only ever called from
    that dashboard action, never automatically.
    """

    code = 'bank_transfer'
    label = 'تحويل بنكي'

    def initiate_payment(self, order) -> Payment:
        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={
                'amount': order.total,
                'gateway': self.code,
                'status': Payment.Status.PENDING,
            },
        )
        return payment

    def verify_payment(self, payment: Payment) -> bool:
        payment.status = Payment.Status.PAID
        payment.save(update_fields=['status', 'updated_at'])
        return True
