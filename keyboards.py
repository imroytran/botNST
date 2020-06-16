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

examples_style = ['Style 1', 'Style 2', 'Style 3']
exam_style_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=examples_style[0]),
            KeyboardButton(text=examples_style[1]),
            KeyboardButton(text=examples_style[2]),
        ],
    ],
    resize_keyboard=True
)
