import time
from http.client import responses
import logging

logger = logging.getLogger("api")



class RequestTimerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        logger.info(f"Запрос пришел {request.path}")
        response = self.get_response(request)
        logger.info(f"Ответ готов {response.status_code}")
        end_time = time.time()
        finish_time = end_time - start_time
        logger.info(f'Время выполнения : {round(finish_time,3)}')
        return response

