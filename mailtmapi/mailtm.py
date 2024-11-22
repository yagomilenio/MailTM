import json
import logging

from aiohttp import ClientSession

from .schemas.account import Account, Token
from .schemas.domains import Domains, Domain
from .schemas.message import Messages, OneMessage, MessageSource
from .utils.exceptions import MailTMInvalidResponse
from .utils.misc import random_string, validate_response

logger = logging.getLogger('mailtm')


class MailTM:
    API_URL = "https://api.mail.tm"
    SSL = False

    def __init__(self, session: ClientSession = None):
        self.session = session or ClientSession()

    async def get_account_token(self, address: str, password: str) -> Token:
        """
        https://docs.mail.tm/#authentication
        """
        headers = {
            "accept": "application/ld+json",
            "Content-Type": "application/json"
        }
        response = await self.session.post(f"{self.API_URL}/token", data=json.dumps({
            "address": address,
            "password": password
        }), headers=headers, ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/token: {response}')
        if await validate_response(response):
            return Token(**(await response.json()))
        logger.debug(f'Error response for {self.API_URL}/token: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/token", await response.json())

    async def get_domains(self) -> Domains:
        """
        https://docs.mail.tm/#get-domains
        """
        response = await self.session.get(f"{self.API_URL}/domains", ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/domains: {response}')
        if await validate_response(response):
            return Domains(**(await response.json()))
        logger.debug(f'Error response for {self.API_URL}/domains: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/domains", await response.json())

    async def get_domain(self, domain_id: str) -> Domain:
        """
        https://docs.mail.tm/#get-domainsid
        """
        response = await self.session.get(f"{self.API_URL}/domains/{domain_id}", ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/domains/{domain_id}: {response}')
        if await validate_response(response):
            return Domain(**(await response.json()))
        logger.debug(f'Error response for {self.API_URL}/domains/{domain_id}: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/domains/{domain_id}",
                                    await response.json())

    async def get_account(self, address: str = None, password: str = None) -> Account:
        """
        https://docs.mail.tm/#post-accounts
        """
        if address is None:
            domain = (await self.get_domains()).hydra_member[0].domain
            address = f"{random_string()}@{domain}"
        if password is None:
            password = random_string()
        payload = {
            "address": address,
            "password": password
        }
        logger.debug(f'Create account with payload: {payload}')
        response = await self.session.post(f"{self.API_URL}/accounts", json=payload, ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/accounts: {response}')
        if await validate_response(response):
            response = await response.json()
            token = await self.get_account_token(address=address, password=password)
            response['token'] = token
            return Account(**response)
        logger.debug(f'Error response for {self.API_URL}/accounts: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/accounts", await response.json())

    async def get_account_by_id(self, account_id: str, token: str) -> Account:
        """
        https://docs.mail.tm/#get-accountsid
        """
        response = await self.session.get(f"{self.API_URL}/accounts/{account_id}",
                                          headers={"Authorization": f"Bearer {token}"},
                                          ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/accounts/{account_id}: {response}')
        if await validate_response(response):
            data = await response.json()
            if 'token' not in data:
                data['token'] = Token(**({'id': account_id, 'token': token}))
            return Account(**data)
        logger.debug(f'Error response for {self.API_URL}/accounts/{account_id}: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/accounts/{account_id}",
                                    await response.json())

    async def delete_account_by_id(self, account_id: str, token: str) -> bool:
        """
        https://docs.mail.tm/#delete-accountsid
        """
        response = await self.session.delete(f"{self.API_URL}/accounts/{account_id}",
                                             headers={'Authorization': f'Bearer {token}'},
                                             ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/accounts/{account_id}: {response}')
        if await validate_response(response):
            return response.status == 204
        logger.debug(f'Error response for {self.API_URL}/accounts/{account_id}: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/accounts/{account_id}",
                                    await response.json())

    async def get_me(self, token: str) -> Account:
        """
        https://docs.mail.tm/#get-me
        """
        response = await self.session.get(f"{self.API_URL}/me",
                                          headers={'Authorization': f'Bearer {token}'},
                                          ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/me: {response}')
        if await validate_response(response):
            data = await response.json()
            if 'token' not in data:
                data['token'] = Token(**({'id': data['id'], 'token': token}))
            return Account(**data)
        logger.debug(f'Error response for {self.API_URL}/me: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/me", await response.json())

    async def get_messages(self, token: str, page: int = 1) -> Messages:
        """
        https://docs.mail.tm/#get-messages
        """
        response = await self.session.get(f"{self.API_URL}/messages?page={page}",
                                          headers={'Authorization': f'Bearer {token}'},
                                          ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/messages: {response}')
        if await validate_response(response):
            return Messages(**(await response.json()))
        logger.debug(f'Error response for {self.API_URL}/messages: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/messages", await response.json())

    async def get_message_by_id(self, message_id: str, token: str) -> OneMessage:
        """
        https://docs.mail.tm/#get-messagesid
        """
        response = await self.session.get(f"{self.API_URL}/messages/{message_id}",
                                          headers={'Authorization': f'Bearer {token}'},
                                          ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/messages/{message_id}: {response}')
        if await validate_response(response):
            return OneMessage(**(await response.json()))
        logger.debug(f'Error response for {self.API_URL}/messages/{message_id}: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/messages/{message_id}",
                                    await response.json())

    async def delete_message_by_id(self, message_id: str, token: str) -> bool:
        """
        https://docs.mail.tm/#delete-messagesid
        """
        response = await self.session.delete(f"{self.API_URL}/messages/{message_id}",
                                             headers={'Authorization': f'Bearer {token}'},
                                             ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/messages/{message_id}: {response}')
        if await validate_response(response):
            return response.status == 204
        logger.debug(f'Error response for {self.API_URL}/messages/{message_id}: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/messages/{message_id}",
                                    await response.json())

    async def set_read_message_by_id(self, message_id: str, token: str) -> bool:
        """
        https://docs.mail.tm/#patch-messagesid
        """
        response = await self.session.put(f"{self.API_URL}/messages/{message_id}/read",
                                          headers={'Authorization': f'Bearer {token}'},
                                          ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/messages/{message_id}/read: {response}')
        if await validate_response(response):
            return (await response.json())['seen'] == "read"
        logger.debug(f'Error response for {self.API_URL}/messages/{message_id}/read: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/messages/{message_id}/read",
                                    await response.json())

    async def get_message_source_by_id(self, message_id: str, token: str) -> MessageSource:
        """
        https://docs.mail.tm/#get-messagesidsource
        """
        response = await self.session.get(f"{self.API_URL}/messages/{message_id}/source",
                                          headers={'Authorization': f'Bearer {token}'},
                                          ssl=self.SSL)
        logger.debug(f'Response for {self.API_URL}/messages/{message_id}/source: {response}')
        if await validate_response(response):
            return MessageSource(**(await response.json()))
        logger.debug(f'Error response for {self.API_URL}/messages/{message_id}/source: {response}')
        raise MailTMInvalidResponse(f"Error response for {self.API_URL}/messages/{message_id}/source",
                                    await response.json())
