import aiohttp
import asyncio
import sys
from datetime import datetime, timedelta

API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"

class CurrencyRateFetcher:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def fetch_rate(self, date: str):
        url = API_URL.format(date=date)
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    print(f"No data available for {date}.")
                    return None
                else:
                    raise ValueError(f"API request failed with status code {response.status}: {await response.text()}")
        except aiohttp.ClientError as e:
            print(f"Network error while fetching data for {date}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for {date}: {e}")
            return None

class ExchangeRateService:
    def __init__(self, fetcher):
        self.fetcher = fetcher

    async def get_rates(self, days: int):
        if days < 1 or days > 10:
            raise ValueError("Days parameter must be between 1 and 10.")

        rates = []
        today = datetime.now()

        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%d.%m.%Y")
            data = await self.fetcher.fetch_rate(date)
            if data:
                extracted_rates = self._extract_rates(data, date)
                if extracted_rates:
                    rates.append(extracted_rates)

        return rates

    @staticmethod
    def _extract_rates(data, date):
        result = {date: {}}
        for rate in data.get("exchangeRate", []):
            if rate["currency"] in ["EUR", "USD"]:
                result[date][rate["currency"]] = {
                    "sale": rate.get("saleRate"),
                    "purchase": rate.get("purchaseRate")
                }
        return result if result[date] else None

async def main():
    if len(sys.argv) != 2:
        print("Usage: py main.py <days>")
        return

    try:
        days = int(sys.argv[1])
    except ValueError:
        print("<days> must be an integer.")
        return

    if days < 1 or days > 10:
        print("Please provide a number of days between 1 and 10.")
        return

    async with CurrencyRateFetcher() as fetcher:
        service = ExchangeRateService(fetcher)
        try:
            rates = await service.get_rates(days)
            print(rates)
        except ValueError as e:
            print(e)

if __name__ == "__main__":
    asyncio.run(main())
