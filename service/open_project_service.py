from config import config_
import aiohttp
import asyncio
import base64


class OpenProjectService:
    host = config_.DOMAIN
    api_key = config_.USER_API_KEY

    async def get_request_to_api(self, endpoint) -> dict or None:
        auth_string = base64.b64encode(f"apikey:{self.api_key}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_string}"}

        async with aiohttp.ClientSession() as session:
            url = f"{self.host}{endpoint}"

            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                return data

    async def process_webhook_json(self, body_json):
        action = body_json.get('action', None)
        if action == "work_package:created":
            # Формируем документ если новая таска
            work_package = body_json['work_package']
            task_info = self.get_task_info(work_package)
            task_info['notify_users'] = list(filter(lambda x: x and x != task_info['author'],
                                                    [
                                                        task_info['author'],
                                                        task_info['responsible'],
                                                        task_info['performer']
                                                    ]
                                                    )
                                             )

            task_info['update_type'] = "🆕 <b>Новая задача</b>"
            return task_info

        elif action == "work_package:updated":
            # Формируем документ если обновление в существующей таске
            work_package = body_json['work_package']
            task_info = self.get_task_info(work_package)
            activities_url = work_package['_links']['activities']['href']
            activities_json: dict = await self.get_request_to_api(activities_url)
            last_activity = activities_json['_embedded']['elements'][-1]['details'][-1]['html']
            activity_user_href = activities_json['_embedded']['elements'][-1]['_links']['user']['href']
            task_info['update_type'] = f"🔁 <b>Обновление задачи:</b> {last_activity}"
            task_info['notify_users'] = list(filter(lambda x: x and x['href'] != activity_user_href,
                                                    [
                                                        task_info['author'],
                                                        task_info['responsible'],
                                                        task_info['performer']
                                                    ]
                                                    )
                                             )
            return task_info

    def get_task_info(self, work_package):
        task_info = {}
        task_info['update_type'] = None
        task_info['subject'] = None
        task_info['type'] = None
        task_info['priority'] = None
        task_info['project'] = None
        task_info['status'] = None
        task_info['author'] = None
        task_info['responsible'] = None
        task_info['performer']: dict or None = None
        task_info['description'] = None
        task_info['link'] = None
        task_info['notify_users'] = []

        try:
            task_info['subject'] = work_package['subject']
        except KeyError:
            pass

        try:
            task_info['priority'] = work_package['_embedded']['priority']['name']
        except KeyError:
            pass

        try:
            task_info['project'] = work_package['_embedded']['project']['name']
        except KeyError:
            pass
        try:
            task_info['status'] = work_package['_embedded']['status']['name']
        except KeyError:
            pass
        try:
            task_info['author'] = {'name': work_package['_embedded']['author']['name'],
                                   'href': work_package['_embedded']['author']['_links']['self']['href']
                                   }
        except KeyError:
            pass

        try:
            task_info['performer'] = {'name': work_package['_embedded']['customField12']['name'],
                                      'href': work_package['_embedded']['customField12']['_links']['self']['href']
                                      }
        except KeyError:
            pass

        try:
            task_info['responsible'] = {'name': work_package['_embedded']['responsible']['name'],
                                        'href': work_package['_embedded']['responsible']['_links']['self']['href']
                                       }
        except KeyError:
            pass

        try:
            task_info['description'] = work_package['description']['raw']
        except KeyError:
            pass

        try:
            url = work_package['_embedded']['attachments']['_links']['self']['href']
            task_info['link'] = url.replace('/api/v3/', f'{self.host}/')
        except KeyError:
            pass
        return task_info


open_prj_service = OpenProjectService()


