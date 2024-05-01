from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException, Query
import requests
from bs4 import BeautifulSoup


Base = declarative_base()

class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    tagline = Column(String)
    image_url = Column(String)
    sections = Column(Text)

app = FastAPI()

DATABASE_URL = "postgresql://user:1234@localhost/urlscrap"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def save_book_to_db(title, tagline, image_url, sections):
    db = SessionLocal()
    book = Book(title=title, tagline=tagline, image_url=image_url, sections=sections)
    db.add(book)
    db.commit()
    db.refresh(book)
    db.close()


@app.get("/book_info")
async def get_book_info(book_number: str ):
    print(book_number)
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
    url = f"https://www.alibris.com/booksearch?mtype=B&keyword={book_number}&hs.x=0&hs.y=0"
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch data from the source website")

    soup = BeautifulSoup(response.text, 'html.parser')

    title_section = soup.find('div', class_='product-title')
    title = title_section.find_all('h1', attrs={'itemprop': 'name'})[0].text
    tagline = title_section.find('a', attrs={'itemprop': 'author'}).text

    image_sections = soup.find('div', class_='hero-wrap')
    images = [image['src'] for image in image_sections.findAll('img')]

    sections = soup.find('div', class_='tracks')
    list_sections_1 = sections.find('ol', class_='track-list-limited')
    final_list_section1 = [li.text for li in list_sections_1.findAll("li")]

    list_sections_2 = sections.find('ol', class_='track-list-detail')
    final_list_section2 = [li.text for li in list_sections_2.findAll("li")]

    final_section_list = final_list_section1 + final_list_section2

    books_info = []
    for image_url in images:
        save_book_to_db(title, tagline, image_url, sections)
        book_dict = {
            'Title': title,
            'Tagline': tagline,
            'Image URL': image_url,
            'Sections': final_section_list
        }
        books_info.append(book_dict)

    return books_info


if __name__ == '__main__':
    uvicorn.run(app=app, host='192.168.18.34' , port=11000)