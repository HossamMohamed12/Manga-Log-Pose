import os
import sys
import threading

from tkinter import filedialog
import customtkinter as ctk
from CTkScrollableDropdown import *
from PIL import Image

from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.download import download_chapters, download_poster


# https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class RedirectText:
    def __init__(self, widget):
        self.widget = widget

    def write(self, string):
        self.widget.insert(ctk.END, string)
        self.widget.see(ctk.END)  # Scroll to the end

    def flush(self):
        pass  # Required for file-like object, but can be left empty


class MangaDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Manga Log Pose')
        self.iconbitmap(resource_path('assets\\log-pose.ico'))
        self.geometry('780x580')

        ctk.set_appearance_mode('dark')

        # Configure the grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=4)

        # Adding main frames
        self.inputs_frame = ctk.CTkFrame(master=self, width=100, height=350)
        self.inputs_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        self.poster_frame = ctk.CTkFrame(master=self, width=400, height=350)
        self.poster_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        self.logs_frame = ctk.CTkFrame(master=self, height=50)
        self.logs_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        # Add elements to inputs_frame
        self.browse_frame = ctk.CTkFrame(master=self.inputs_frame, border_width=1)
        self.browse_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

        self.browse_label = ctk.CTkLabel(master=self.browse_frame, text="Browse:", anchor="w", justify="left")
        self.browse_label.pack(padx=5, pady=5, fill="x")

        self.browse_button = ctk.CTkButton(master=self.inputs_frame, text="Browse", command=self.browse_files)
        self.browse_button.grid(row=0, column=0, padx=170, pady=10, sticky='w')

        # creating search data frame

        self.search_data_frame = ctk.CTkFrame(master=self.inputs_frame, border_width=0, fg_color='transparent')
        self.search_data_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

        self.manga_entry = ctk.CTkEntry(master=self.search_data_frame, placeholder_text="Enter Manga Title")
        self.manga_entry.grid(row=0, column=0, padx=5, pady=5)

        self.sites_dropdown = ctk.CTkComboBox(master=self.search_data_frame, values=['ComicK', 'Mangafire'])
        self.sites_dropdown.grid(row=0, column=1, padx=10, pady=5)
        self.sites_dropdown.set('Sites')

        self.search_button = ctk.CTkButton(master=self.search_data_frame, text="Search",
                                           command=self.start_search_func)
        self.search_button.grid(row=0, column=2, padx=5, pady=5)

        self.starting_chapter_frame = ctk.CTkFrame(master=self.inputs_frame, border_width=0, fg_color='transparent')
        self.starting_chapter_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

        self.start_chapter_label = ctk.CTkLabel(master=self.starting_chapter_frame, text="Starting Chapter:")
        self.start_chapter_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        self.chapter_dropdown = ctk.CTkComboBox(master=self.starting_chapter_frame, values=[])
        self.chapter_dropdown.grid(row=0, column=1, padx=55, pady=5)
        self.chapter_dropdown.set('Chapters')

        self.num_of_downloads_frame = ctk.CTkFrame(master=self.inputs_frame, border_width=0, fg_color='transparent')
        self.num_of_downloads_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

        self.num_chapters_label = ctk.CTkLabel(master=self.num_of_downloads_frame, text="Number of Chapters:")
        self.num_chapters_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.num_chapters_entry = ctk.CTkEntry(master=self.num_of_downloads_frame)
        self.num_chapters_entry.grid(row=0, column=1, padx=22, pady=5)

        self.pdf_checkbox = ctk.CTkCheckBox(master=self.inputs_frame, text="Generate PDF File")
        self.pdf_checkbox.grid(row=8, column=0, padx=10, pady=5, sticky='w')

        self.download_button = ctk.CTkButton(master=self.inputs_frame, text="Download",
                                             command=self.start_download_func)

        self.download_button.grid(row=9, column=0, padx=20, pady=20)

        self.manga_poster_label = ctk.CTkLabel(master=self.poster_frame, text="")
        self.manga_poster_label.pack(pady=20)

        self.logs_textbox = ctk.CTkTextbox(master=self.logs_frame)
        self.logs_textbox.pack(fill="both", expand=True, padx=10, pady=10)

        # Redirect stdout and stderr to the textbox
        sys.stdout = RedirectText(self.logs_textbox)
        sys.stderr = RedirectText(self.logs_textbox)

        self.chapters_list = None
        self.starting_ch = None
        self.manga_url = None

    # adding functions to gui elements
    def browse_files(self):
        directory = filedialog.askdirectory()
        if directory:
            self.browse_label.configure(text=directory)
            os.chdir(directory)

    def start_search_func(self):
        if self.sites_dropdown.get() == 'ComicK':
            thread = threading.Thread(target=self.search_comick, args=(self.manga_entry.get(),))
            thread.start()
        else:
            thread = threading.Thread(target=self.search_mangafire, args=(self.manga_entry.get(),))
            thread.start()

    def start_download_func(self):
        thread = threading.Thread(target=download_chapters, args=(self.sites_dropdown.get(),
                                                                  self.chapter_dropdown.get(),
                                                                  self.num_chapters_entry.get(),
                                                                  self.manga_url,
                                                                  self.manga_entry.get(),
                                                                  self.pdf_checkbox.get()))
        thread.start()

    def search_comick(self, manga_name: str):
        driver = Driver(uc=True, headless=True)
        driver.get('https://comick.io/home')
        # searching for a manga
        open_search_box = driver.find_element(By.XPATH, "//button[@title='Search']")
        open_search_box.click()
        search_box = driver.find_element(By.XPATH, "//input[@type='search']")
        search_box.send_keys(manga_name)
        manga_url = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                    "(//li[@role='option']/a)[2]"))).get_attribute(
            'href')
        driver.get(f'{manga_url}?lang=en')
        poster_link = driver.find_element(By.XPATH, "//a/img").get_attribute('src')
        driver.execute_script("window.scrollTo(0, 1800)")
        final_ch = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//td/a//span"))).text
        final_ch_num = final_ch.split('.')[1]
        self.manga_url = driver.current_url
        self.chapters_list = [str(x) for x in range(1, int(final_ch_num) + 1)]
        CTkScrollableDropdown(attach=self.chapter_dropdown, values=self.chapters_list, justify="left",
                              button_color="transparent")
        poster_path = download_poster(poster_link, self.manga_entry.get())
        manga_poster = Image.open(poster_path)
        manga_poster.resize((300, 300), Image.Resampling.LANCZOS)
        manga_poster_ctk = ctk.CTkImage(light_image=manga_poster, dark_image=manga_poster, size=(250, 350))

        self.manga_poster_label.configure(image=manga_poster_ctk, text="")
        self.manga_poster_label.image = manga_poster_ctk
        print(f'searched for {manga_name} manga successfully')
        driver.close()

    def search_mangafire(self, manga_name: str):
        driver = Driver(uc=True, headless=True)
        driver.get('https://mangafire.to/')

        # searching for a manga
        search_box = driver.find_element(By.XPATH, "//input[@placeholder='Search manga...']")
        search_box.send_keys(manga_name)
        manga_url = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                    "//a[@class = 'unit']"))).get_attribute(
            'href')
        driver.get(manga_url)
        poster_link = driver.find_element(By.XPATH, "//div [@class='poster']//img").get_attribute('src')
        final_ch_num = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                       '//div[@data-name="chapter"]//li'))).get_attribute(
            'data-number')
        self.manga_url = driver.current_url
        self.chapters_list = [str(x) for x in range(1, int(final_ch_num) + 1)]
        CTkScrollableDropdown(attach=self.chapter_dropdown, values=self.chapters_list, justify="left",
                              button_color="transparent")
        poster_path = download_poster(poster_link, self.manga_entry.get())
        manga_poster = Image.open(poster_path)
        manga_poster.resize((300, 300), Image.Resampling.LANCZOS)
        manga_poster_ctk = ctk.CTkImage(light_image=manga_poster, dark_image=manga_poster, size=(250, 350))

        self.manga_poster_label.configure(image=manga_poster_ctk, text="")
        self.manga_poster_label.image = manga_poster_ctk
        print(f'searched for {manga_name} manga successfully')
        driver.close()
