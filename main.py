import discord
import os
import requests
import re
import time
from bs4 import BeautifulSoup as bs

client = discord.Client()
bot_token = os.environ['TOKEN']
admins = os.environ['ADMINS']

# request.get handling
def get_response(my_url):
  time.sleep(6)
  response = requests.get(my_url, headers={'User-Agent': 'Mozilla/5.0'})
  soup = bs(response.text, 'lxml')
  return(soup)

# get ratings from metacritic
def get_rating(movie_dict):
  prefix_url = 'https://www.metacritic.com/movie/'
  title = movie_dict['meta_suffix']
  full_url = prefix_url+movie_dict['meta_suffix']
  soup = get_response(full_url)
  print('==============================================================')
  ratings = []
  # find aggregated ratings which are encased in anchors
  # this -could- be better off as a regex
  anchors = soup.find_all('a', class_ = 'metascore_anchor' )
  for rating in anchors[0:2]:
      ratings.append(rating.find('span').text )
  return ratings

# prepare a url suffix for metacritic
def get_meta_suffix(rtitle):
  # transformation table
  trans_from = ' '
  trans_to = '-'
  remove_char = '.,/!@#$%^&*)]([\':;'
  # If discord message failed to embed the bot will visit the site to gather data
  if 'https://' in rtitle:
    movie_dict = {}
    response = requests.get(rtitle, headers={'User-Agent': 'Mozilla/5.0'} )
    soup = bs(response.text, 'lxml')
    title = soup.find('h1', 
        class_ = re.compile('^TitleHeader__TitleText.*') ).text
    meta_suffix = title.replace(' ', '-')
    meta_suffix = meta_suffix.lower()
    movie_dict['link'] = rtitle
    movie_dict['title'] = title
    movie_dict['meta_suffix'] = meta_suffix
    movie_dict['year'] = soup.find('span',
        'TitleBlockMetaData__ListItemText-sc-12ein40-2 jedhex' )
    return(movie_dict)
# for working with embedded objects
  else:
# isolate title by cutting off year and imdb signature
    # ex. 'Hellraiser (1987) - IMDb' --> 'Hellraiser'
    search_obj = re.search(r' ?\(\d{4}\)', rtitle)
    meta_suffix = rtitle[:search_obj.start()]
    # prep title for metacritic url
    mytable = meta_suffix.maketrans(trans_from, trans_to, remove_char)
    # special case: +1 --> plus-one
    mytable[43] = '-plus-'
    meta_suffix = meta_suffix.translate(mytable).strip('-').lower()
    return(meta_suffix)
    
# pull information out of embeded message if possible.
def handling_embeds(embed_object):
  media = {}
  media['title'] = embed_object.title
  media['url'] = embed_object.url
  media['description'] = embed_object.description
  media['meta_suffix'] = get_meta_suffix(media['title'])
  # detect if it is a TV Series ifso: raise error to prevent issues
  tvpattern = re.compile(r'TV (Mini )?Series')
  if tvpattern.search(embed_object.title):
    raise ValueError
  return media

# event decoraters
# notify as ready
nominations = {}
@client.event
async def on_ready():
  print('Movies!')
  print(f'We have logged in as {client.user}')

@client.event
async def on_message(msg):
  if str(msg.channel) == 'moviebottest' and str(msg.author) in admins:
    if msg.content.startswith('!test'):
      await msg.channel.send('Testing Connection in 1... 2... 3...')
      await msg.channel.send(f'We are connected to {msg.channel}')  
# Check embedded messages
    if msg.embeds:
      medialist = []
      for embeded in msg.embeds:
        try:
          medialist.append(handling_embeds(embeded))
        except ValueError:
          await msg.channel.send('Error occurred, Is this a movie?')
      for media in medialist:
        ratings = get_rating(media)
        await msg.channel.send(f'{media["url"]}')
        await msg.channel.send(f'` {media["title"]} `')
        await msg.channel.send(f'` | {ratings[0]}/100 | {ratings[1]}/10 | `')
  
# Check failed embeds for https:// this will be replaced with command
    elif msg.content.startswith('https://'):
      movie_dict = get_meta_suffix(msg.content)
      ratings = get_rating(movie_dict)
      print(movie_dict)
      await msg.channel.send(f'{movie_dict["link"]}')
      await msg.channel.send(f'` {movie_dict["title"]} `')
      await msg.channel.send(f'` | {ratings[0]}/100 | {ratings[1]}/10 | `')

    if msg.content.startswith('!shutdown'):
      await msg.channel.send('Shutting Down Robot')
      await msg.channel.send(msg.author)
      print('/////////////////SHUT DOWN COMMENCED==========================>')
      await client.close()
  
  elif str(msg.channel) == 'reccomended-movies' and msg.content.startswith('!nominate'):
    print("we're in nominate")
    nomination = str(msg.content)
    if nomination in nominations:
      nominations[nomination] += 1
    else:
      nominations[nomination] = 1
    await msg.channel.send(f'{str(msg.author)} has nominated {nomination}')
    await msg.channel.send(nominations)

client.run(bot_token)