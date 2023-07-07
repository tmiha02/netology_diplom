import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from db import Database
from typing import Tuple


class VKinderBot:
    def __init__(self):
        self.vk_session = vk_api.VkApi(token=input('Введите токен ВК: '))
        self.vk = self.vk_session.get_api()
        self.upload = VkUpload(self.vk_session)
        self.longpoll = VkLongPoll(self.vk_session)
        self.db = Database()

    def start(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_id = event.user_id
                message = event.text
                if message == 'Начать':
                    self.send_message(user_id, "Привет! Давай начнем поиск твоей идеальной пары)")
                    self.search_for_match(user_id)
                else:
                    self.send_message(user_id, 'Я не понимаю, чего ты хочешь. Пожалуйста, введи "Начать", чтобы начать поиск.')

    def search_for_match(self, user_id):
        age_from, age_to = self.ask_user_age_range(user_id)
        gender = self.ask_user_gender(user_id)
        city_id = self.ask_user_city(user_id)
        marital_status = self.ask_user_marital_status(user_id)

        matches = self.get_matches(age_from, age_to, gender, city_id, marital_status)
        if not matches:
            self.send_message(user_id, "Извини, совпадений не найдено.")
        else:
            for match in matches:
                profile_link = f"<https://vk.com/id{match['id']}>"
                photos = self.get_top_three_photos(match['id'])
                for photo in photos:
                    self.send_photo(user_id, photo['url'], profile_link)

    def ask_user_age_range(self, user_id) -> Tuple[int, int]:
        age_from, age_to = None, None
        while True:
            self.send_message(user_id, "Каков возрастной диапазон твоей потенциальной пары? (Например, 20-30 лет)")
            age_range = self.get_user_message(user_id)
            try:
                age_from, age_to = map(int, age_range.split('-'))
                break
            except ValueError:
                self.send_message(user_id, "Неверный ввод. Пожалуйста, попробуй еще раз.")
        return age_from, age_to

    def ask_user_gender(self, user_id):
        while True:
            self.send_message(user_id, "Каков пол твоей потенциальной пары? (мужчина/женщина)")
            gender = self.get_user_message(user_id).lower()
            if gender in ('мужчина', 'женщина'):
                return gender
            else:
                self.send_message(user_id, "Неверный ввод. Пожалуйста, попробуй еще раз.")

    def ask_user_city(self, user_id):
        while True:
            self.send_message(user_id, "Каков город твоего потенциального партнера? (Например, Москва, Санкт-Петербург)")
            city_name = self.get_user_message(user_id)
            try:
                city_id = self.vk.database.getCities(country_id=1, q=city_name)['items'][0]['id']
                return city_id
            except (IndexError, vk_api.exceptions.ApiError):
                self.send_message(user_id, "Неверный ввод. Пожалуйста, попробуй еще раз.")

    def ask_user_marital_status(self, user_id):
        while True:
            self.send_message(user_id, "Каково семейное положение твоего потенциального партнера? (холост/замужем)")
            marital_status = self.get_user_message(user_id).lower()
            if marital_status in ('холост', 'замужем'):
                return marital_status
            else:
                self.send_message(user_id, "Неверный ввод. Пожалуйста, попробуй еще раз.")

    def get_user_message(self, user_id):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.user_id == user_id:
                return event.text

    def get_matches(self, age_from, age_to, gender, city_id, marital_status):
        matches = []
        for user in self.vk.users.search(count=50, fields='photo_max_orig', city=city_id, sex=self.get_gender_id(gender),
                                          status=self.get_marital_status_id(marital_status), age_from=age_from, age_to=age_to)['items']:
            if user['id'] not in self.db.get_matches(user_id):
                matches.append(user)
        return matches

    def get_top_three_photos(self, user_id):
        photos = []
        for photo in self.vk.photos.get(owner_id=user_id, album_id='profile', extended=1)['items']:
            photos.append({
                'url': photo['sizes'][-1]['url'],
                'likes': photo['likes']['count'],
                'comments': photo['comments']['count']
            })
        photos.sort(key=lambda x: (x['likes'] + x['comments']), reverse=True)
        top_photos = photos[:3]
        return top_photos

    def send_message(self, user_id, message):
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=message
        )

    def send_photo(self, user_id, photo_url, profile_link):
        photo = self.upload.photo_messages(photos=photo_url)[0]
        attachment = f'photo{photo["owner_id"]}_{photo["id"]}'
        self.send_message(user_id, f"Profile link: {profile_link}")
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            attachment=attachment
        )

    def get_gender_id(self, gender):
        return {'male': 2, 'female': 1}[gender]

    def get_marital_status_id(self, marital_status):
        return {'single': 1, 'married': 2}[marital_status]

