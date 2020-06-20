from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

workmode = ['Style transfer', 'Fast style transfer', 'GAN']
menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=workmode[0])
        ],
        [
            KeyboardButton(text=workmode[1])
        ],
        [
            KeyboardButton(text=workmode[2])
        ]
    ],
    resize_keyboard=True
)


examples_style = ['style 1', 'style 2', 'style 3', 'style 4', 'style 5', 'style 6', 'style 7', 'style 8']
exam_style_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=examples_style[0]),
            KeyboardButton(text=examples_style[1]),
            KeyboardButton(text=examples_style[2]),
            KeyboardButton(text=examples_style[3]),
        ],
        [
            KeyboardButton(text=examples_style[4]),
            KeyboardButton(text=examples_style[5]),
            KeyboardButton(text=examples_style[6]),
            KeyboardButton(text=examples_style[7]),
        ]
    ],
    resize_keyboard=True
)


cartoon_styles = ['Hayao', 'Hosoda', 'Paprika', 'Shinkai']
cartoon_styles_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=cartoon_styles[0]),
            KeyboardButton(text=cartoon_styles[1]),
        ],
        [
            KeyboardButton(text=cartoon_styles[2]),
            KeyboardButton(text=cartoon_styles[3]),
        ]
    ],
    resize_keyboard=True
)