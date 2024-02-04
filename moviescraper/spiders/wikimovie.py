import scrapy
import re

class WikimovieSpider(scrapy.Spider):
    name = "wikimovie"
    allowed_domains = ["ru.wikipedia.org"]
    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"]

    def start_requests(self):
        URL = 'https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту'
        yield scrapy.Request(url=URL, callback=self.parse_category)

    def parse_moviepage(self, response):
        def clean_and_join(selector):
            joined = ', '.join(re.sub(r'\[\d+\]|\[…\]|\n|\xa0|\[d\]', '', text) for text in selector.getall())
            # remove quotation marks
            cleaned = ', '.join([element.strip() for element in joined.split(',') if element.strip() != ''])
            # remove symbols and words
            cleaned = re.sub(r'[/\(\)—]|рус.|англ.|\[en\]|ru|en', '', cleaned)
            # remove extra commas
            cleaned = re.sub(r',\s*,', ',', cleaned)
            # remove trailing spaces and commas
            cleaned = cleaned.rstrip(', ')
            return cleaned
        
        title = response.css('table.infobox th.infobox-above::text').get().strip()
        genre = clean_and_join(response.css('table.infobox tr th:contains("Жанр") + td ::text'))
        director = clean_and_join(response.css('table.infobox tr th:contains("Режисс") + td ::text'))
        country = clean_and_join(response.css('table.infobox tr th:contains("Стран") + td ::text'))
        
        year_text = response.css('table.infobox tr th:contains("Год") + td ::text').getall()
        year = ', '.join([str(year) for year in re.findall(r'\d{4}', ', '.join(year_text))])

        yield {
            'Название': title,
            'Жанр': genre,
            'Режиссёр': director,
            'Страна': country,
            'Год': year,
        }

    def parse_category(self, response):
        # extract movie links from the category page without cartoons and tv shows
        movie_links = response.css('#mw-pages div.mw-category-group a::attr(href)').getall()
        for link in movie_links:
            yield response.follow(link, callback=self.parse_moviepage)

        # check for the link to the next page
        next_page_link = response.css('a:contains("Следующая страница")::attr(href)').get()
        
        # if the next page is found, follow it and continue parsing
        if next_page_link:
            next_page_link = response.urljoin(next_page_link)
            yield response.follow(next_page_link, callback=self.parse_category)   