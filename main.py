import discord
import os
import requests
import re
import time
from bs4 import BeautifulSoup as bs
from replit import db


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
# for working with embedded objects
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
  media['watched'] = False
  # detect if it is a TV Series ifso: raise error to prevent issues
  tvpattern = re.compile(r'TV (Mini )?Series')
  if tvpattern.search(embed_object.title):
    raise ValueError
  return media

def update_movies(movie_dict, user, watched=False):
  string_key = movie_dict["meta_suffix"]
  if string_key in db.keys():
    movie = db[string_key]
    if user in movie["watch_list"]:
      print("You've already nominated this movie")
      return
    movie["watch_list"].append(user)
    db[string_key] = movie
    print(db[string_key])
  else:
    movie_dict["watch_list"] = [user]
    db[string_key] = movie_dict

def watch_list(command_string, user):
  string_key = command_string.strip("!watchlist ")
  if string_key in db.keys():
    movie = db[string_key]
    if movie['watched'] == True:
      return("Sorry, we've already watched that movie")
    movie["watch_list"].append(user)
    return(string_key + " added to your watchlist, I'll @ you when watching.")
  else:
    print(f'''not found, here is a list of watchlistable movies:''')
    for key in db.keys():
      print(key)

# event decoraters
# notify as ready
nominations = {}
@client.event
async def on_ready():
  print('Movies!')
  print(f'We have logged in as {client.user}')

@client.event
async def on_message(msg):
  response_msg = None
  if str(msg.channel) == 'moviebottest' and str(msg.author) in admins:
    if msg.content.startswith('!test'):
      response_msg = f'Testing Connection. \n We are connected to the {msg.channel}'
# Check embedded messages
    if msg.embeds:
      embedlist = []
      for embeded in msg.embeds:
        try:
          embedlist.append(handling_embeds(embeded))
        except ValueError:
          response_msg = 'Error occurred, Is this a movie?'
      for media in embedlist:
        ratings = get_rating(media)
        update_movies(media, str(msg.author))
        response_msg = f'` {media["title"]} `\n` | {ratings[0]}/100 | {ratings[1]}/10 | `'

    if msg.content.startswith('!shutdown'):
      await msg.channel.send(f'Shutting Down Robot \n {msg.author}')
      print('/////////////////SHUT DOWN COMMENCED==========================>')
      await client.close()
    if msg.content.startswith('!deletedb'):
      for x in db.keys():
        del db[x]
    # PRINT any response message generated.
    if response_msg is not None:
      await msg.channel.send(response_msg)
      
  elif str(msg.channel) == 'reccomended-movies' and msg.content.startswith('!nominate'):
    print("we're in nominate")
    nominations = nominate(msg.content)
    response_msg = f'{str(msg.author)} has nominated {nomination} \n {nominations}'


client.run(bot_token)