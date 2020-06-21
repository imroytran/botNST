import logging
import aiohttp
import asyncio

from styletransfer import StyleTransfer
from styletransfer2 import FastStyleTransfer
from GAN import get_output

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.executor import start_webhook, start_polling
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import torchvision.utils as vutils
from config import BOT_TOKEN, PROXY_LOGIN, PROXY_PW, PROXY_URL
from config import WEBAPP_HOST, WEBAPP_PORT, WEBHOOK_HOST, WEBHOOK_PATH, WEBHOOK_URL, WEBHOOK_SSL_CERT
from keyboards import menu, exam_style_kb, examples_style, workmode, cartoon_styles, cartoon_styles_kb


PROXY_AUTH = aiohttp.BasicAuth(login=PROXY_LOGIN, password=PROXY_PW)

logging.basicConfig(level=logging.INFO)


class Images(StatesGroup):
    mode = State()
    content_img = State()
    style_img = State()
    GAN_img = State()

#bot = Bot(token=BOT_TOKEN, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_close()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.message):
    texts =['Welcome to Style transfer Bot!',
            'I will transfer style your photo.',
            '\tSend /mode to select working mode!',
            '\tSend /cancel for cancel transfer.',
            'We have three options:\n'
            '\tStyle transfer need to two photo: content and style image, will work on 2-3 min.\n'
            '\tFast style transfer is the same.\n'
            '\tGAN wil transfer your photo to cartoon style.']
    for text in texts:
        await message.answer(text)
        await asyncio.sleep(0.5)


@dp.message_handler(commands=['mode'])
async def choice(message: types.message):
    await message.answer('Select the working mode with the popup keyboards!', reply_markup=menu)
    await Images.mode.set()

@dp.message_handler(state="*", commands=['cancel'])
@dp.message_handler(Text(equals='cancel', ignore_case=True), state="*")
async def cancel(message: types.message, state:FSMContext):
    curent_state = await state.get_data()
    if curent_state is None:
        return
    await state.finish()
    await message.answer('Canceled!', reply_markup=ReplyKeyboardRemove())

@dp.message_handler(Text(equals=workmode), state=Images.mode)
async def get_routine(message: types.message, state:FSMContext):
    await asyncio.sleep(.5)
    if message.text not in workmode:
        await message.answer('Please select keyboards below!')
        return
    await message.answer(f'You selected working mode {message.text}.',
                         reply_markup=ReplyKeyboardRemove())
    await state.update_data(model=message.text)
    await asyncio.sleep(.5)
    if message.text in ['Style transfer', 'Fast style transfer']:
        await Images.content_img.set()
        await message.answer('Send me the image content you want to style transfer!')
    elif message.text == 'GAN':
        await Images.GAN_img.set()
        await message.answer('GAN will transfer your photo into cartoon style!')
        await asyncio.sleep(.5)
        await message.answer('Please send me a photo!')


@dp.message_handler(content_types=['document', 'photo'], state=Images.content_img)
async def download_if_send_as_file(message, state: FSMContext):
    if message.content_type == 'document':
        file_id = message.document.file_id
    else:
        file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    if file.file_path[-3:] in ['jpg', 'peg', 'png']:
        photo = await bot.download_file(file.file_path)
        async with state.proxy() as data:
            data['content_img'] = photo
    else:
        await message.answer('Send me image only!')
        return

    await asyncio.sleep(0.2)
    data = await state.get_data()
    if data.get('model') in ['Style transfer', 'Fast style transfer']:
        texts = ['Now send me the style image!',
                 'You can try the next examples style, or send me your style image from device!']
        for text in texts:
            await message.answer(text)
            await asyncio.sleep(0.2)

        for i in range(0, 8, 2):
            keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
            await types.ChatActions.upload_photo()
            media = types.MediaGroup()
            media.attach_photo(types.InputFile('data/{}.jpg'.format(examples_style[i])), examples_style[i])
            media.attach_photo(types.InputFile('data/{}.jpg'.format(examples_style[i+1])), examples_style[i+1])
            await message.answer_media_group(media=media)
            row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in \
                zip(examples_style[i:i+2], examples_style[i:i+2]))
            keyboard_markup.row(*row_btns)
            await message.answer('Examples for style images:',reply_markup=keyboard_markup)

        await message.answer('Select or send new style photo')
        await Images.style_img.set()


