from config import config_
import aiohttp
import base64
from typing import Optional, Dict, Any, List
import re

class OpenProjectService:
    def __init__(self):
        self.host = config_.DOMAIN
        self.api_key = config_.USER_API_KEY

    async def get_request_to_api(self, endpoint: str) -> Optional[Dict[str, Any]]:
        auth_string = base64.b64encode(f"apikey:{self.api_key}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_string}"}
        url = f"{self.host}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None
                return await response.json()

    async def get_all_users(self, offset=1, data=None) -> list or None:
        if not data:
            data = []

        res = await self.get_request_to_api(f'/api/v3/users?offset={str(offset)}')
        if not res:
            ValueError('Пустой ответ при запросе на получение списка всех пользователей к /api/v3/users')
        if not res['_embedded']['elements']:  # выход из рекурсии
            return data

        elements: list[dict] = res['_embedded']['elements']
        data.extend([i['name'] for i in elements])
        return await self.get_all_users(offset + 1, data)

    async def process_webhook_json(self, body_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        action = body_json.get('action')

        work_package = body_json.get('work_package')
        if work_package:
            task_info = self.get_task_info(work_package)
        else:
            task_info = None

        if action == "work_package:created":
            # Формируем документ если новая таска
            task_info['notify_users'] = [
                user for user in [task_info['author'], task_info['responsible'], task_info['performer']]
                if user and user != task_info['author']
            ]
            task_info['update_type'] = "🆕 <b>Новая задача</b>"
            return task_info

        elif action == "work_package:updated":

            # Формируем документ если обновление в существующей таске
            activities_url = work_package['_links']['activities']['href']
            activities_json = await self.get_request_to_api(activities_url)
            if not activities_json:
                return None
            try:
                last_element = activities_json['_embedded']['elements'][-1]
                last_activity = last_element['details'][-1]['html']
                activity_user_href = last_element['_links']['user']['href']
            except (KeyError, IndexError):
                return None
            task_info['update_type'] = f"🔁 <b>Обновление задачи:</b>\n{last_activity}"
            task_info['notify_users'] = [
                user for user in [task_info['author'], task_info['responsible'], task_info['performer']]
                if user and user.get('href') != activity_user_href
            ]
            return task_info

        elif action == "work_package_comment:comment":
            print("11")
            # Формируем документ если новый комментарий к таске
            new_comment = body_json["activity"]["comment"]["raw"]
            activity_user_href = body_json["activity"]["_links"]["user"]['href']
            work_package_url = body_json["activity"]["_links"]["workPackage"]["href"]
            work_package = await self.get_request_to_api(work_package_url)
            try:
                task_info = self.get_task_info(work_package)
            except Exception as _ex:
                return
            task_info['update_type'] = f"💬 <b>Добавлен новый комментарий к задаче</b> пользователем"

            resp = await self.get_request_to_api(activity_user_href)
            activity_user_name = resp.get('name', '<Нет данных>')
            task_info['update_type'] += f" <i>{activity_user_name}</i>"
            pattern = r'<img\b[^>]*>'
            new_comment = re.sub(pattern, '<Изображение>', new_comment)
            task_info['comment'] = new_comment
            task_info['notify_users'] = [
                user for user in [task_info['author'], task_info['responsible'], task_info['performer']]
                if user and user.get('href') != activity_user_href
            ]

            return task_info

        return None

    @staticmethod
    def _get_embedded_value(work_package: Dict[str, Any], keys: List[str], default=None):
        """Safely get deeply embedded value from a dict."""
        current = work_package
        try:
            for key in keys:
                current = current[key]
            pattern = r'<img\b[^>]*>'
            current = re.sub(pattern, '<Изображение>', current)
            return current
        except (KeyError, TypeError):
            return default

    def get_task_info(self, work_package: Dict[str, Any]) -> Dict[str, Any]:
        info = {
            'update_type': None,
            'subject': work_package.get('subject'),
            'type': work_package.get('_type'),
            'priority': self._get_embedded_value(work_package, ['_embedded', 'priority', 'name']),
            'project': self._get_embedded_value(work_package, ['_embedded', 'project', 'name']),
            'status': self._get_embedded_value(work_package, ['_embedded', 'status', 'name']),
            'author': self._get_author_info(work_package),
            'performer': self._get_field_info(work_package, 'customField12'),
            'responsible': self._get_field_info(work_package, 'responsible'),
            'description': self._get_embedded_value(work_package, ['description', 'raw']),
            'link': self._get_link(work_package, self.host),
            'notify_users': []
        }
        return info


    @staticmethod
    def _get_author_info(work_package: Dict[str, Any]) -> Optional[Dict[str, str]]:
        author = OpenProjectService._get_embedded_value(work_package, ['_embedded', 'author'])
        if author:
            return {
                'name': author.get('name'),
                'href': OpenProjectService._get_embedded_value(author, ['_links', 'self', 'href'])
            }
        return None

    @staticmethod
    def _get_field_info(work_package: Dict[str, Any], field: str) -> Optional[Dict[str, str]]:
        field_data = OpenProjectService._get_embedded_value(work_package, ['_embedded', field])
        if field_data:
            return {
                'name': field_data.get('name'),
                'href': OpenProjectService._get_embedded_value(field_data, ['_links', 'self', 'href'])
            }
        return None

    @staticmethod
    def _get_link(work_package: Dict[str, Any], host: str) -> Optional[str]:
        url: str = OpenProjectService._get_embedded_value(work_package, ['_embedded',
                                                                         'attachments',
                                                                         '_links',
                                                                         'self',
                                                                         'href']
                                                          )
        if url:
            return url.replace('/api/v3/', f'{host}/')
        return None


open_prj_service = OpenProjectService()
