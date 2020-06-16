import logging
import aiohttp
import asyncio

from styletransfer import StyleTransfer
from styletransfer2 import StyleTransfer2

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.executor import start_webhook, start_polling
from aiogram.contrib.fsm_storage.memory import MemoryStorage


from config import BOT_TOKEN, PROXY_LOGIN, PROXY_PW, PROXY_URL
from config import WEBAPP_HOST, WEBAPP_PORT, WEBHOOK_HOST, WEBHOOK_PATH, WEBHOOK_URL
from keyboards import menu, exam_style_kb, examples_style, workmode

PROXY_AUTH = aiohttp.BasicAuth(login=PROXY_LOGIN, password=PROXY_PW)

logging.basicConfig(level=logging.INFO)


class Images(StatesGroup):
    mode = State()
    content_img = State()
    style_img = State()
    GAN_img = State()

bot = Bot(token=BOT_TOKEN, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)
#bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL,
                          certificate=open('certificate/url_cert.pem', 'r'))

async def on_shutdown(dp):
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_close()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.message):
    texts =['Welcome to Style transfer Bot!',
            'Please enter /mode to select working mode!']
    for text in texts:
        await message.answer(text)
        await asyncio.sleep(0.5)


@dp.message_handler(commands=['mode'])
async def choice(message: types.message):
    await message.answer('Select the working mode with the popup keyboards!', reply_markup=menu)
    await Images.mode.set()


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
    else:
        await Images.GAN_img.set()
        await message.answer('Send me the image for .......')

# Save content image if client send photo as file
@dp.message_handler(content_types=['document'], state=Images.content_img)
async def download_if_send_as_file(message, state: FSMContext):
    file_id = message.document.file_id
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

        await message.answer('Examples for style images:')
        await types.ChatActions.upload_photo()
        media = types.MediaGroup()
        media.attach_photo(types.InputFile('data/1.jpg'), 'style1')
        media.attach_photo(types.InputFile('data/2.jpg'), 'style2')
        media.attach_photo(types.InputFile('data/3.jpg'), 'style3')
        await message.answer_media_group(media=media)
        await message.answer('Select:', reply_markup=exam_style_kb)
        await Images.style_img.set()



# Save content image if user send as a photo
@dp.message_handler(content_types=['photo'], state=Images.content_img)
async def download_if_send_as_photo(message, state: FSMContext):
    file = await bot.get_file(message.photo[-1].file_id)
    photo = await bot.download_file(file.file_path)
    async with state.proxy() as data:
        data['content_img'] = photo

    await asyncio.sleep(0.2)

    data = await state.get_data()
    if data.get('model') in ['Style transfer', 'Fast style transfer']:
        texts = ['Now i nesd to the style image!',
                 'You can try the next examples style, or send me your style image from device!']
        for text in texts:
            await message.answer(text)
            await asyncio.sleep(0.8)

        await message.answer('Examples for style images:')
        await types.ChatActions.upload_photo()
        media = types.MediaGroup()
        media.attach_photo(types.InputFile('data/1.jpg'), 'style1')
        media.attach_photo(types.InputFile('data/2.jpg'), 'style2')
        media.attach_photo(types.InputFile('data/3.jpg'), 'style3')
        await message.answer_media_group(media=media)
        await message.answer('Select', reply_markup=exam_style_kb)
        await Images.style_img.set()

@dp.message_handler(Text(equals=examples_style), state=Images.style_img)
async def exam_style_set(message: types.message, state:FSMContext):
    async with state.proxy() as data:
        data['style_img'] = 'data/{}.jpg'.format(message.text[-1])
    await message.answer('You selected style {}'.format(message.text[-1]),reply_markup=ReplyKeyboardRemove())

    data = await state.get_data()
    content_image = data.get('content_img')
    style_image = data.get('style_img')
    if data.get('model') == 'Style transfer':
        output_image = StyleTransfer(style_image, content_image).get_output()
        output_image.save('output.jpg')
    elif data.get('model') == 'Fast style transfer':
        StyleTransfer2(content_image, style_image).get_output()

    await state.finish()

    await message.answer('Your mix photo by Neural Style Transfer')
    await types.ChatActions.upload_photo()
    media = types.MediaGroup()
    media.attach_photo(types.InputFile('output.jpg'))
    await message.answer_media_group(media=media)

# Save style image if user send photo as file
@dp.message_handler(content_types=['document'], state=Images.style_img)
async def download_if_send_as_file(message, state: FSMContext):
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    if file.file_path[-3:] in ['jpg', 'peg', 'png']:
        photo = await bot.download_file(file.file_path)
        await Images.style_img.set()
        async with state.proxy() as data:
            data['style_img'] = photo
    else:
        await message.answer('Send me image only!')
        return

    data = await state.get_data()
    content_image = data.get('content_img')
    style_image = data.get('style_img')
    if data.get('model') == 'Style transfer':
        output_image = StyleTransfer(style_image, content_image).get_output()
        output_image.save('output.jpg')
    elif data.get('model') == 'Fast style transfer':
        StyleTransfer2(content_image, style_image).get_output()

    await state.finish()

    await message.answer('Your mix photo by Neural Style Transfer')
    await types.ChatActions.upload_photo()
    media = types.MediaGroup()
    media.attach_photo(types.InputFile('output.jpg'))
    await message.answer_media_group(media=media)

# Save style image if user send as a photo
@dp.message_handler(content_types=['photo'], state=Images.style_img)
async def download_if_send_as_photo(message, state: FSMContext):
    file = await bot.get_file(message.photo[-1].file_id)
    photo = await bot.download_file(file.file_path)
    await Images.style_img.set()
    async with state.proxy() as data:
        data['style_img'] = photo

    data = await state.get_data()
    content_image = data.get('content_img')
    style_image = data.get('style_img')
    if data.get('model') == 'Style transfer':
        output_image = StyleTransfer(style_image, content_image).get_output()
        output_image.save('output.jpg')
    elif data.get('model') == 'Fast style transfer':
        StyleTransfer2(content_image, style_image).get_output()

    await state.finish()

    await message.answer('Your mix photo by Neural Style Transfer')
    await types.ChatActions.upload_photo()
    media = types.MediaGroup()
    media.attach_photo(types.InputFile('output.jpg'))
    await message.answer_media_group(media=media)




if __name__ == '__main__':
    start_polling(dp, skip_updates=True)
'''
    start_webhook(dispatcher=dp,
                  webhook_path=WEBHOOK_PATH,
                  on_startup=on_startup,
                  on_shutdown=on_shutdown,
                  skip_updates=True,
                  host=WEBAPP_HOST,
                  port=WEBAPP_PORT,
                  )
'''