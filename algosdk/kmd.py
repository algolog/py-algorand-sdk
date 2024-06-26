import base64
import json
from typing import Any
import urllib.error
from urllib import parse
from urllib.request import Request, urlopen

from . import constants, encoding, error, transaction

api_version_path_prefix = "/v1"


class KMDClient:
    """
    Client class for kmd. Handles all kmd requests.

    Args:
        kmd_token (str): kmd API token
        kmd_address (str): kmd address

    Attributes:
        kmd_token (str)
        kmd_address (str)
    """

    def __init__(self, kmd_token, kmd_address):
        self.kmd_token = kmd_token
        self.kmd_address = kmd_address

    def kmd_request(self, method, requrl, params=None, data=None, timeout=30):
        """
        Execute a given request.

        Args:
            method (str): request method
            requrl (str): url for the request
            params (dict, optional): parameters for the request
            data (dict, optional): data in the body of the request
            timeout (int, optional): request timeout in seconds

        Returns:
            dict: loaded from json response body
        """
        if requrl in constants.no_auth:
            header = {}
        else:
            header = {constants.kmd_auth_header: self.kmd_token}

        if requrl not in constants.unversioned_paths:
            requrl = api_version_path_prefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)
        if data:
            data = json.dumps(data, indent=2)
            data = bytearray(data, "utf-8")
        req = Request(
            self.kmd_address + requrl, headers=header, method=method, data=data
        )
        resp = None
        try:
            resp = urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            e = e.read().decode("utf-8")
            try:
                raise error.KMDHTTPError(json.loads(e)["message"])
            except:
                raise error.KMDHTTPError(e)
        return json.loads(resp.read().decode("utf-8"))

    def versions(self, **kwargs: Any):
        """
        Get kmd versions.

        Returns:
            str[]: list of versions
        """
        req = "/versions"
        return self.kmd_request("GET", req, **kwargs)["versions"]

    def list_wallets(self, **kwargs: Any):
        """
        List all wallets hosted on node.

        Returns:
            dict[]: list of dictionaries containing wallet information
        """
        req = "/wallets"
        res = self.kmd_request("GET", req, **kwargs)
        if "wallets" in res:
            return res["wallets"]
        else:
            return []

    def create_wallet(
        self,
        name,
        pswd,
        driver_name="sqlite",
        master_deriv_key=None,
        **kwargs: Any
    ):
        """
        Create a new wallet.

        Args:
            name (str): wallet name
            pswd (str): wallet password
            driver_name (str, optional): name of the driver
            master_deriv_key (str, optional): if recovering a wallet, include

        Returns:
            dict: dictionary containing wallet information
        """
        req = "/wallet"
        query = {
            "wallet_driver_name": driver_name,
            "wallet_name": name,
            "wallet_password": pswd,
        }
        if master_deriv_key:
            query["master_derivation_key"] = master_deriv_key
        return self.kmd_request("POST", req, data=query, **kwargs)["wallet"]

    def get_wallet(self, handle, **kwargs: Any):
        """
        Get wallet information.

        Args:
            handle (str): wallet handle token

        Returns:
            dict: dictionary containing wallet handle and wallet information
        """
        req = "/wallet/info"
        query = {"wallet_handle_token": handle}
        return self.kmd_request("POST", req, data=query, **kwargs)[
            "wallet_handle"
        ]

    def init_wallet_handle(self, id, password, **kwargs: Any):
        """
        Initialize a handle for the wallet.

        Args:
            id (str): wallet ID
            password (str): wallet password

        Returns:
            str: wallet handle token
        """
        req = "/wallet/init"
        query = {"wallet_id": id, "wallet_password": password}
        return self.kmd_request("POST", req, data=query, **kwargs)[
            "wallet_handle_token"
        ]

    def release_wallet_handle(self, handle, **kwargs: Any):
        """
        Deactivate the handle for the wallet.

        Args:
        handle (str): wallet handle token

        Returns:
            bool: True if the handle has been deactivated
        """
        req = "/wallet/release"
        query = {"wallet_handle_token": handle}
        result = self.kmd_request("POST", req, data=query, **kwargs)
        return result == {}

    def renew_wallet_handle(self, handle, **kwargs: Any):
        """
        Renew the wallet handle.

        Args:
            handle (str): wallet handle token

        Returns:
            dict: dictionary containing wallet handle and wallet information
        """
        req = "/wallet/renew"
        query = {"wallet_handle_token": handle}
        return self.kmd_request("POST", req, data=query, **kwargs)[
            "wallet_handle"
        ]

    def rename_wallet(self, id, password, new_name, **kwargs: Any):
        """
        Rename the wallet.

        Args:
            id (str): wallet ID
            password (str): wallet password
            new_name (str): new name for the wallet

        Returns:
            dict: dictionary containing wallet information
        """
        req = "/wallet/rename"
        query = {
            "wallet_id": id,
            "wallet_password": password,
            "wallet_name": new_name,
        }
        return self.kmd_request("POST", req, data=query, **kwargs)["wallet"]

    def export_master_derivation_key(self, handle, password, **kwargs: Any):
        """
        Get the wallet's master derivation key.

        Args:
            handle (str): wallet handle token
            password (str): wallet password

        Returns:
            str: master derivation key
        """
        req = "/master-key/export"
        query = {"wallet_handle_token": handle, "wallet_password": password}
        result = self.kmd_request("POST", req, data=query, **kwargs)
        return result["master_derivation_key"]

    def import_key(self, handle, private_key, **kwargs: Any):
        """
        Import an account into the wallet.

        Args:
            handle (str): wallet handle token
            private_key (str): private key of account to be imported

        Returns:
            str: base32 address of the account
        """
        req = "/key/import"
        query = {"wallet_handle_token": handle, "private_key": private_key}
        return self.kmd_request("POST", req, data=query, **kwargs)["address"]

    def export_key(self, handle, password, address, **kwargs: Any):
        """
        Return an account private key.

        Args:
            handle (str): wallet handle token
            password (str): wallet password
            address (str): base32 address of the account

        Returns:
            str: private key
        """
        req = "/key/export"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "address": address,
        }
        return self.kmd_request("POST", req, data=query, **kwargs)[
            "private_key"
        ]

    def generate_key(self, handle, display_mnemonic=True, **kwargs: Any):
        """
        Generate a key in the wallet.

        Args:
            handle (str): wallet handle token
            display_mnemonic (bool, optional): whether or not the mnemonic
                should be displayed

        Returns:
            str: base32 address of the generated account
        """
        req = "/key"
        query = {"wallet_handle_token": handle}
        return self.kmd_request("POST", req, data=query, **kwargs)["address"]

    def delete_key(self, handle, password, address, **kwargs: Any):
        """
        Delete a key in the wallet.

        Args:
            handle (str): wallet handle token
            password (str): wallet password
            address (str): base32 address of account to be deleted

        Returns:
            bool: True if the account has been deleted
        """
        req = "/key"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "address": address,
        }
        result = self.kmd_request("DELETE", req, data=query, **kwargs)
        return result == {}

    def list_keys(self, handle, **kwargs: Any):
        """
        List all keys in the wallet.

        Args:
            handle (str): wallet handle token

        Returns:
            str[]: list of base32 addresses in the wallet
        """
        req = "/key/list"
        query = {"wallet_handle_token": handle}

        result = self.kmd_request("POST", req, data=query, **kwargs)
        if result:
            return result["addresses"]
        return []

    def sign_transaction(
        self, handle, password, txn, signing_address=None, **kwargs: Any
    ):
        """
        Sign a transaction.

        Args:
            handle (str): wallet handle token
            password (str): wallet password
            txn (Transaction): transaction to be signed
            signing_address (str, optional): sign the transaction with SK corresponding to base32
                signing_address, if provided, rather than SK corresponding to sender

        Returns:
            SignedTransaction: signed transaction with signature of sender
        """
        txn = encoding.msgpack_encode(txn)
        req = "/transaction/sign"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "transaction": txn,
        }
        if signing_address:
            query["public_key"] = signing_address
        result = self.kmd_request("POST", req, data=query, **kwargs)
        result = result["signed_transaction"]
        return encoding.msgpack_decode(result)

    def list_multisig(self, handle, **kwargs: Any):
        """
        List all multisig accounts in the wallet.

        Args:
            handle (str): wallet handle token

        Returns:
            str[]: list of base32 multisig account addresses
        """
        req = "/multisig/list"
        query = {"wallet_handle_token": handle}
        result = self.kmd_request("POST", req, data=query, **kwargs)
        if result == {}:
            return []
        return result["addresses"]

    def import_multisig(self, handle, multisig, **kwargs: Any):
        """
        Import a multisig account into the wallet.

        Args:
            handle (str): wallet handle token
            multisig (Multisig): multisig account to be imported

        Returns:
            str: base32 address of the imported multisig account
        """
        req = "/multisig/import"
        query = {
            "wallet_handle_token": handle,
            "multisig_version": multisig.version,
            "threshold": multisig.threshold,
            "pks": [
                base64.b64encode(s.public_key).decode()
                for s in multisig.subsigs
            ],
        }
        return self.kmd_request("POST", req, data=query, **kwargs)["address"]

    def export_multisig(self, handle, address, **kwargs: Any):
        """
        Export a multisig account.

        Args:
            handle (str): wallet token handle
            address (str): base32 address of the multisig account

        Returns:
            Multisig: multisig object corresponding to the address
        """
        req = "/multisig/export"
        query = {"wallet_handle_token": handle, "address": address}
        result = self.kmd_request("POST", req, data=query, **kwargs)
        pks = result["pks"]
        pks = [encoding.encode_address(base64.b64decode(p)) for p in pks]
        msig = transaction.Multisig(
            result["multisig_version"], result["threshold"], pks
        )
        return msig

    def delete_multisig(self, handle, password, address, **kwargs: Any):
        """
        Delete a multisig account.

        Args:
            handle (str): wallet handle token
            password (str): wallet password
            address (str): base32 address of the multisig account to delete

        Returns:
            bool: True if the multisig account has been deleted
        """
        req = "/multisig"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "address": address,
        }
        result = self.kmd_request("DELETE", req, data=query, **kwargs)
        return result == {}

    def sign_multisig_transaction(
        self, handle, password, public_key, mtx, **kwargs: Any
    ):
        """
        Sign a multisig transaction for the given public key.

        Args:
            handle (str): wallet handle token
            password (str): wallet password
            public_key (str): base32 address that is signing the transaction
            mtx (MultisigTransaction): multisig transaction containing
                unsigned or partially signed multisig

        Returns:
            MultisigTransaction: multisig transaction with added signature
        """
        partial = mtx.multisig.json_dictify()
        txn = encoding.msgpack_encode(mtx.transaction)
        public_key = base64.b64encode(encoding.decode_address(public_key))
        public_key = public_key.decode()
        req = "/multisig/sign"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "transaction": txn,
            "public_key": public_key,
            "partial_multisig": partial,
        }

        if hasattr(mtx, "auth_addr") and mtx.auth_addr is not None:
            signer = base64.b64encode(encoding.decode_address(mtx.auth_addr))
            query["signer"] = signer.decode()

        result = self.kmd_request("POST", req, data=query, **kwargs)[
            "multisig"
        ]
        msig = encoding.msgpack_decode(result)
        mtx.multisig = msig
        return mtx
