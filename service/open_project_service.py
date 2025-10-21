from config import config_
import aiohttp
import base64
from typing import Optional, Dict, Any, List
import re
from logging_config import logger


def watchers(func):
    """
    Декоратор. Расширяет метод OpenProjectService.process_webhook_json добавляя в список пользователей которым
    будет выслано уведомление "Наблюдателей".
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

                # Добавляем пользователей-наблюдателей в результирующий словарь
                [task_info['notify_users'].append(item) for item in watching_users
                 if item not in task_info['notify_users']
                 ]

        except Exception as _ex:
            logger.error(f"Ошибка обработки данных в декораторе <watchers>: {_ex}\n <body_json>: {body_json}")
        finally:
            return task_info

    return wrapper


class OpenProjectService:
    """
    Класс для обработки содержания вебхука. Формирует новый json с деталями и споиском пользователей,
    которые получат уведомления
    """

    def __init__(self):
        self.host = config_.DOMAIN
        self.api_key = config_.USER_API_KEY

    async def get_request_to_api(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Базовая функция для запроса на различные ендпоинты апи опенпроджекта
        """

        auth_string = base64.b64encode(f"apikey:{self.api_key}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_string}"}
        url = f"{self.host}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None
                return await response.json()

    async def get_all_users(self, offset=1, data=None) -> list[str] or None:
        """
        Получает список всех логинов при помощи запроса к апи. Работает рекурсивно
        """

        if not data:
            data = []

        res = await self.get_request_to_api(f'/api/v3/users?offset={str(offset)}')
        if not res:
            raise ValueError('‼️ Пустой ответ при запросе на получение списка всех пользователей к /api/v3/users. Возможно сервисный аккаунт заблокирован, обратитесь к администратору')
        if not res['_embedded']['elements']:  # выход из рекурсии
            return data

        elements: list[dict] = res['_embedded']['elements']
        data.extend([i['name'] for i in elements])
        return await self.get_all_users(offset + 1, data)

    @watchers
    async def process_webhook_json(self, body_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Метод, который из сырого вебхука формирует словарь с деталями и списком пользователей
        """

        action = body_json.get('action')
        work_package = body_json.get('work_package') # основной блок с информацией из вебхука
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
            task_info['update_type'] = f"🔁 <b>Обновление задачи: </b>\n{last_activity}"
            task_info['notify_users'] = [
                user for user in [task_info['author'], task_info['responsible'], task_info['performer']]
                if user and user.get('href') != activity_user_href
            ]
            return task_info

        elif action == "work_package_comment:comment":
            # Формируем документ если новый комментарий к таске
            new_comment = body_json["activity"]["comment"]["raw"]
            activity_user_href = body_json["activity"]["_links"]["user"]['href']
            # При типе обновления <work_package_comment:comment> вебхук не содержит нужных ключей. Поэтому необходимо
            # выдернуть ендпоинт ведущий на детализацию таски и сделать запрос
            work_package_url = body_json["activity"]["_links"]["workPackage"]["href"]
            work_package = await self.get_request_to_api(work_package_url)
            try:
                task_info = self.get_task_info(work_package)
            except Exception as _ex:
                logger.error(f"Ошибка обработки данных в методе <process_webhook_json>: {_ex}"
                             f"\n <body_json>: {body_json}")

                return
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

    @staticmethod
    def _get_embedded_value(work_package: Dict[str, Any], keys: List[str], default=None):
        """
        Сервисный метод для работы с ключами словаря
        """

        current = work_package
        try:
            for key in keys:
                current = current[key]
            pattern = r'<img\b[^>]*>|<figure\b[^>]*>[\s\S]*?</figure>'
            current = re.sub(pattern, '* Изображение 🏞', current)
            return current
        except (KeyError, TypeError):
            return default

    def get_task_info(self, work_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Метод разбирает данные вебхука, извлекает только необходимое и создаёт новый словарь с извлечёнными данными
        """

        info = {
            'update_type': None,
            'subject': work_package.get('subject'),
            'type': work_package.get('_type'),
            'priority': self._get_embedded_value(work_package, ['_embedded', 'priority', 'name']),
            'project': self._get_embedded_value(work_package, ['_embedded', 'project', 'name']),
            'status': self._get_embedded_value(work_package, ['_embedded', 'status', 'name']),
            'author': self._get_field_info(work_package, 'author'),
            'performer': self._get_field_info(work_package, 'customField12'),
            'responsible': self._get_field_info(work_package, 'responsible'),
            'description': self._get_embedded_value(work_package, ['description', 'raw']),
            'link': self._get_link(work_package, self.host),
            'notify_users': []
        }
        return info

    def _get_field_info(self, work_package: Dict[str, Any], field: str) -> Optional[Dict[str, str]]:
        """
        Сервисный метод для извлечения значений по определённым ключам (логин и ендпоинт пользователя)
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
        Сервисный метод для извлечения значений по определённым ключам (логин и ендпоинт пользователя)
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


open_prj_service = OpenProjectService()

# d_ = \
#     {'action': 'work_package_comment:comment', 'activity': {'_type': 'Activity::Comment', 'id': 1817, 'comment': {'format': 'markdown', 'raw': 'test comment', 'html': '<p class="op-uc-p">test comment</p>'}, 'details': [], 'version': 2, 'internal': False, 'createdAt': '2025-10-21T11:04:25.482Z', 'updatedAt': '2025-10-21T11:04:25.482Z', '_embedded': {'attachments': {'_type': 'Collection', 'total': 0, 'count': 0, '_embedded': {'elements': []}, '_links': {'self': {'href': '/api/v3/activities/1817/attachments'}}}, 'workPackage': {'_type': 'WorkPackage', 'id': 410, 'lockVersion': 1, 'subject': 'testwatcher', 'description': {'format': 'markdown', 'raw': 'test watcher', 'html': '<p class="op-uc-p">test watcher</p>'}, 'scheduleManually': True, 'startDate': None, 'dueDate': None, 'derivedStartDate': None, 'derivedDueDate': None, 'estimatedTime': None, 'derivedEstimatedTime': None, 'derivedRemainingTime': None, 'duration': None, 'ignoreNonWorkingDays': False, 'percentageDone': None, 'derivedPercentageDone': None, 'createdAt': '2025-10-21T11:04:25.398Z', 'updatedAt': '2025-10-21T11:04:25.482Z', 'readonly': False, '_links': {'attachments': {'href': '/api/v3/work_packages/410/attachments'}, 'addAttachment': {'href': '/api/v3/work_packages/410/attachments', 'method': 'post'}, 'fileLinks': {'href': '/api/v3/work_packages/410/file_links'}, 'addFileLink': {'href': '/api/v3/work_packages/410/file_links', 'method': 'post'}, 'self': {'href': '/api/v3/work_packages/410', 'title': 'testwatcher'}, 'update': {'href': '/api/v3/work_packages/410/form', 'method': 'post'}, 'schema': {'href': '/api/v3/work_packages/schemas/25-15'}, 'updateImmediately': {'href': '/api/v3/work_packages/410', 'method': 'patch'}, 'delete': {'href': '/api/v3/work_packages/410', 'method': 'delete'}, 'logTime': {'href': '/api/v3/time_entries', 'title': "Log time on work package 'testwatcher'"}, 'move': {'href': '/work_packages/410/move/new', 'type': 'text/html', 'title': "Move work package 'testwatcher'"}, 'copy': {'href': '/work_packages/410/copy', 'type': 'text/html', 'title': "Copy work package 'testwatcher'"}, 'pdf': {'href': '/work_packages/410.pdf', 'type': 'application/pdf', 'title': 'Export as PDF'}, 'generate_pdf': {'href': '/work_packages/410/generate_pdf_dialog', 'type': 'text/vnd.turbo-stream.html', 'title': 'Generate PDF'}, 'atom': {'href': '/work_packages/410.atom', 'type': 'application/rss+xml', 'title': 'Atom feed'}, 'availableRelationCandidates': {'href': '/api/v3/work_packages/410/available_relation_candidates', 'title': 'Potential work packages to relate to'}, 'customFields': {'href': '/projects/tikiety/settings/custom_fields', 'type': 'text/html', 'title': 'Custom fields'}, 'configureForm': {'href': '/types/15/form_configuration/edit', 'type': 'text/html', 'title': 'Configure form'}, 'activities': {'href': '/api/v3/work_packages/410/activities'}, 'availableWatchers': {'href': '/api/v3/work_packages/410/available_watchers'}, 'relations': {'href': '/api/v3/work_packages/410/relations'}, 'revisions': {'href': '/api/v3/work_packages/410/revisions'}, 'watchers': {'href': '/api/v3/work_packages/410/watchers'}, 'addWatcher': {'href': '/api/v3/work_packages/410/watchers', 'method': 'post', 'payload': {'user': {'href': '/api/v3/users/{user_id}'}}, 'templated': True}, 'removeWatcher': {'href': '/api/v3/work_packages/410/watchers/{user_id}', 'method': 'delete', 'templated': True}, 'addRelation': {'href': '/api/v3/work_packages/410/relations', 'method': 'post', 'title': 'Add relation'}, 'addChild': {'href': '/api/v3/projects/tikiety/work_packages', 'method': 'post', 'title': 'Add child of testwatcher'}, 'changeParent': {'href': '/api/v3/work_packages/410', 'method': 'patch', 'title': 'Change parent of testwatcher'}, 'addComment': {'href': '/api/v3/work_packages/410/activities', 'method': 'post', 'title': 'Add comment'}, 'previewMarkup': {'href': '/api/v3/render/markdown?context=/api/v3/work_packages/410', 'method': 'post'}, 'timeEntries': {'href': '/api/v3/time_entries?filters=%5B%7B%22entity_type%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%22WorkPackage%22%5D%7D%7D%2C%7B%22entity_id%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%22410%22%5D%7D%7D%5D', 'title': 'Time entries'}, 'ancestors': [], 'category': {'href': None}, 'type': {'href': '/api/v3/types/15', 'title': 'Тикет'}, 'priority': {'href': '/api/v3/priorities/8', 'title': 'Нормальный'}, 'project': {'href': '/api/v3/projects/25', 'title': 'Тикеты'}, 'projectPhase': {'href': None, 'title': None}, 'projectPhaseDefinition': {'href': None, 'title': None}, 'status': {'href': '/api/v3/statuses/1', 'title': 'Новый'}, 'author': {'href': '/api/v3/users/12', 'title': 'Кривощекий Альфред'}, 'responsible': {'href': None}, 'assignee': {'href': None}, 'version': {'href': None}, 'parent': {'href': None, 'title': None}, 'customActions': [{'href': '/api/v3/custom_actions/11', 'title': 'Принять тикет'}], 'github': {'href': '/work_packages/410/tabs/github', 'title': 'github'}, 'github_pull_requests': {'href': '/api/v3/work_packages/410/github_pull_requests', 'title': 'GitHub pull requests'}, 'gitlab': {'href': '/work_packages/410/tabs/gitlab', 'title': 'gitlab'}, 'gitlab_merge_requests': {'href': '/api/v3/work_packages/410/gitlab_merge_requests', 'title': 'Gitlab merge requests'}, 'gitlab_issues': {'href': '/api/v3/work_packages/410/gitlab_issues', 'title': 'Gitlab Issues'}, 'meetings': {'href': '/work_packages/410/tabs/meetings', 'title': 'meetings'}, 'convertBCF': {'href': '/api/bcf/2.1/projects/tikiety/topics', 'title': 'Convert to BCF', 'payload': {'reference_links': ['/api/v3/work_packages/410']}, 'method': 'post'}, 'customField25': {'title': 'Закупка оборудования', 'href': '/api/v3/custom_options/21'}, 'customField12': {'title': 'Рябцев Дмитрий', 'href': '/api/v3/users/33'}}}, 'emojiReactions': {'_type': 'Collection', 'total': 0, 'count': 0, '_embedded': {'elements': []}, '_links': {'self': {'href': '/api/v3/activities/1817/emoji_reactions'}}}}, '_links': {'attachments': {'href': '/api/v3/activities/1817/attachments'}, 'addAttachment': {'href': '/api/v3/activities/1817/attachments', 'method': 'post'}, 'self': {'href': '/api/v3/activities/1817'}, 'workPackage': {'href': '/api/v3/work_packages/410', 'title': 'testwatcher'}, 'user': {'href': '/api/v3/users/33'}, 'update': {'href': '/api/v3/activities/1817', 'method': 'patch'}, 'emojiReactions': {'href': '/api/v3/activities/1817/emoji_reactions'}}}}
#
#
# async def main():
#     res = await open_prj_service.process_webhook_json(d_)
#     print(res)
#
# import asyncio
# if __name__ == "__main__":
#     asyncio.run(main())