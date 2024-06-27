import os
import aiohttp
import asyncio
from requests import get
from utils.extract import get_comick_chapter_images, get_mangafire_chapter_images, locate_comick_starting_ch, \
                           locate_mangafire_starting_ch
from utils.generate_pdf import generate_pdf_from_folders, create_full_page_table, populate_index_table, merge_pdfs, \
    generate_hyperlinks
from utils.tools import find_missing_numbers



# track failed downloads
failed_downloads = {}


async def download_image(session, url, path):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                img_data = await response.read()
                with open(path, 'wb') as f:
                    f.write(img_data)
            else:
                raise Exception(f"Failed to download {url} with status {response.status}")
    except Exception as e:
        print(f"Attempt to download {url} failed: {e}")
        # Add to failed downloads
        failed_downloads[path] = url


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


def retry_failed_downloads(ch_dict):

    for key, image_list in failed_downloads.items():
        folder_name = key
        missing_images = find_missing_numbers(folder_name)
        os.chdir(folder_name)
        i = 0
        # Download each image in the image_list
        for image_url in image_list:
            # Get the image filename from the URL
            image_path = f'{missing_images[i]}.{image_url.split(".")[-1]}'

            response = get(image_url)

            if response.status_code == 200:
                # Open a new file in binary write mode and write the image content
                with open(image_path, 'wb') as image_file:
                    image_file.write(response.content)
            i+= 1
        os.chdir('..')


def run_download_images(ch_dict: dict):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(download_images(ch_dict))
    else:
        loop.create_task(download_images(ch_dict))
    if failed_downloads:
        retry_failed_downloads(ch_dict)


def download_poster(poster_link, manga_name):
    if os.path.exists(manga_name):
        os.chdir(manga_name)
    else:
        os.makedirs(manga_name)
        os.chdir(manga_name)
    poster_data = get(poster_link).content
    poster_path = f'Poster.{poster_link.split(".")[-1]}.'
    with open(poster_path, 'wb') as f:
        f.write(poster_data)
    return poster_path


def download_chapters(site_name, starting_ch, number_of_downloads ,manga_url, manga_name, generate_pdf):
    if site_name == 'ComicK':
        links_dict = get_comick_chapter_images(locate_comick_starting_ch(manga_url, starting_ch), number_of_downloads)
    else:
        links_dict = get_mangafire_chapter_images(locate_mangafire_starting_ch(manga_url, starting_ch), number_of_downloads)
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
