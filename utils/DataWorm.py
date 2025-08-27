import requests
from urllib.parse import urlencode
import datetime
from dateutil.relativedelta import relativedelta


class DataWorm:
    def __init__(self, cd , API_KEY=None, region="europe", start=0, match_count=20):
        if (API_KEY is None):
            raise ValueError("Need to initialize an API key!!!")
        self.key = API_KEY
        self.start = start
        self.match_count = match_count
        self.region="europe"
        self.DM = DataMaker_obj
        self.version = self.get_version()

    def if_aram(self, match_info):
        if (match_info["info"]["gameMode"] != "ARAM"):
            return False
        return True
    
    def get_version(self):
        response = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()
        return response[0]

    def try_to_connect(api_url, params):
        for i in range(5):
            try:
                response = requests.get(api_url, params=urlencode(params))
                response.raise_for_status()
                successfulGet = 1
                
            except requests.exceptions.RequestException as e:
                print(f"Issue getting summoner data from API: {e}\n {i} attempt...")
        return response
        
    def search_by_puuid(self, puuid=None):
        if (puuid is None):
            raise ValueError("Puuid can't be None!!!")
        
        params = {
        "start" : self.start,
        "count" : self.match_count,
        "api_key" : self.key
        }
        
        api_url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        
        response = self.try_to_connect(api_url, params)
        
        return response.json() 
        
        
    def metadata_to_puuid(self, tagLine=None, gameName=None):
        if ((tagLine is None) or (gameName is None)):
            raise ValueError("Tagline and Gamename must be not None!!!")
        
        params = {
            "api_key": self.key
        }
        api_url = f"https://{self.region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
        
        response = self.try_to_connect(api_url, params)
        
        return response.json()["puuid"]
    
    def get_match_info(self, match_id):
        params = {
            "api_key" : self.key 
        }
        api_url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        
        response = self.try_to_connect(api_url, params)
        
        return response.json()
        
    
        
    def set_key(self, API_KEY):
        self.key = API_KEY
    
    def set_region(self, region):
        self.region = region
    
    def set_start(self, start):
        self.start = start
    
    def set_match_count(self, match_count):
        self.match_count = match_count
    
    def recursive_search(self, LOL_db, params, start_puuid=None, start_tag=None, start_name=None):
        """
        params: Dict(month: int(or None), version: str(or None))
        """

        current_date = datetime.datetime.now()

        m_months_ago = current_date - relativedelta(months=m-1)
        m_months_ago = m_months_ago.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        criterion = {
            "month" : 1,
            "version" : self.version
        }

        if not(params["month"] is None):
            criterion["month"] = params["month"]

        if not(params["version"] is None):
            criterion["version"] = params["version"]
        
        if not(start_puuid is None):
            current_puuid = start_puuid
        
        if (not(start_tag is None) and not(start_name is None) and (start_puuid is None)):
            current_puuid = self.metadata_to_puuid(start_tag, start_name)
        
        else:
            raise ValueError("Searching data must be only by one way!!!")
        
        stillCont = 1
        puuids_players = set()
        already_visit_players = set()
        while(stillCont or len(puuids_players)):
            match_list = self.search_by_puuid(current_puuid) # Извлекаем список матчей по puuid или tag и name игрока
            for match_id in match_list: # Проходимся по списку
                is_not_in_db = LOL_db.match_scan(match_id) # Проверяем, есть ли матч в базе данных
                if (is_not_in_db and not(self.if_aram(match_id))):
                    match_info = self.get_match_info(match_id) # Берем данные о матче
                    version = match_info["info"]["gameVersion"].split(".") # Определяем версию игры,
                    version = f"{version[0]}.{version[1]}" # в которой проводился матч
                    match_date = datetime.datetime.fromtimestamp(match_info["info"]["gameCreation"] / 1000.0).month # Определяем дату создания матча
                    if ((version in criterion["version"]) and (match_date >= m_months_ago)): 
                        # Если матч удовлетворяет критериям отбора - добавляем информацию в БД
                        summoners_data = self.DM.make_summoners_data(match_info)
                        match_data = self.DM.make_match_data(match_info)
                        self.DM.add_data(summoners_data, match_data)
                        puuids_players.update(match_info["metadata"]["participants"])
                    else:
                        stillCont = 0
                        break
            self.start += self.match_count
            # Если у данного игрока не осталось актуальных по критериям матчей:
            if (not(stillCont) and len(puuids_players)):
                already_visit_players.add(current_puuid)
                current_puuid = None
                while (current_puuid is None):
                    new_start = next(iter(puuids_players))
                    if not(new_start in already_visit_players):
                        current_puuid = new_start
                        self.start = 0
                        stillCont = 1
                    puuids_players.remove(new_start)

# Написать тест к данному классу

            
                    

            
            


            
