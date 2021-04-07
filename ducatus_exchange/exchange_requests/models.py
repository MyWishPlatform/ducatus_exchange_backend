from bip32utils import BIP32Key
from eth_keys import keys

from django.db import models
from django.contrib.auth.models import User

from ducatus_exchange.consts import MAX_DIGITS
from ducatus_exchange.settings import ROOT_KEYS, BITCOIN_URLS, IS_TESTNET_PAYMENTS
from ducatus_exchange.exchange_requests.api import get_root_key, registration_btc_address
from ducatus_exchange.bip32_ducatus import DucatusWallet


class DucatusUser(models.Model):
    address = models.CharField(max_length=50, unique=False)
    platform = models.CharField(max_length=25, null=True, default=None)
    email = models.CharField(max_length=50, null=True, default=None)
    ref_address = models.CharField(max_length=50, null=True, default=None)


class ExchangeRequest(models.Model):
    user = models.ForeignKey(DucatusUser, on_delete=models.CASCADE, null=True)
    duc_address = models.CharField(max_length=50, null=True, default=None)
    ducx_address = models.CharField(max_length=50, null=True, default=None)
    btc_address = models.CharField(max_length=50, null=True, default=None)
    eth_address = models.CharField(max_length=50, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    dayly_swap = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0, default=0)
    weekly_swap = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0, default=0)

    def generate_keys(self):
        eth_btc_root_pub_key = get_root_key()
        eth_btc_root_key = BIP32Key.fromExtendedKey(eth_btc_root_pub_key, public=True)
        eth_btc_child_key = eth_btc_root_key.ChildKey(self.user.id)
        btc_address = eth_btc_child_key.Address()
        registration_btc_address(btc_address)
        eth_address = keys.PublicKey(eth_btc_child_key.K.to_string()).to_checksum_address().lower()

        duc_root_key = DucatusWallet.deserialize(ROOT_KEYS['ducatus']['public'])
        duc_address = duc_root_key.get_child(self.user.id, is_prime=False).to_address()

        ducx_root_pub_key = ROOT_KEYS['ducatusx']['public']
        ducx_root_key = BIP32Key.fromExtendedKey(ducx_root_pub_key, public=True)
        ducx_child_key = ducx_root_key.ChildKey(self.user.id)
        ducx_address = keys.PublicKey(ducx_child_key.K.to_string()).to_checksum_address().lower()

        self.btc_address = btc_address
        self.eth_address = eth_address
        self.duc_address = duc_address
        self.ducx_address = ducx_address

        self.save()



class Status(models.TextChoices):
    ENABLED = 'Enabled'
    DISABLED = 'Disabled'

class ExchangeStatus(models.Model):
    status = models.CharField(max_length=20, choices=Status.choices)
    updated_at = models.DateTimeField(auto_now_add=True)