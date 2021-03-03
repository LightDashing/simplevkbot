import vk_api
from Projects_and_lessons.VKbot import Bot
from vk_api.longpoll import VkLongPoll, VkEventType, VkLongpollMode
import random

_SPEC_COMMANDS = [
    'ТЕГ',
    'МЕМ'
]
version = '5.103'
token = 'напиши сюда токен'
vk_session = vk_api.VkApi(token=token)
longpool = VkLongPoll(vk_session, mode=VkLongpollMode.GET_ATTACHMENTS)


def write_msg(user_id, message):
    vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': random.randrange(2 ** 64)})


def write_msg_attach(user_id, attach, message):
    vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': random.randrange(2**64), 'attachment': ','.join(attach)})


for event in longpool.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            print('New message')
            print(f'By user: {event.user_id}')
            bot = Bot.VKBot(event.user_id)
            print(event.attachments)
            message = bot.new_message(event, vk_session)
            if type(message) == dict:
                write_msg_attach(user_id=event.user_id, message=message.get('message'), attach=message.get('attach'))
            else:
                write_msg(event.user_id, message)
