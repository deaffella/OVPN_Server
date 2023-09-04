from telegram import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


import math
from typing import List, Dict, Union, Any






class BaseInlineKeyboardPaginator:
    def __init__(self,
                 prefix: str,
                 items_per_page: int = 5):
        self.prefix = prefix
        self.items_per_page = items_per_page

    def __get_current_page_data(self,
                                page: int,
                                data_list: List[Any]) -> List[Dict[str, Union[str, int]]]:
        start_idx = (page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return data_list[start_idx:end_idx]

    def __add_page_buttons(self, page: int, data_list: List[Any]) -> List[List[InlineKeyboardButton]]:
        keyboard = []

        total_pages = math.ceil(len(data_list) / self.items_per_page)
        page_info = f"📄 {page}/{total_pages}"
        page_button = InlineKeyboardButton(page_info, callback_data=f"{self.prefix}:page={page}")

        bottom_keys = []
        if page > 1:
            prev_button = InlineKeyboardButton("⬅️", callback_data=f"{self.prefix}:page={page - 1}")
            bottom_keys.append(prev_button)
        bottom_keys.append(page_button)
        if page < total_pages:
            next_button = InlineKeyboardButton("➡️", callback_data=f"{self.prefix}:page={page + 1}")
            bottom_keys.append(next_button)
        keyboard.append(bottom_keys)
        keyboard.append([InlineKeyboardButton('🏠 Главное меню', callback_data=f"menu")])
        return keyboard

    def get_keyboard(self, page: int, data_list: List[Any]) -> InlineKeyboardMarkup:
        current_data = self.__get_current_page_data(page=page, data_list=data_list)
        keyboard = []

        for item in current_data:
            button = self._create_button(item=item)
            keyboard.append([button])

        keyboard += self.__add_page_buttons(page=page, data_list=data_list)
        return InlineKeyboardMarkup(keyboard)

    def _create_button(self, item: Any) -> InlineKeyboardButton:
        raise NotImplementedError



class OVPNUsersPaginator(BaseInlineKeyboardPaginator):
    def __init__(self):
        BaseInlineKeyboardPaginator.__init__(self, prefix='ovpn', items_per_page=10)

    def _create_button(self, item: Any):
        return InlineKeyboardButton(f'{item["name"]} - 🖥️ [{item["ip"]}]', callback_data=f"{self.prefix}:name={item['name']}")
