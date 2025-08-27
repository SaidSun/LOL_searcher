import requests
from urllib.parse import urlencode
import pandas as pd
import utils.DataMaker
import utils.DataWorm
import utils.SQLOL


API_KEY="RGAPI-a58032b1-4c17-4a6a-b2b6-7dda4aee0127"
DEFAULT_REGION_CODE="euw1"
DEFAULT_REGION="europe"


# ## Take summoner puuid

def get_summoner_info(tagLine=None, gameName=None, region=DEFAULT_REGION):
    if not(tagLine):
        tagLine = input("Summoner tag: ")
    if not(gameName):
        gameName = input("Summoner name: ")
    params = {
        "api_key": API_KEY
    }
    api_url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    try:
        response = requests.get(api_url, params=urlencode(params))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Issue getting summoner data from API: {e}")
        return None


# ## Take summoner matches ids

def get_summoner_match_id(puuid=None, start=0, match_count=20, region=DEFAULT_REGION):
    if not(puuid):
        puuid = input("Summoner puuid: ")
    params = {
        "start" : start,
        "count" : match_count,
        "api_key" : API_KEY
    }
    api_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    try:
        response = requests.get(api_url, params=urlencode(params))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Issue getting summoner data from API: {e}")
        return None

# ## Take match info

def get_match_info(match_id=None, region=DEFAULT_REGION):
    if not(match_id):
        match_ids = input("Match id: ")
    params = {
        "api_key" : API_KEY 
    }
    api_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    try:
        response = requests.get(api_url, params=urlencode(params))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Issue getting summoner data from API: {e}")
        return None


# ## Choose not ARAM match

# For json format data
def if_aram(match_info):
    if (match_info["info"]["gameMode"] != "ARAM"):
        return False
    return True


## Main code

summoner_tag = "FOXX"
summoner_name = "Cress"

summoner = get_summoner_info(tagLine=summoner_tag, gameName=summoner_name)
if not(summoner is None):
    print(summoner["puuid"], "\n")
else:
    print("Error with taking puuid summoner! \n")

summoner_puuid = summoner["puuid"]

summoner_matches = get_summoner_match_id(puuid=summoner_puuid)
print(summoner_matches, "\n")

DM = utils.DataMaker.DataMaker()
sqll = utils.SQLOL.LoLdatabase()

for match_id in summoner_matches:
    match_info = get_match_info(match_id=match_id)
    print(f"Version: {match_info["info"]["gameVersion"]}\n")
    print(f"Count of participants: {len(match_info["info"]["participants"])}\n")
    print(f"Is ARAM?: {if_aram(match_info)}\n")
    if not(if_aram(match_info)):
        summoners_data = DM.make_summoners_data(match_info)
        match_data = DM.make_match_data(match_info)
        # DM.add_data(summoners_data, match_data)

print(f"Is match {summoner_matches[0]} in db?: ", sqll.match_scan(summoner_matches[0]))


# # План

# ## 1. Создать базу данных, которая будет хранить с каждого матча информацию об рунах и способностях самого игрока, его союзников и его оппонентов(сделать отдельно базы данных под каждого чемпиона)

# ## 2. Создать программу, выполняющую автоматическое заполнение базы данных, с помощью перехода от одного id к другому из матчей

# ## 3. Разработать модкль, определяющую наиболее подходящие предметы для данного матча



