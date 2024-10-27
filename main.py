import re
from dataclasses import dataclass
from pprint import pprint
from typing import Self

from bs4 import BeautifulSoup
from requests import Session


@dataclass(frozen=True, slots=True)
class Product:
    name: str
    url: str
    price: int


# Класс Parser представляет собой парсер для извлечения данных из каталога на сайте maxidom.ru.
class Parser:

    def __init__(self):
        self.__session: Session | None = None

    def close(self):
        self.__session.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args):
        self.close()

    def __parse_page(self, slug: str, page: int, amount: int = 30) -> tuple[bool, list[Product]]:
        """
        Парсинг страницы каталога и извлечение данных о товарах

        :param slug: Уникальный идентификатор сегмента каталога
        :param page: Номер страницы
        :param amount: Количество товаров на странице
        :return: Список товаров страницы
        """

        response = self.__session.get(f'https://www.maxidom.ru/catalog/{slug}/?amount={amount}&PAGEN_2={page}')

        if response.status_code != 200:
            raise ValueError('Ошибка при запросе каталога. Повторите попытку')

        content = response.content

        soup = BeautifulSoup(content.decode(), 'html.parser')

        elements = (
            soup
            .find('div', {'class': 'lvl1__product-body lvl2 hidden lvl1__product-body-searchresult'})
            .find_all('article', {'class': 'l-product l-product__horizontal'})
        )

        page_data: list[Product] = []

        for element in elements:
            name = element.find('span', {'itemprop': 'name'}).text
            product_path = element.find('a', {'itemprop': 'url'}).get('href')
            price = int(element.find('span', {'itemprop': 'price'}).text)

            page_data.append(Product(name, f'https://www.maxidom.ru{product_path}', price))

        return not soup.find('a', {'id': 'navigation_2_next_page'}), page_data

    def parse_catalog(self, url: str) -> list[Product]:
        """
        Парсинг каталога и извлечение данных о всех товарах в данном сегменте каталога

        :param url: Ссылка на сегмент каталога
        :return: Список товаров сегмента каталога
        """

        if not self.__session:
            self.__session = Session()

        match = re.fullmatch(r'^https://www\.maxidom\.ru/catalog/([^/]+)/?', url)

        if not match:
            raise ValueError('Ссылка некорректна')

        slug = match.group(1)

        current_page = 1
        catalog_data: list[Product] = []

        while True:
            is_last_page, page_data = self.__parse_page(slug, current_page)

            catalog_data += page_data

            if is_last_page:
                break

            current_page += 1

        return catalog_data


def main():
    with Parser() as parser:
        result = parser.parse_catalog('https://www.maxidom.ru/catalog/tovary-dlya-poliva/')

    pprint(result)
    print(f'Количество товаров: {len(result)}')


if __name__ == '__main__':
    main()
