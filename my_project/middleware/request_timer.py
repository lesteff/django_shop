import time
from http.client import responses




class RequestTimerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        print("Запрос пришел", request.path)
        response = self.get_response(request)
        print("Ответ готов", response.status_code)
        end_time = time.time()
        print(f'Время выполнения : {end_time - start_time}')
        return response

