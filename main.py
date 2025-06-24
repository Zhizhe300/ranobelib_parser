from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from lxml import etree
import datetime


def create_fb2_book(title, author, chapters):
    """FB2 structure"""
    root = etree.Element("FictionBook", xmlns="http://www.gribuser.ru/xml/fictionbook/2.0")

    # Description section
    description = etree.SubElement(root, "description")
    title_info = etree.SubElement(description, "title-info")
    book_title = etree.SubElement(title_info, "book-title")
    book_title.text = title
    author_elem = etree.SubElement(title_info, "author")
    author_first = etree.SubElement(author_elem, "first-name")
    author_first.text = author
    date = etree.SubElement(title_info, "date", value=datetime.datetime.now().strftime("%Y-%m-%d"))
    date.text = datetime.datetime.now().strftime("%d.%m.%Y")
    lang = etree.SubElement(title_info, "lang")
    lang.text = "ru"

    # Body section
    body = etree.SubElement(root, "body")

    # Add chapters
    for chapter_title, content in chapters:
        section = etree.SubElement(body, "section")
        title_elem = etree.SubElement(section, "title")
        p = etree.SubElement(title_elem, "p")
        p.text = chapter_title

        # Add content paragraphs
        for paragraph in content.split("\n"):
            if paragraph.strip():
                p = etree.SubElement(section, "p")
                p.text = paragraph

    return etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)


def parse_chapter(driver):
    """Parse current chpt"""
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "lp_bu")))
    # Get title
    chapter_title = driver.find_element(By.CLASS_NAME, "lp_bu").text.strip()

    # Parse chpt content
    content_div = driver.find_element(By.CLASS_NAME, "node-doc")
    soup = BeautifulSoup(content_div.get_attribute("outerHTML"), "html.parser")

    # Extract chpt text
    paragraphs = []
    for p in soup.find_all("p", class_="node-paragraph"):
        text = p.get_text(separator="\n", strip=True)
    if text:
        paragraphs.append(text)

    return chapter_title, "\n\n".join(paragraphs)


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Starter-page
        start_url = "https://ranobelib.me/ru/26690--omniscient-readers-viewpoint-novel/read/v1/c0?bid=17824"
        driver.get(start_url)

        chapters = []
        chapter_count = 0

        while True:
            chapter_count += 1
            print(f"Chapter {chapter_count}...")

            # Parse current chapter
            title, content = parse_chapter(driver)
            chapters.append((title, content))

            # Check if next chapter exists
            next_buttons = driver.find_elements(By.XPATH,
                                                "//a[contains(@class, 've_b6') and not(contains(@disabled, 'true'))]")
            if not next_buttons:
                print("No next chapter")
                break

            # Next chapter
            next_url = next_buttons[0].get_attribute("href")
            driver.get(next_url)
            time.sleep(2)

        # Create FB2 doc
        book_title = "Точка зрения Всеведущего читателя"
        book_author = "Сингсонг"
        fb2_content = create_fb2_book(book_title, book_author, chapters)

        # write out
        output_file = f"{book_title.replace(' ', '_')}.fb2"
        with open(output_file, "wb") as f:
            f.write(fb2_content)

        print(f"\nSuccesfully downloaded {len(chapters)} chapters into: {output_file}")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()