import requests
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, UploadFile

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get('/pokemon',tags=["Pokemon"])
def get_pokemon(request: Request):
    URL = requests.get('https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0')
    POKEMON_LIST = URL.json()['results']
    return templates.TemplateResponse("pokemon.html", {"request": request, "name": "Hello World", "POKEMON_LIST": POKEMON_LIST})
        

@router.get('/pokemon/{name}',tags=["Pokemon"])
def get_pokemon_name(request: Request, name: str):
    URL = requests.get('https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0')
    POKEMON_LIST = URL.json()['results']
    POKEMON_LIST_NAME = [ pokemon['name'] for pokemon in POKEMON_LIST]
    #print(POKEMON_LIST_NAME)
    if name in POKEMON_LIST_NAME:
        print(f'Pokemon {name} Exists...')
        for pokemon in POKEMON_LIST:
            if pokemon['name'] == name:
                pokemon_name = pokemon['name']
                pokemon_url = pokemon['url']
                return templates.TemplateResponse("pokesingle.html", {"request": request, "name": "Hello World", "pokemon_name": pokemon_name, "pokemon_url": pokemon_url})
    else:
      print(f'Pokemon {name} Dont Exists...')
      return templates.TemplateResponse("pokesingle.html", {"request": request, "name": "Hello World", "pokemon_name": 'Pokemon Name Not Found', "pokemon_url": 'Pokemon URL Not Found'}) 

  