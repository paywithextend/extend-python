import asyncio
import os

from dotenv import load_dotenv

from extend import ExtendClient

load_dotenv()

# Initialize the client
api_key = os.getenv("EXTEND_API_KEY")
api_secret = os.getenv("EXTEND_API_SECRET")
extend = ExtendClient(api_key, api_secret)


async def test_virtual_cards():
    cards = await extend.virtual_cards.get_virtual_cards()
    print("Virtual Cards:")
    print(cards)
    return cards


async def test_transactions():
    txns = await extend.transactions.get_transactions()
    print("Transactions:")
    print(txns)
    return txns


async def main():
    await test_virtual_cards()
    # await test_transactions()


if __name__ == "__main__":
    asyncio.run(main())
