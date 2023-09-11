import discord
from discord.ext import commands
import random
import requests
import asyncio
import requests
from bs4 import BeautifulSoup


API_KEY = 'RGAPI-927dd190-161b-4e0d-99bb-c33bc9897309'


class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_champion_build(self, champion_name):
        champion_name = champion_name.lower()
        url = f"https://ddragon.leagueoflegends.com/cdn/11.4.1/data/en_US/champion/{champion_name.capitalize()}.json"
        response = requests.get(url)

        if response.status_code != 200:
            return None

        data = response.json()
        champion_data = data['data'][champion_name.capitalize()]
        recommended_build = champion_data['recommended'][0]['blocks']

        items = []
        for block in recommended_build:
            for item in block['items']:
                item_id = item['id']
                items.append(item_id)

        return items
    
    def search_items(self, item_name):
        item_name_encoded = requests.utils.quote(item_name)
        url = f"https://runescape.wiki/api.php?action=query&list=search&format=json&srsearch={item_name_encoded}&srprop=size&srlimit=5"

        response = requests.get(url)

        if response.status_code != 200:
            return None

        data = response.json()
        search_results = data["query"]["search"]

        if len(search_results) == 0:
            return None

        items = []
        for result in search_results:
            items.append({'title': result['title'], 'pageid': result['pageid']})

        return items
    def get_item_id(self, item_name):
        items = self.search_items(item_name)
        if items and len(items) > 0:
            return items[0]['pageid']
        else:
            return None


    ################################################################################ commands ################################################################################
    
    @commands.command()
    async def price(self, ctx, *, item_name):
        items = self.get_item_id(item_name)

        if not items:
            await ctx.send(f"Error: Could not find any items matching '{item_name}'.")
            return

        if len(items) == 1:
            price = self.get_item_price_by_name(items[0]['title'])
            await ctx.send(f"{items[0]['title']}: {price}")
        else:
            message = "Multiple items found. Please choose one by typing its number:\n"
            for i, item in enumerate(items):
                message += f"{i + 1}. {item['title']}\n"

            await ctx.send(message)

            def check(m):
                return m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= len(items)

            try:
                response = await self.bot.wait_for('message', check=check, timeout=30)
                chosen_index = int(response.content) - 1
                chosen_item = items[chosen_index]['title']
                price = self.get_item_price_by_name(chosen_item)
                await ctx.send(f"{chosen_item}: {price}")
            except asyncio.TimeoutError:
                await ctx.send("No response. Please try the command again and choose an item.")


    @commands.command()
    async def roll(self, ctx):
        """Rolls a random number between 1 and 100."""
        random_number = random.randint(1, 100)
        await ctx.send(f'You rolled: {random_number}')



    @commands.command()
    async def question(self, ctx, *, question):
        """Answers a question."""
        responses = ["Yes", "No", "Maybe", "I don't know"]
        response = random.choice(responses)
        await ctx.send(response)



    @commands.command()
    async def wikipedia(self, ctx, *, query):
        """Searches for a Wikipedia article and returns the summary."""
        search_url = 'https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch='
        summary_url = 'https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&format=json&pageids='
        search_results = requests.get(search_url + query).json()
        page_id = search_results['query']['search'][0]['pageid']
        summary = requests.get(summary_url + str(page_id)).json()['query']['pages'][str(page_id)]['extract']
        summary = summary.split('\n')[0] + '\n\n' + summary.split('\n')[1]  # Get the first two lines of the summary
        await ctx.send(summary)



    @commands.command()
    async def joke(self, ctx):
        """Tells a random joke."""
        joke_url = 'https://official-joke-api.appspot.com/random_joke'
        joke = requests.get(joke_url).json()
        await ctx.send(joke['setup'])
        await asyncio.sleep(2)  # Wait for two seconds before sending the punchline
        await ctx.send(joke['punchline'])



    @commands.command()
    async def cat(self, ctx):
        """Sends a random picture of a cat."""
        cat_url = 'https://api.thecatapi.com/v1/images/search'
        cat_data = requests.get(cat_url).json()
        await ctx.send(cat_data[0]['url'])



    @commands.command()
    async def dog(self, ctx):
        """Sends a random picture of a dog."""
        dog_url = 'https://dog.ceo/api/breeds/image/random'
        dog_data = requests.get(dog_url).json()
        await ctx.send(dog_data['message'])



    @commands.command()
    async def chatbot(self, ctx, *, message):
        """Talks to a chatbot."""
        chatbot_url = 'https://api.affiliateplus.xyz/api/chatbot'
        data = {'message': message}
        response = requests.post(chatbot_url, data=data).json()
        await ctx.send(response['message'])



    @commands.command()
    async def fact(self, ctx):
        """Sends a random fact."""
        fact_url = 'https://useless-facts.sameerkumar.website/api'
        fact_data = requests.get(fact_url).json()
        await ctx.send(fact_data['data'])



    @commands.command(name="build")
    async def champion_build(self, ctx, *, champion_name: str):
        build_item_ids = self.get_champion_build(champion_name)
        item_data = self.get_item_data()

        if build_item_ids and item_data:
            build_items = [self.get_item_name(item_data, item_id) for item_id in build_item_ids]
            build_string = "\n".join(build_items)
            await ctx.send(f"Here is a recommended build for {champion_name.capitalize()}:\n\n{build_string}")
        else:
            await ctx.send(f"Could not find a build for {champion_name.capitalize()}. Please check the champion name and try again.")

    @commands.command()
    async def votacao(self, ctx, tempo: int, *opcoes):
        """Abre uma votação. Use o formato '!votacao tempo_opcional opcao1 opcao2 opcao3 ...'"""
        if tempo < 10 or tempo > 300:  # Verifica se o tempo está dentro de limites razoáveis
            await ctx.send("O tempo deve estar entre 10 e 300 segundos.")
            return

        if len(opcoes) < 2:
            await ctx.send("Você precisa fornecer pelo menos duas opções para a votação.")
            return

        await abrir_votacao(ctx, opcoes, tempo)




def setup(bot):
    bot.add_cog(MyCog(bot))