@dp.callback_query_handler(Text(equals=examples_style), state=Images.style_img)
async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state:FSMContext):
    answer_data = query.data
    async with state.proxy() as data:
        data['style_img'] = 'data/{}.jpg'.format(answer_data)
    await bot.send_message(query.from_user.id, 'You selected {}'.format(answer_data))
    await bot.send_message(query.from_user.id, 'Waiting...')
    data = await state.get_data()
    content_image = data.get('content_img')
    style_image = data.get('style_img')
    if data.get('model') == 'Style transfer':
        output_image = StyleTransfer(style_image, content_image).get_output()
        output_image.save('results/output.jpg')
    elif data.get('model') == 'Fast style transfer':
        FastStyleTransfer(content_image, style_image).get_output()

    await state.finish()
    await bot.send_message(query.from_user.id, 'Your mix photo by Neural Style Transfer')
    with open('results/output.jpg', 'rb') as photo:
        await bot.send_photo(query.from_user.id, photo)
    await asyncio.sleep(0.5)
    await bot.send_message(query.from_user.id, 'For next style transfer, type /mode and select working mode!')


@dp.message_handler(content_types=['document', 'photo'], state=Images.style_img)
async def download_if_send_as_file(message, state: FSMContext):
    if message.content_type == 'document':
        file_id = message.document.file_id
    else:
        file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    if file.file_path[-3:] in ['jpg', 'peg', 'png']:
        photo = await bot.download_file(file.file_path)
        await Images.style_img.set()
        async with state.proxy() as data:
            data['style_img'] = photo
    else:
        await message.answer('Send me image only!')
        return
    await message.answer('Waiting...', reply_markup=ReplyKeyboardRemove())

    data = await state.get_data()
    content_image = data.get('content_img')
    style_image = data.get('style_img')
    if data.get('model') == 'Style transfer':
        output_image = StyleTransfer(style_image, content_image).get_output()
        output_image.save('results/output.jpg')
    elif data.get('model') == 'Fast style transfer':
        FastStyleTransfer(content_image, style_image).get_output()

    await state.finish()

    await message.answer('Your mix photo by Neural Style Transfer')
    await types.ChatActions.upload_photo()
    media = types.MediaGroup()
    media.attach_photo(types.InputFile('results/output.jpg'))
    await message.answer_media_group(media=media)
    await asyncio.sleep(0.5)
    await message.answer('For next style transfer, type /mode and select working mode!')


@dp.message_handler(content_types=['document', 'photo'], state=Images.GAN_img)
async def download_if_send_as_file(message, state: FSMContext):
    if message.content_type == 'document':
        file_id = message.document.file_id
    else:
        file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    if file.file_path[-3:] in ['jpg', 'peg', 'png']:
        photo = await bot.download_file(file.file_path)
        async with state.proxy() as data:
            data['gan_image'] = photo
    else:
        await message.answer('Send me image only!')
        return

    await asyncio.sleep(0.2)
    data = await state.get_data()
    if data.get('model') == 'GAN':
        await message.answer('Now select type of style:', reply_markup=cartoon_styles_kb)

@dp.message_handler(Text(equals=cartoon_styles), state=Images.GAN_img)
async def cartoon_style(message: types.message, state: FSMContext):
    await message.answer('You selected style {}'.format(message.text), reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.2)
    data = await state.get_data()
    gan_image = data.get('gan_image')
    output_image = get_output(message.text, gan_image)
    vutils.save_image(output_image, 'results/gan.jpg')

    await state.finish()

    await message.answer('Your photo into cartoon style:')
    await types.ChatActions.upload_photo()
    media = types.MediaGroup()
    media.attach_photo(types.InputFile('results/gan.jpg'))
    await message.answer_media_group(media=media)
    await asyncio.sleep(0.5)
    await message.answer('For next style transfer, type /mode and select working mode!')


def main():
    #start_polling(dp, skip_updates=True)

    start_webhook(dispatcher=dp,
                  webhook_path=WEBHOOK_PATH,
                  on_startup=on_startup,
                  on_shutdown=on_shutdown,
                  skip_updates=True,
                  host=WEBAPP_HOST,
                  port=WEBAPP_PORT,
                  )


if __name__ == '__main__':
    main()
