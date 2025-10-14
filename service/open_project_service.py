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
            raise ValueError('‼️ Пустой ответ при запросе на получение списка всех пользователей к /api/v3/users. Возможно сервисный аккаунт заблокирован, обратитесь к администратору')
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
        """Safely get deeply embedded value from a dict."""
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

d = {'action': 'work_package:updated', 'work_package': {'_type': 'WorkPackage', 'id': 318, 'lockVersion': 6, 'subject': 'test telegram-bot', 'description': {'format': 'markdown', 'raw': 'telegram-bot', 'html': '<p class="op-uc-p">telegram-bot</p>'}, 'scheduleManually': True, 'startDate': None, 'dueDate': None, 'derivedStartDate': None, 'derivedDueDate': None, 'estimatedTime': None, 'derivedEstimatedTime': None, 'derivedRemainingTime': None, 'duration': None, 'ignoreNonWorkingDays': False, 'percentageDone': None, 'derivedPercentageDone': None, 'createdAt': '2025-10-13T12:36:56.291Z', 'updatedAt': '2025-10-13T13:57:27.004Z', 'readonly': False, '_embedded': {'attachments': {'_type': 'Collection', 'total': 0, 'count': 0, '_embedded': {'elements': []}, '_links': {'self': {'href': '/api/v3/work_packages/318/attachments'}}}, 'relations': {'_type': 'Collection', 'total': 0, 'count': 0, '_embedded': {'elements': []}, '_links': {'self': {'href': '/api/v3/work_packages/318/relations'}}}, 'type': {'_type': 'Type', 'id': 15, 'name': 'Тикет', 'color': '#339933', 'position': 7, 'isDefault': False, 'isMilestone': False, 'createdAt': '2025-09-30T12:53:11.172Z', 'updatedAt': '2025-09-30T14:29:24.832Z', '_links': {'self': {'href': '/api/v3/types/15', 'title': 'Тикет'}}}, 'priority': {'_type': 'Priority', 'id': 8, 'name': 'Нормальный', 'position': 2, 'color': '#74C0FC', 'isDefault': True, 'isActive': True, '_links': {'self': {'href': '/api/v3/priorities/8', 'title': 'Нормальный'}}}, 'project': {'_type': 'Project', 'id': 25, 'identifier': 'tikiety', 'name': 'Тикеты', 'active': True, 'public': True, 'description': {'format': 'markdown', 'raw': '', 'html': ''}, 'createdAt': '2025-09-30T12:38:06.472Z', 'updatedAt': '2025-10-08T10:24:31.626Z', 'statusExplanation': {'format': 'markdown', 'raw': '', 'html': ''}, '_links': {'self': {'href': '/api/v3/projects/25', 'title': 'Тикеты'}, 'createWorkPackage': {'href': '/api/v3/projects/25/work_packages/form', 'method': 'post'}, 'createWorkPackageImmediately': {'href': '/api/v3/projects/25/work_packages', 'method': 'post'}, 'workPackages': {'href': '/api/v3/projects/25/work_packages'}, 'storages': [], 'categories': {'href': '/api/v3/projects/25/categories'}, 'versions': {'href': '/api/v3/projects/25/versions'}, 'memberships': {'href': '/api/v3/memberships?filters=%5B%7B%22project%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%2225%22%5D%7D%7D%5D'}, 'types': {'href': '/api/v3/projects/25/types'}, 'update': {'href': '/api/v3/projects/25/form', 'method': 'post'}, 'updateImmediately': {'href': '/api/v3/projects/25', 'method': 'patch'}, 'delete': {'href': '/api/v3/projects/25', 'method': 'delete'}, 'schema': {'href': '/api/v3/projects/schema'}, 'ancestors': [{'href': '/api/v3/projects/6', 'title': 'REMZONA.by'}], 'projectStorages': {'href': '/api/v3/project_storages?filters=%5B%7B%22projectId%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%2225%22%5D%7D%7D%5D'}, 'parent': {'href': '/api/v3/projects/6', 'title': 'REMZONA.by'}, 'status': {'href': None}}}, 'status': {'_type': 'Status', 'id': 7, 'name': 'В работе', 'isClosed': False, 'color': '#00B0F0', 'isDefault': False, 'isReadonly': False, 'excludedFromTotals': False, 'defaultDoneRatio': 0, 'position': 3, '_links': {'self': {'href': '/api/v3/statuses/7', 'title': 'В работе'}}}, 'author': {'_type': 'User', 'id': 12, 'name': 'Кривощекий Альфред', 'createdAt': '2025-09-19T10:34:12.031Z', 'updatedAt': '2025-10-01T06:21:40.014Z', 'login': 'Кривощекий Альфред', 'admin': True, 'firstName': 'Альфред', 'lastName': 'Кривощекий', 'email': 'alfkriv@mail.remzona.by', 'avatar': '', 'status': 'active', 'identityUrl': None, 'language': 'ru', '_links': {'self': {'href': '/api/v3/users/12', 'title': 'Кривощекий Альфред'}, 'memberships': {'href': '/api/v3/memberships?filters=%5B%7B%22principal%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%2212%22%5D%7D%7D%5D', 'title': 'Членство'}, 'showUser': {'href': '/users/12', 'type': 'text/html'}, 'updateImmediately': {'href': '/api/v3/users/12', 'title': 'Update Кривощекий Альфред', 'method': 'patch'}, 'lock': {'href': '/api/v3/users/12/lock', 'title': 'Set lock on Кривощекий Альфред', 'method': 'post'}, 'delete': {'href': '/api/v3/users/12', 'title': 'Delete Кривощекий Альфред', 'method': 'delete'}}}, 'customActions': [], 'customField12': {'_type': 'User', 'id': 33, 'name': 'Рябцев Дмитрий', 'createdAt': '2025-09-25T13:10:59.198Z', 'updatedAt': '2025-10-13T07:37:54.568Z', 'login': 'Рябцев Дмитрий', 'admin': True, 'firstName': 'Дмитрий', 'lastName': 'Рябцев', 'email': 'kms@mail.remzona.by', 'avatar': '', 'status': 'active', 'identityUrl': None, 'language': 'ru', '_links': {'self': {'href': '/api/v3/users/33', 'title': 'Рябцев Дмитрий'}, 'memberships': {'href': '/api/v3/memberships?filters=%5B%7B%22principal%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%2233%22%5D%7D%7D%5D', 'title': 'Членство'}, 'showUser': {'href': '/users/33', 'type': 'text/html'}, 'updateImmediately': {'href': '/api/v3/users/33', 'title': 'Update Рябцев Дмитрий', 'method': 'patch'}, 'lock': {'href': '/api/v3/users/33/lock', 'title': 'Set lock on Рябцев Дмитрий', 'method': 'post'}, 'delete': {'href': '/api/v3/users/33', 'title': 'Delete Рябцев Дмитрий', 'method': 'delete'}}}}, '_links': {'attachments': {'href': '/api/v3/work_packages/318/attachments'}, 'addAttachment': {'href': '/api/v3/work_packages/318/attachments', 'method': 'post'}, 'fileLinks': {'href': '/api/v3/work_packages/318/file_links'}, 'addFileLink': {'href': '/api/v3/work_packages/318/file_links', 'method': 'post'}, 'self': {'href': '/api/v3/work_packages/318', 'title': 'test telegram-bot'}, 'update': {'href': '/api/v3/work_packages/318/form', 'method': 'post'}, 'schema': {'href': '/api/v3/work_packages/schemas/25-15'}, 'updateImmediately': {'href': '/api/v3/work_packages/318', 'method': 'patch'}, 'delete': {'href': '/api/v3/work_packages/318', 'method': 'delete'}, 'logTime': {'href': '/api/v3/time_entries', 'title': "Log time on work package 'test telegram-bot'"}, 'move': {'href': '/work_packages/318/move/new', 'type': 'text/html', 'title': "Move work package 'test telegram-bot'"}, 'copy': {'href': '/work_packages/318/copy', 'type': 'text/html', 'title': "Copy work package 'test telegram-bot'"}, 'pdf': {'href': '/work_packages/318.pdf', 'type': 'application/pdf', 'title': 'Export as PDF'}, 'generate_pdf': {'href': '/work_packages/318/generate_pdf_dialog', 'type': 'text/vnd.turbo-stream.html', 'title': 'Generate PDF'}, 'atom': {'href': '/work_packages/318.atom', 'type': 'application/rss+xml', 'title': 'Atom feed'}, 'availableRelationCandidates': {'href': '/api/v3/work_packages/318/available_relation_candidates', 'title': 'Potential work packages to relate to'}, 'customFields': {'href': '/projects/tikiety/settings/custom_fields', 'type': 'text/html', 'title': 'Custom fields'}, 'configureForm': {'href': '/types/15/form_configuration/edit', 'type': 'text/html', 'title': 'Configure form'}, 'activities': {'href': '/api/v3/work_packages/318/activities'}, 'availableWatchers': {'href': '/api/v3/work_packages/318/available_watchers'}, 'relations': {'href': '/api/v3/work_packages/318/relations'}, 'revisions': {'href': '/api/v3/work_packages/318/revisions'}, 'watchers': {'href': '/api/v3/work_packages/318/watchers'}, 'addWatcher': {'href': '/api/v3/work_packages/318/watchers', 'method': 'post', 'payload': {'user': {'href': '/api/v3/users/{user_id}'}}, 'templated': True}, 'removeWatcher': {'href': '/api/v3/work_packages/318/watchers/{user_id}', 'method': 'delete', 'templated': True}, 'addRelation': {'href': '/api/v3/work_packages/318/relations', 'method': 'post', 'title': 'Add relation'}, 'addChild': {'href': '/api/v3/projects/tikiety/work_packages', 'method': 'post', 'title': 'Add child of test telegram-bot'}, 'changeParent': {'href': '/api/v3/work_packages/318', 'method': 'patch', 'title': 'Change parent of test telegram-bot'}, 'addComment': {'href': '/api/v3/work_packages/318/activities', 'method': 'post', 'title': 'Add comment'}, 'previewMarkup': {'href': '/api/v3/render/markdown?context=/api/v3/work_packages/318', 'method': 'post'}, 'timeEntries': {'href': '/api/v3/time_entries?filters=%5B%7B%22entity_type%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%22WorkPackage%22%5D%7D%7D%2C%7B%22entity_id%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%22318%22%5D%7D%7D%5D', 'title': 'Time entries'}, 'ancestors': [], 'category': {'href': None}, 'type': {'href': '/api/v3/types/15', 'title': 'Тикет'}, 'priority': {'href': '/api/v3/priorities/8', 'title': 'Нормальный'}, 'project': {'href': '/api/v3/projects/25', 'title': 'Тикеты'}, 'projectPhase': {'href': None, 'title': None}, 'projectPhaseDefinition': {'href': None, 'title': None}, 'status': {'href': '/api/v3/statuses/7', 'title': 'В работе'}, 'author': {'href': '/api/v3/users/12', 'title': 'Кривощекий Альфред'}, 'responsible': {'href': None}, 'assignee': {'href': None}, 'version': {'href': None}, 'parent': {'href': None, 'title': None}, 'customActions': [], 'github': {'href': '/work_packages/318/tabs/github', 'title': 'github'}, 'github_pull_requests': {'href': '/api/v3/work_packages/318/github_pull_requests', 'title': 'GitHub pull requests'}, 'gitlab': {'href': '/work_packages/318/tabs/gitlab', 'title': 'gitlab'}, 'gitlab_merge_requests': {'href': '/api/v3/work_packages/318/gitlab_merge_requests', 'title': 'Gitlab merge requests'}, 'gitlab_issues': {'href': '/api/v3/work_packages/318/gitlab_issues', 'title': 'Gitlab Issues'}, 'meetings': {'href': '/work_packages/318/tabs/meetings', 'title': 'meetings'}, 'convertBCF': {'href': '/api/bcf/2.1/projects/tikiety/topics', 'title': 'Convert to BCF', 'payload': {'reference_links': ['/api/v3/work_packages/318']}, 'method': 'post'}, 'customField12': {'title': 'Рябцев Дмитрий', 'href': '/api/v3/users/33'}, 'customField25': {'title': 'Закупка оборудования', 'href': '/api/v3/custom_options/21'}}}}

async def main():
    res = await open_prj_service.process_webhook_json(d)
    print(res)

import asyncio

asyncio.run(main())