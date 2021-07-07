MAX_DIGITS = len(str(2 ** 256))

#DUCATUS_USD_RATE = 0.06

DECIMALS = {
    'ETH': 10 ** 18,
    'BTC': 10 ** 8,
    'DUC': 10 ** 8,
    'DUCX': 10 ** 18,
    'USDC': 10 ** 6,

    # quantum currencies
    'USD': 10 ** 2,
    'EUR': 10 ** 2,
    'GBP': 10 ** 2,
    'CHF': 10 ** 2,
}

TICKETS_FOR_USD = {
    10: 1,
    50: 6,
    100: 13,
    500: 70,
    1000: 150,
}

BONUSES_FOR_TICKETS = {
    1: {
        'back_office_bonus': 5,
        'e_commerce_bonus': 5,
    },
    6: {
        'back_office_bonus': 8,
        'e_commerce_bonus': 8,
    },
    13: {
        'back_office_bonus': 13,
        'e_commerce_bonus': 13,
    },
    70: {
        'back_office_bonus': 21,
        'e_commerce_bonus': 21,
    },
    150: {
        'back_office_bonus': 34,
        'e_commerce_bonus': 34,
    }
}

DIVIDENDS_INFO = {
    5: 8,
    13: 13,
    34: 21,
}

RATES_PRECISION = 0.97

DAYLY_LIMIT = 25000 * DECIMALS['DUC']
WEEKLY_LIMIT = 100000 * DECIMALS['DUC']
