import requests
from urllib.parse import urlencode
import datetime
from dateutil.relativedelta import relativedelta
import sys
import time


class DataWorm:
    def __init__(self, DataMaker_obj, API_KEY=None, region="europe", start=0, match_count=20):
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

    def try_to_connect(self, api_url, params):
        attemps = 0
        for i in range(5):
            try:
                response = requests.get(api_url, params=urlencode(params))
                response.raise_for_status()
                break     
            
            except requests.exceptions.RequestException as e:
                print(f"Issue getting summoner data from API: {e}\n {i+2} attempt...")   
                attemps += 1     
                time.sleep(10)
        
        if (attemps < 5):
            return response
        else:
            sys.exit(1)
        
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

    def get_next_unvisited_puuid(self, all_puuids):
        not_visited = all_puuids
        if not_visited:
            next_puuid = next(iter(not_visited))
            # time.sleep(2)
            return next_puuid
        return None
    
    def recursive_search(self, LOL_db, params={"month": None, "version": None}, 
                         start_puuid=None, start_tag=None, start_name=None):
        """
        params: Dict(month: int(or None), version: str(or None))
        """
        criterion = {
            "month" : 1,
            "version" : self.version
        }
        current_date = datetime.datetime.now()
        m = current_date.month
        m_months_ago = current_date - relativedelta(months=(m-criterion["month"]+12) % 12)
        m_months_ago = m_months_ago.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        

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
            print(f"Get data from {self.start} to {self.start + self.match_count} about match history from {current_puuid} puuid...")
            # time.sleep(2)

            if not match_list:
                print(f"No matches found for puuid {current_puuid}")
                already_visit_players.add(current_puuid)
                puuids_players = puuids_players - already_visit_players
                current_puuid = self.get_next_unvisited_puuid(puuids_players)
                self.start = 0 
                continue

            for i, match_id in enumerate(match_list): # Проходимся по списку
                print(f"Analysing match number {i+1} - {match_id}:")
                time.sleep(1)
                is_not_in_db = LOL_db.match_scan(match_id) # Проверяем, есть ли матч в базе данных
                match_info = self.get_match_info(match_id) # Берем данные о матче
                puuids_players.update(match_info["metadata"]["participants"])
                if (is_not_in_db and len(match_info["metadata"]["participants"]) == 10):
                    print(f"{match_id} is not in database!")
                    version = match_info["info"]["gameVersion"].split(".") # Определяем версию игры,
                    version = f"{version[0]}.{version[1]}" # в которой проводился матч
                    match_date = datetime.datetime.fromtimestamp(match_info["info"]["gameCreation"] / 1000.0) # Определяем дату создания матча
                    if ((version in criterion["version"]) and (match_date >= m_months_ago) and (is_not_in_db)): 
                        print(f"Adding match {match_id}")
                        time.sleep(1)
                        # Если матч удовлетворяет критериям отбора - добавляем информацию в БД
                        match_data = self.DM.make_match_data(match_info)
                        summoners_data = self.DM.make_summoners_data(match_info)
                        LOL_db.add_data(summoners_data, match_data)
                        print(f"Match {match_id} add!")
                        print("Add new summoners puuid")
                        time.sleep(1)
                    else:
                        stillCont = 0
                        break

            self.start += self.match_count
            # Если у данного игрока не осталось актуальных по критериям матчей:
            if (not(stillCont)):
                already_visit_players.add(current_puuid)
                puuids_players = puuids_players - already_visit_players
                current_puuid = self.get_next_unvisited_puuid(puuids_players)
                print(f"New puuid has been choose: {current_puuid}")
                # time.sleep(2)
                self.start = 0
                stillCont = 1
        print("Searching ended!!!")

# Написать тест к данному классу
if __name__ == "__main__":
    from DataMaker import DataMaker
    from SQLOL import LoLdatabase
    # try:
    DM = DataMaker()
    LOL_db = LoLdatabase()

    API_KEY = input("Enter AI_KEY: ")
    summoner_name = "Cress"
    summoner_tag = "FOXX"
    DataWormix = DataWorm(DM, API_KEY=API_KEY, region="europe", start=0, match_count=20)

    DataWormix.recursive_search(LOL_db, start_name=summoner_name, start_tag=summoner_tag)
    # except Exception as e:
    #     print(f"Error: {e}")
    #     sys.exit(1)