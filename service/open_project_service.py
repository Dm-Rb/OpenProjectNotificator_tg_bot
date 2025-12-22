from config import config_
import aiohttp
import base64
from typing import Optional, Dict, Any, List
import re
from logging_config import logger


def customField55(func):
    async def wrapper(self_instance, body_json):

        task_info = await func(self_instance, body_json)
        try:
            if task_info.get('project'):
                prj_name = 'Оплата счетов'
                if prj_name.lower() in task_info['project'].lower():
                    if task_info.get('status'):
                        stat_name = 'В оплату'
                        if stat_name.lower() in task_info['status'].lower():
                            work_package = body_json.get('work_package')
                            if work_package:
                                if work_package.get('customField55'):
                                    task_info['notify_users'].append({"name": work_package['customField55'], "href": ""})
                                    if work_package.get('customField51'):
                                        task_info['invoice'] = str(work_package.get('customField51'))
                                    return task_info
                            activity = body_json.get('activity')
                            if activity:
                                _embedded = activity.get('_embedded')
                                if _embedded:
                                    work_package = _embedded.get('workPackage')
                                    if work_package:
                                        if work_package.get('customField55'):
                                            task_info['notify_users'].append(
                                                {"name": work_package['customField55'], "href": ""})
                                            if work_package.get('customField51'):
                                                task_info['invoice'] = str(work_package.get('customField51'))
                                            return task_info
        except Exception as e:
            logger.error("Error in the <customField55> decorator': %s; body_json: %s", str(e), body_json)
        finally:
            return task_info

    return wrapper


def watchers(func):
    """
    Decorator. Extends the OpenProjectService.process_webhook_json method.
    Adds users with the "Observer" status to the list of recipients for notifications.
    """
    async def wrapper(self_instance, body_json):
        task_info = await func(self_instance, body_json)
        try:
            if body_json.get('work_package', None):
                endpoint = self_instance._get_embedded_value(body_json['work_package'], ['_links', 'watchers', 'href'])
            elif body_json.get('activity', None):
                endpoint = self_instance._get_embedded_value(body_json['activity'],
                                                             ['_embedded', 'workPackage', '_links', 'watchers', 'href'])
            else:
                endpoint = None

            if endpoint:
                response = await self_instance.get_request_to_api(endpoint)
                if not response:
                    return task_info
                _array = response.get('_embedded', None)
                if not _array:
                    return task_info
                _array = _array.get('elements', None)
                if not _array:
                    return task_info

                name_lamb = lambda x: self_instance._get_embedded_value(x, ['_links', 'self', 'title'])
                href_lamb = lambda x: self_instance._get_embedded_value(x, ['_links', 'self', 'href'])
                watching_users = [{"name": name_lamb(i), "href": href_lamb(i)} for i in _array]
                # Add watcher users to the resulting dictionary
                for watching_user in watching_users:
                    if watching_user != task_info['author']:
                        task_info['notify_users'].append(watching_user)

        except Exception as _ex:

            logger.error("Error in the <watchers> decorator: %s; body_json: %s", str(_ex), body_json)
        finally:
            return task_info

    return wrapper


