import requests
import bs4
import wolframalpha
import random
from currency_converter import CurrencyConverter
from vk_api import VkUpload
from vk_api.exceptions import ApiError


class VKBot:

    _WOLFRAM_CLIENT = wolframalpha.Client('здесь токен вольфрамальфа')
    _COMMANDS = [
        'ПРИВЕТ',  # 0
        'СКАЖИ ЧИСЛО',  # 1
        'ФОТО МАРС',  # 2
        'РЕШИ',  # 3
        'ПЕРЕВЕДИ',  # 4
        'ВЫБЕРИ',  # 5
        'ИНФА',  # 6
        'МЕМ',  # 7
        'КОМАНДЫ',  # 8
        'ВОЗРАСТ',  # 9
        'ТЕГ',  # 10
        'СОЗДАТЬ QR',  # 11
        'ЧТО НА QR',  # 12
        'КАЧЕСТВО ФОТО' #13
    ]

    def get_maxsize_picture(self, vk_session, message_id):
        response = vk_session.method('messages.getHistoryAttachments',
                                     {'peer_id': self._USER_ID,
                                      'media_type': 'photo',
                                      'count': 1,
                                      'photo_sizes': 1,
                                      'start_from': str(message_id)})
        lst = response.get('items')[0].get('attachment').get('photo').get('sizes')
        for i in lst:
            if i.get('type') == 'o':
                return i.get('url')

    def _SQL_string_parser(self, string):
        return '"' + string + '"'

    def __init__(self, user_id):
        self._EVERYPIXEL_ID = 'а вот тут токен эврипикселя'
        self._EVERYPIXEL_SECRET = 'а вот тут секрет его'
        self._USER_ID = user_id
        self._USERNAME = self._get_user_name_from_vk_id(user_id)
        self._SESSION = requests.Session()

    def _get_user_name_from_vk_id(self, user_id):
        request = requests.get('https://vk.com/id' + str(user_id))
        bs = bs4.BeautifulSoup(request.text, "html.parser")

        user_name = self._clean_all_tag_from_str(bs.find_all("title")[0])
        return user_name.split()[0]

    def UploadPhotoInMessage(self, vk_session, photo_url, attachments):
        upload = VkUpload(vk_session)
        image = self._SESSION.get(photo_url, stream=True)
        if not image:
            return attachments
        try:
            photo = upload.photo_messages(photos=image.raw)[0]
        except ApiError:
            return attachments
        attachments.append(
            f'photo{photo["owner_id"]}_{photo["id"]}'
        )
        return attachments

    def read_qr(self, photo_url):
        request = requests.get('http://api.qrserver.com/v1/read-qr-code/?fileurl=' + photo_url).json()
        result = request[0].get('symbol')[0].get('data')
        if not result:
            return 'Не удалось распознать QR код!('
        return request[0].get('symbol')[0].get('data')

    def get_photo_tags(self, photo_url):
        result = []
        params = {'url': photo_url,
                  'num_keywords': 10}
        keywords = requests.get('https://api.everypixel.com/v1/keywords', params=params,
                                auth=(self._EVERYPIXEL_ID, self._EVERYPIXEL_SECRET)).json()
        for i in keywords.get('keywords'):
            result.append(i.get('keyword'))
        return result

    def get_age_on_photo(self, photo_url):
        result = []
        params = {'url': photo_url,
                  'num_keywords': 10}
        keywords = requests.get('https://api.everypixel.com/v1/faces', params=params,
                                auth=(self._EVERYPIXEL_ID, self._EVERYPIXEL_SECRET)).json()
        for i in keywords.get('faces'):
            if i.get('age'):
                result.append(int(i.get('age')))
            else:
                return 'Не удалось определить возраст('
        result = list(map(str, result))
        if not result:
            return 'На картинке более одного человека('
        return result[0]

    def get_photo_quality(self, photo_url):
        params = {'url': photo_url}
        quality = requests.get('https://api.everypixel.com/v1/quality_ugc', params=params,
                               auth=(self._EVERYPIXEL_ID, self._EVERYPIXEL_SECRET)).json()
        return quality.get('quality').get('score')

    def _wolfram_query(self, query):
        try:
            print(query)
            res = self._WOLFRAM_CLIENT.query(query)
            result = next(res.results)
            return result.text
            # TODO Сделать полный вывод решения; Желательно ещё посмотреть ошибки
        except Exception:
            return 'Введён неверный пример!'

    def create_qr_code(self, text):
        request = requests.get('https://api.qrserver.com/v1/create-qr-code/?size=500x500&data=' + text)

    @staticmethod
    def _clean_all_tag_from_str(string_line):
        result = ""
        not_skip = True
        for i in list(string_line):
            if not_skip:
                if i == "<":
                    not_skip = False
                else:
                    result += i
            else:
                if i == ">":
                    not_skip = True

        return result

    def random_curiosity_picture(self):
        key = 'ключ сюда свой'
        request = requests.get(
            'https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos?sol=1000&api_key=' + key).json()
        return request.get('photos')[random.randrange(0, 855)].get('img_src')

    def _currency_convertor(self, value, from_curr, to_curr):
        c = CurrencyConverter()
        try:
            return c.convert(value, from_curr, to_curr)
        except ValueError:
            return 'Вы ввели неверную валюту!'

    def new_message(self, event, vk_session):
        if event.text.upper() == self._COMMANDS[0]:
            return f'Привет, {self._USERNAME}, я Mayaro!'
        elif event.text.upper() == self._COMMANDS[1]:
            return f'Случайное число: {random.randrange(1000)}'
        elif event.text.upper() == self._COMMANDS[2]:
            attach = attach = self.UploadPhotoInMessage(vk_session=vk_session,
                                                        attachments=[],
                                                        photo_url=self.random_curiosity_picture())
            if not attach:
                return 'Ошибка! Не удалось загрузить картинку'
            return {'message': 'Случайная картинка с Curiosity', 'attach': attach}
            pass
        elif event.text[:4].upper() == self._COMMANDS[3]:
            return self._wolfram_query(event.text[5:])
        elif event.text[:8].upper() == self._COMMANDS[4]:
            return self._currency_convertor(from_curr=event.text[9:12].upper(), to_curr=event.text[15:18].upper(),
                                            value=event.text[19:])
        elif event.text[:6].upper() == self._COMMANDS[5]:
            choice = event.text[6:].split()
            choice_num = random.randrange(0, len(choice))
            return f'Я выбераю {choice[choice_num]}!'
        elif event.text[:4].upper() == self._COMMANDS[6]:
            percent = random.randrange(0, 100)
            return f'Вероятность, что {event.text[5:]} — {percent}%'
        elif event.text.upper() == self._COMMANDS[8]:
            return f'Команда Мем выводить случайный тупой мем (не советую пользоваться, страшна) \n ' \
                   f'Команда Скажи число выводит случайное число \n' \
                   f'Команда Найди картинку + запрос выводит картинку по запросу \n' \
                   f'Команда Реши + пример выводит ответ на решение вашей домашкиб (не списывойте твари) \n' \
                   f'Команда Выбери + выбор выбирает случайный пример из выбранного \n' \
                   f'Команда Инфа + событие выводит вероятность события \n' \
                   f'Команда привет говорит вам преветб \n' \
                   f'Команда тег выводит теги по фото \n' \
                   f'Команда Создать QR + текст создаёт QR код, а команда Что на QR выводит содержимое QR \n' \
                   f'Команда Возраст позволяет узнать возраст человека на картинке \n' \
                   f'Команда Переведи (например Переведи 100 RUB в USD) переводит валюту \n' \
                   f'Команда Фото Марс выводит случайное фото с ровера NASA curiosity \n' \
                   f'Команда Качество фото распознает качество фото. Что бы это сделать используется сторонняя нейросеть.'
        elif event.text.upper() == self._COMMANDS[9]:
            return 'Примерный возраст человека на картинке: ' + self.get_age_on_photo(self.get_maxsize_picture(vk_session=vk_session, message_id=event.message_id))
        elif event.text.upper() == self._COMMANDS[10]:
            return 'Ваши теги: ' + ', '.join(
                self.get_photo_tags(self.get_maxsize_picture(vk_session=vk_session, message_id=event.message_id)))
        elif event.text.upper() == self._COMMANDS[7]:
            return {'message': 'Ваш мем подан!', 'attach': self.UploadPhotoInMessage(vk_session=vk_session,
                                                                                     attachments=[],
                                                                                     photo_url='http://admem.ru/content/images/139111'
                                                                                               + str(
                                                                                         random.randrange(1000,
                                                                                                          9999)) + '.jpg')}
        elif event.text[:10].upper() == self._COMMANDS[11]:
            attach = self.UploadPhotoInMessage(vk_session=vk_session,
                                               attachments=[],
                                               photo_url='https://api.qrserver.com/v1/create-qr-code/?size=500x500&data=' + event.text[
                                                                                                                            11:])
            if not attach:
                return 'QR Код не удалось создать!'
            return {'message': 'QR-Код был создан!', 'attach': attach}
        elif event.text.upper() == self._COMMANDS[12]:
            return self.read_qr(self.get_maxsize_picture(vk_session=vk_session, message_id=event.message_id))
        elif event.text.upper() == self._COMMANDS[13]:
            return 'Качество вашего фото ' + str(self.get_photo_quality(self.get_maxsize_picture(vk_session=vk_session, message_id=event.message_id)))
        else:
            return f'Извините, но я не понимаю о чём вы('
