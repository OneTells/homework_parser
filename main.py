import re
from typing import Self

from bs4 import BeautifulSoup
from requests import Session


class Parser:

    def __init__(self):
        self.session: Session | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args):
        self.session.close()

    def __parse_page(self, slug: str, page: int, amount: int = 30) -> tuple[bool, dict[str, int]]:
        response = self.session.get(f'https://www.maxidom.ru/catalog/{slug}/?amount={amount}&PAGEN_2={page}')

        if response.status_code != 200:
            raise ValueError('Ошибка при запросе каталога. Повторите попытку')

        content = response.content

        soup = BeautifulSoup(content.decode(), 'html.parser')

        elements = (
            soup
            .find('div', {'class': 'lvl1__product-body lvl2 hidden lvl1__product-body-searchresult'})
            .find_all('article', {'class': 'l-product l-product__horizontal'})
        )

        page_data: dict[str, int] = {}

        for element in elements:
            name = element.find('span', {'itemprop': 'name'}).text.capitalize()
            price = int(element.find('span', {'itemprop': 'price'}).text)

            page_data |= {name: price}

        return not soup.find('a', {'id': 'navigation_2_next_page'}), page_data

    def parse_catalog(self, url: str) -> dict[str, int]:
        if not self.session:
            self.session = Session()

        match = re.fullmatch(r'^https://www\.maxidom\.ru/catalog/([^/]+)', url)

        if not match:
            raise ValueError('Ссылка некорректна')

        slug = match.group(1)

        current_page = 1
        catalog_data: dict[str, int] = {}

        self.session = Session()

        while True:
            is_last_page, page_data = self.__parse_page(slug, current_page)

            catalog_data |= page_data

            if is_last_page:
                break

            current_page += 1

        return catalog_data


def main():
    with Parser() as parser:
        result = parser.parse_catalog('https://www.maxidom.ru/catalog/sadovaya-tehnika')

    print(result)
    print(len(result))


if __name__ == '__main__':
    main()
