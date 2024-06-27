import os
import aiohttp
import asyncio
from extract import get_chapter_images, search_for_manga
from generate_pdf import generate_pdf_from_folders, create_full_page_table, populate_index_table, merge_pdfs, \
    generate_hyperlinks



async def download_image(session, url, path):
    async with session.get(url) as response:
        img_data = await response.read()
        with open(path, 'wb') as f:
            f.write(img_data)

async def download_images_for_key(session, key, values):
    if os.path.exists(key):
        os.remove(key)
    os.makedirs(key)
    tasks = []
    for i, v in enumerate(values, 1):
        path = os.path.join(key, f'{i}.{v.split(".")[-1]}')
        task = asyncio.create_task(download_image(session, v, path))
        tasks.append(task)
    await asyncio.gather(*tasks)
    print(f'{key} was downloaded successfully')

async def download_images(ch_dict: dict):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for key, values in ch_dict.items():
            task = asyncio.create_task(download_images_for_key(session, key, values))
            tasks.append(task)
        await asyncio.gather(*tasks)

def run_download_images(ch_dict: dict):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(download_images(ch_dict))
    else:
        loop.create_task(download_images(ch_dict))


def download_poster(poster_link, manga_name):
    if os.path.exists(manga_name):
        os.chdir(manga_name)
    else:
        os.makedirs(manga_name)
        os.chdir(manga_name)
    poster_data = get(poster_link).content
    with open(f'Poster.{poster_link.split(".")[-1]}.', 'wb') as f:
        f.write(poster_data)


def download_chapters(starting_ch, number_of_downloads, manga_url, generate_pdf):
    links_dict = get_chapter_images(search_for_manga(manga_url, starting_ch), number_of_downloads)
    print('chapters data collected successfully')
    print('starting download...')
    run_download_images(links_dict)
    if generate_pdf:
        print('generating pdf file...')

        generate_pdf_from_folders(manga_name, 'combined_images.pdf')
        create_full_page_table('full_page_table_example.pdf',
                               populate_index_table(['chapter', 'page number'], 'index_page.txt'))
        merge_pdfs('full_page_table_example.pdf', 'combined_images.pdf', 'merged.pdf')
        generate_hyperlinks('merged.pdf',
                            f'{manga_name} chapters {starting_ch} to {int(starting_ch) + int(number_of_downloads)-1}.pdf')
        trash_files = ['combined_images.pdf', 'full_page_table_example.pdf', 'merged.pdf']
        for t in trash_files:
            os.remove(t)
        print(f'{manga_name} pdf was created successfully')
