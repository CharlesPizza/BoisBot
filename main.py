import discord
import os
import requests
import re
import time
from bs4 import BeautifulSoup as bs

client = discord.Client()
bot_token = os.environ['TOKEN']

def get_response(my_url):
    time.sleep(6)
    response = requests.get(my_url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = bs(response.text, 'lxml')
    return(soup)

def get_rating(movie_dict):
    prefix_url = 'https://www.metacritic.com/movie/'
    title = movie_dict['title']
    full_url = prefix_url+movie_dict['title']
    soup = get_response(full_url)
    print('===================================================================')
    ratings = []
    anchors = soup.find_all('a', class_ = 'metascore_anchor' )
    for rating in anchors[0:2]:
        ratings.append(rating.find('span').text )
    """
    num_ratings = soup.find_all('span', class_ = 'based_on')
    num_ratings = [i for i in num_ratings.text]
    print(f'{movie_dict["title"]} has a...')
    """
    return ratings


def get_title(imdb_url):
    movie_dict = {}
    response = requests.get(imdb_url, headers={'User-Agent': 'Mozilla/5.0'} )
    soup = bs(response.text, 'lxml')
    title = soup.find('h1', 
        class_ = re.compile('^TitleHeader__TitleText.*') ).text
        # class_ = 'TitleHeader__TitleText-sc-1wu6n3d-0 dxSWFG' ).text.lower()
    title = title.replace(' ', '-')
    title = title.lower()
    movie_dict['link'] = imdb_url
    movie_dict['title'] = title
    movie_dict['year'] = soup.find('span',
        'TitleBlockMetaData__ListItemText-sc-12ein40-2 jedhex' )
    return(movie_dict)

# event decoraters
@client.event
async def on_ready():
    print('Movies!')
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return
    if msg.content.startswith('!test'):
        await msg.channel.send('Testing Connection in 1... 2... 3...')
        await msg.channel.send(f'We are connected to {msg.channel}')

    if msg.content.startswith('https://'):
        movie_dict = get_title(msg.content)
        ratings = get_rating(movie_dict)
        print(movie_dict)
        await msg.channel.send(f'{movie_dict["link"]}')
        await msg.channel.send(f'` {movie_dict["title"]} `')
        await msg.channel.send(f'` | {ratings[0]}/100 | {ratings[1]}/10 | `')

    if msg.content.startswith('!shutdown'):
        await msg.channel.send('Shutting Down Robot')
        print('/////////////////SHUT DOWN COMMENCED==========================>')
        await client.close()


client.run(bot_token)