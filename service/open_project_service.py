from config import config_
import aiohttp
import asyncio
import base64
from typing import Optional, Dict, Any, List


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

    async def process_webhook_json(self, body_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        action = body_json.get('action')
        print(action)

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
            task_info = self.get_task_info(work_package)
            print(task_info)
            task_info['update_type'] = f"💬 <b>Добавлен новый комментарий к задаче</b> пользователем"

            resp = await self.get_request_to_api(activity_user_href)
            activity_user_name = resp.get('name', '<Нет данных>')
            task_info['update_type'] += f" <i>{activity_user_name}</i>"
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
            return current
        except (KeyError, TypeError):
            return default

    def get_task_info(self, work_package: Dict[str, Any]) -> Dict[str, Any]:
        host = self.host
        return {
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
            'link': self._get_link(work_package, host),
            'notify_users': []
        }

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

# d = {'action': 'work_package_comment:comment', 'activity': {'_type': 'Activity::Comment', 'id': 1081, 'comment': {'format': 'markdown', 'raw': 'коммент \\_\\_', 'html': '<p class="op-uc-p">коммент __</p>'}, 'details': [], 'version': 33, 'internal': False, 'createdAt': '2025-10-09T12:49:23.935Z', 'updatedAt': '2025-10-09T12:49:23.935Z', '_embedded': {'attachments': {'_type': 'Collection', 'total': 0, 'count': 0, '_embedded': {'elements': []}, '_links': {'self': {'href': '/api/v3/activities/1081/attachments'}}}, 'workPackage': {'_type': 'WorkPackage', 'id': 274, 'lockVersion': 19, 'subject': 'test 8443', 'description': {'format': 'markdown', 'raw': 'https://86.57.139.197:8443/webhook', 'html': '<p class="op-uc-p"><a href="https://86.57.139.197:8443/webhook" class="op-uc-link" rel="noopener noreferrer" target="_top">https://86.57.139.197:8443/webhook</a></p>'}, 'scheduleManually': True, 'startDate': None, 'dueDate': None, 'derivedStartDate': None, 'derivedDueDate': None, 'estimatedTime': None, 'derivedEstimatedTime': None, 'derivedRemainingTime': None, 'duration': None, 'ignoreNonWorkingDays': False, 'percentageDone': None, 'derivedPercentageDone': None, 'createdAt': '2025-10-07T09:50:55.944Z', 'updatedAt': '2025-10-09T12:49:23.935Z', 'readonly': False, '_links': {'attachments': {'href': '/api/v3/work_packages/274/attachments'}, 'addAttachment': {'href': '/api/v3/work_packages/274/attachments', 'method': 'post'}, 'fileLinks': {'href': '/api/v3/work_packages/274/file_links'}, 'addFileLink': {'href': '/api/v3/work_packages/274/file_links', 'method': 'post'}, 'self': {'href': '/api/v3/work_packages/274', 'title': 'test 8443'}, 'update': {'href': '/api/v3/work_packages/274/form', 'method': 'post'}, 'schema': {'href': '/api/v3/work_packages/schemas/25-15'}, 'updateImmediately': {'href': '/api/v3/work_packages/274', 'method': 'patch'}, 'delete': {'href': '/api/v3/work_packages/274', 'method': 'delete'}, 'logTime': {'href': '/api/v3/time_entries', 'title': "Log time on work package 'test 8443'"}, 'move': {'href': '/work_packages/274/move/new', 'type': 'text/html', 'title': "Move work package 'test 8443'"}, 'copy': {'href': '/work_packages/274/copy', 'type': 'text/html', 'title': "Copy work package 'test 8443'"}, 'pdf': {'href': '/work_packages/274.pdf', 'type': 'application/pdf', 'title': 'Export as PDF'}, 'generate_pdf': {'href': '/work_packages/274/generate_pdf_dialog', 'type': 'text/vnd.turbo-stream.html', 'title': 'Generate PDF'}, 'atom': {'href': '/work_packages/274.atom', 'type': 'application/rss+xml', 'title': 'Atom feed'}, 'availableRelationCandidates': {'href': '/api/v3/work_packages/274/available_relation_candidates', 'title': 'Potential work packages to relate to'}, 'customFields': {'href': '/projects/tikiety/settings/custom_fields', 'type': 'text/html', 'title': 'Custom fields'}, 'configureForm': {'href': '/types/15/form_configuration/edit', 'type': 'text/html', 'title': 'Configure form'}, 'activities': {'href': '/api/v3/work_packages/274/activities'}, 'availableWatchers': {'href': '/api/v3/work_packages/274/available_watchers'}, 'relations': {'href': '/api/v3/work_packages/274/relations'}, 'revisions': {'href': '/api/v3/work_packages/274/revisions'}, 'watchers': {'href': '/api/v3/work_packages/274/watchers'}, 'addWatcher': {'href': '/api/v3/work_packages/274/watchers', 'method': 'post', 'payload': {'user': {'href': '/api/v3/users/{user_id}'}}, 'templated': True}, 'removeWatcher': {'href': '/api/v3/work_packages/274/watchers/{user_id}', 'method': 'delete', 'templated': True}, 'addRelation': {'href': '/api/v3/work_packages/274/relations', 'method': 'post', 'title': 'Add relation'}, 'addChild': {'href': '/api/v3/projects/tikiety/work_packages', 'method': 'post', 'title': 'Add child of test 8443'}, 'changeParent': {'href': '/api/v3/work_packages/274', 'method': 'patch', 'title': 'Change parent of test 8443'}, 'addComment': {'href': '/api/v3/work_packages/274/activities', 'method': 'post', 'title': 'Add comment'}, 'previewMarkup': {'href': '/api/v3/render/markdown?context=/api/v3/work_packages/274', 'method': 'post'}, 'timeEntries': {'href': '/api/v3/time_entries?filters=%5B%7B%22entity_type%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%22WorkPackage%22%5D%7D%7D%2C%7B%22entity_id%22%3A%7B%22operator%22%3A%22%3D%22%2C%22values%22%3A%5B%22274%22%5D%7D%7D%5D', 'title': 'Time entries'}, 'ancestors': [], 'category': {'href': None}, 'type': {'href': '/api/v3/types/15', 'title': 'Тикет'}, 'priority': {'href': '/api/v3/priorities/9', 'title': 'Высокий'}, 'project': {'href': '/api/v3/projects/25', 'title': 'Тикеты'}, 'projectPhase': {'href': None, 'title': None}, 'projectPhaseDefinition': {'href': None, 'title': None}, 'status': {'href': '/api/v3/statuses/1', 'title': 'Новый'}, 'author': {'href': '/api/v3/users/12', 'title': 'Кривощекий Альфред'}, 'responsible': {'href': None}, 'assignee': {'href': None}, 'version': {'href': None}, 'parent': {'href': None, 'title': None}, 'customActions': [{'href': '/api/v3/custom_actions/11', 'title': 'Принять тикет'}], 'github': {'href': '/work_packages/274/tabs/github', 'title': 'github'}, 'github_pull_requests': {'href': '/api/v3/work_packages/274/github_pull_requests', 'title': 'GitHub pull requests'}, 'gitlab': {'href': '/work_packages/274/tabs/gitlab', 'title': 'gitlab'}, 'gitlab_merge_requests': {'href': '/api/v3/work_packages/274/gitlab_merge_requests', 'title': 'Gitlab merge requests'}, 'gitlab_issues': {'href': '/api/v3/work_packages/274/gitlab_issues', 'title': 'Gitlab Issues'}, 'meetings': {'href': '/work_packages/274/tabs/meetings', 'title': 'meetings'}, 'convertBCF': {'href': '/api/bcf/2.1/projects/tikiety/topics', 'title': 'Convert to BCF', 'payload': {'reference_links': ['/api/v3/work_packages/274']}, 'method': 'post'}, 'customField12': {'title': 'Рябцев Дмитрий', 'href': '/api/v3/users/33'}, 'customField25': {'title': 'Настройка оборудования', 'href': '/api/v3/custom_options/20'}}}, 'emojiReactions': {'_type': 'Collection', 'total': 0, 'count': 0, '_embedded': {'elements': []}, '_links': {'self': {'href': '/api/v3/activities/1081/emoji_reactions'}}}}, '_links': {'attachments': {'href': '/api/v3/activities/1081/attachments'}, 'addAttachment': {'href': '/api/v3/activities/1081/attachments', 'method': 'post'}, 'self': {'href': '/api/v3/activities/1081'}, 'workPackage': {'href': '/api/v3/work_packages/274', 'title': 'test 8443'}, 'user': {'href': '/api/v3/users/33'}, 'update': {'href': '/api/v3/activities/1081', 'method': 'patch'}, 'emojiReactions': {'href': '/api/v3/activities/1081/emoji_reactions'}}}}
#
#
# async def main(d):
#     res = await open_prj_service.process_webhook_json(d)
#     print(res)
#
# asyncio.run(main(d))