class OpenProjectService:
    """
    Class for processing webhooks. Forms a new JSON with details and a list of users
    who will receive notifications
    """

    def __init__(self):
        self.host = config_.DOMAIN
        self.api_key = config_.USER_API_KEY

    async def get_request_to_api(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Method for making GET requests to various API endpoints of your "Open Project" board
        """

        auth_string = base64.b64encode(f"apikey:{self.api_key}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_string}"}
        url = f"{self.host}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_= await response.json()
                    raise ValueError(f'Request to {url} has status code {response.status}. Response body: {error_}')
                return await response.json()

    async def get_all_users(self, offset=1, data=None) -> list[str] or None:
        """
        Retrieves a list of all logins from your "Open Project" board
        """

        if not data:
            data = []

        res = await self.get_request_to_api(f'/api/v3/users?offset={str(offset)}')
        if not res:
            raise ValueError("An API request to retrieve the list of all users was made. "
                             "The API returned an empty response. Please check the user's access token.")
        if not res['_embedded']['elements']:  # exit frm recursion
            return data

        elements: list[dict] = res['_embedded']['elements']
        data.extend([i['name'] for i in elements])
        return await self.get_all_users(offset + 1, data)

    @staticmethod
    def _get_embedded_value(work_package: Dict[str, Any], keys: List[str], default=None) -> str:
        """
        Service method for working with dictionary keys. The first argument takes the dictionary content from the
        webhook under the key "work_package". The second argument takes a list representing the chain of keys to extract
        the value for the final key. For example, 'key1' contains a dictionary with 'key2',
        which in turn contains 'key3'. We pass the list [key1, key2, key3] and get the value for key3
        """

        current = work_package
        try:
            for key in keys:
                current = current[key]
            # If the key value is an HTML tag containing an image link, we replace the value with the string
            # "* Image 🏞", because the original value causes an error during processing by Telegram servers.
            pattern = r'<img\b[^>]*>|<figure\b[^>]*>[\s\S]*?</figure>'
            current = re.sub(pattern, '* Image 🏞', current)
            return current
        except (KeyError, TypeError):
            return default

    def _get_field_info(self, work_package: Dict[str, Any], field: str) -> Optional[Dict[str, str]]:
        """
        A service method for extracting values for specific keys (user login and endpoint).
        It is almost analogous to <_get_embedded_value>, but with some specific differences.
        """

        name = self._get_embedded_value(work_package, ['_embedded', field, '_links', 'self', 'title'])
        href = self._get_embedded_value(work_package, ['_embedded', field, '_links', 'self', 'href'])
        if name and href:
            return {
                'name': name,
                'href': href
            }
        return None

    @staticmethod
    def _get_link(work_package: Dict[str, Any], host: str) -> Optional[str]:
        """
        A service method for extracting values for specific keys
        """

        url: str = OpenProjectService._get_embedded_value(work_package, ['_embedded',
                                                                         'attachments',
                                                                         '_links',
                                                                         'self',
                                                                         'href']
                                                          )
        if url:
            return url.replace('/api/v3/', f'{host}/')
        return None

    def get_task_info(self, work_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        This method parses the webhook data, extracts only the necessary information, and creates a new dictionary with
        the extracted data, which is then passed for processing to the Telegram bot.
        """

        info = {
            'update_type': None,
            'subject': work_package.get('subject'),
            'type': work_package.get('_type'),
            'priority': self._get_embedded_value(work_package, ['_embedded', 'priority', 'name']),
            'project': self._get_embedded_value(work_package, ['_embedded', 'project', 'name']),
            'status': self._get_embedded_value(work_package, ['_embedded', 'status', 'name']),
            'author': self._get_field_info(work_package, 'author'),
            'performer': self._get_field_info(work_package, 'customField12'),  # Custom Field
            'responsible': self._get_field_info(work_package, 'responsible'),
            'description': self._get_embedded_value(work_package, ['description', 'raw']),
            'link': self._get_link(work_package, self.host),
            'notify_users': []
        }
        return info

    @customField55
    @watchers
    async def processing_webhook_json(self, body_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        The method forms a dictionary used to create the message for sending via the Telegram bot,
        and also generates a list of users who will receive the distribution
        """
        action = body_json.get('action')
        # based on the update type, the resulting dictionary is formed. there are only three types: creating a new task,
        # updating an existing task, and adding a comment to an existing task

        # ****
        if action == "work_package:created":
            task_info = self.get_task_info(body_json.get('work_package')) # block with necessary information from the webhook

            # New task was created
            task_info['notify_users'] = [
                user for user in [task_info['author'], task_info['responsible'], task_info['performer']]
                if user and user != task_info['author']
            ]

            task_info['update_type'] = "🆕 <b>Новая задача</b>"
            return task_info
        # ****
        elif action == "work_package:updated":
            work_package = body_json.get('work_package')
            task_info = self.get_task_info(work_package) # block with necessary information from the webhook
            # Existing task was updated
            activities_url = work_package['_links']['activities']['href']
            activities_json = await self.get_request_to_api(activities_url)
            if not activities_json:
                raise ValueError("An API request was made to get the history of all changes made to a task by users. "
                                 "The API returned an empty response. Please check the user's access token.")
            try:
                last_element = activities_json['_embedded']['elements'][-1]

                last_activity = last_element['details'][-1]['html']
                activity_user_href = last_element['_links']['user']['href']
            except (KeyError, IndexError):
                raise ValueError("An API request was made to get the history of all changes made to a task by users. "
                                 "The API returned an empty response. Please check the user's access token.")

            task_info['update_type'] = f"🔁 <b>Обновление задачи: </b>\n{last_activity}"
            task_info['notify_users'] = [
                user for user in [task_info['author'], task_info['responsible'], task_info['performer']]
                if user and user.get('href') != activity_user_href
            ]
            return task_info
        # ****
        elif action == "work_package_comment:comment":
            # Сomment was added to an existing task
            new_comment = body_json["activity"]["comment"]["raw"]
            activity_user_href = body_json["activity"]["_links"]["user"]['href']

            # With this type of update, the webhook doesn't contain the required keys. Therefore, it's necessary
            work_package_url = body_json["activity"]["_links"]["workPackage"]["href"]  # get API endpoint
            work_package = await self.get_request_to_api(work_package_url)
            try:
                task_info = self.get_task_info(work_package)
            except Exception as _ex:
                raise ValueError(f"Error processing data in the <process_webhook_json> method. {_ex}"
                             f"\n <body_json>: {body_json}")

            task_info['update_type'] = f"💬 <b>Добавлен новый комментарий к задаче</b> пользователем"

            resp = await self.get_request_to_api(activity_user_href)
            activity_user_name = resp.get('name', '<Нет данных>')
            task_info['update_type'] += f" <i>{activity_user_name}</i>"
            pattern = r'<img\b[^>]*>'
            new_comment = re.sub(pattern, '* Изображение 🏞', new_comment)
            task_info['comment'] = new_comment
            task_info['notify_users'] = [
                user for user in [task_info['author'], task_info['responsible'], task_info['performer']]
                if user and user.get('href') != activity_user_href
            ]
            return task_info

        return None


open_prj_service = OpenProjectService()
