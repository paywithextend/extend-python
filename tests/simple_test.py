import asyncio
import os
from extend_api import ExtendAPI

# Initialize the client
api_key = os.getenv("EXTEND_API_KEY")
api_secret = os.getenv("EXTEND_API_SECRET")
client = ExtendAPI(api_key, api_secret)

async def test_virtual_cards():
    cards = await client.get_virtual_cards()
    print("Virtual Cards:")
    print(cards)
    return cards

async def test_transactions():
    txns = await client.get_transactions()
    print("Transactions:")
    print(txns)
    return txns

async def main():
    await test_virtual_cards()
    # await test_transactions()

if __name__ == "__main__":
    asyncio.run(main())