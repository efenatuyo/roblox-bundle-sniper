import aiohttp, json, asyncio

class Sniper:
    def __init__(self):
        self.data = self.setup()
    
    def setup(self):
        with open('config.json', 'r') as file:
            return json.load(file)
    
    def append_already_bought(self, id):
        self.data["already_bought"].append(id)
        with open("config.json", "w") as file:
            json.dump(self.data, file, indent=4)
        
    async def _get_xcsrf_token(self, cookie) -> dict:
        async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": cookie}) as client:
            response = await client.post("https://accountsettings.roblox.com/v1/email", ssl=False)
            if "x-csrf-token" in response.headers:
                return response.headers["x-csrf-token"]
            else:
                raise Exception("An error occurred while getting the X-CSRF-TOKEN. Could be due to an invalid Roblox Cookie")
    
    async def buy_item(self, session, cookie, productId, expectedSellerId):
        while True:
            try:
                async with session.post(f"https://economy.roblox.com/v1/purchases/products/{productId}", json={"expectedCurrency": 1, "expectedPrice": 0, "expectedSellerId": expectedSellerId}, headers={"X-CSRF-TOKEN": await self._get_xcsrf_token(cookie)}, cookies={".ROBLOSECURITY": cookie}) as response:
                    if response.status == 429 or response.status == 403 : continue
                    return print(f"status code on buying item {productId}: {response.status}")
            except:
                continue
            finally:
                await asyncio.sleep(5)
        
    async def auto_search(self):
        while True:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get("https://catalog.roblox.com/v2/search/items/details?Category=4&Limit=120&MaxPrice=0&SortType=3") as response:
                        if response.status == 200:
                            items = (await response.json()).get("data", [])
                            for item in items:
                                if not (item.get("itemType") == "Bundle" and "productId" in item and "creatorTargetId" in item and item.get("id") not in self.data["already_bought"]):
                                    continue
                                self.append_already_bought(item.get("id"))
                                tasks = []
                                for cookie in self.data["cookies"]:
                                    tasks.append(self.buy_item(session, cookie, item["productId"], item["creatorTargetId"]))
                                await asyncio.gather(*tasks)
                except Exception as e:
                    continue
                finally:
                    await asyncio.sleep(1)

asyncio.run(Sniper().auto_search())