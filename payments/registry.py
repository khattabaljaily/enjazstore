from .gateways import BankTransferGateway

GATEWAYS = {
    BankTransferGateway.code: BankTransferGateway,
}

DEFAULT_GATEWAY = BankTransferGateway.code


def get_gateway(code=DEFAULT_GATEWAY):
    try:
        gateway_class = GATEWAYS[code]
    except KeyError:
        raise ValueError(f'Unknown payment gateway: {code}')
    return gateway_class()
