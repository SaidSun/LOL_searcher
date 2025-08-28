import pandas as pd
import warnings

warnings.filterwarnings("ignore")
class DataMaker:
    def __init__(self):
        self.CHAMP_FIELD_MAPPING = {"assists" : "assists",
                       "champLevel" : "level",
                       "championName" : "ch_name", 
                       "championId" : "ch_id",
                       "deaths" : "deaths",
                       "individualPosition" : "role",
                       "item0" : "item0",
                       "item1" : "item1",
                       "item2" : "item2",
                       "item3" : "item3",
                       "item4" : "item4",
                       "item5" : "item5", 
                       "item6" : "item6",
                       "kills" : "kills",
                       "totalHeal" : "totalHeal",
                       "totalHealsOnTeammates" : "HealsOnTeam",
                       "magicDamageDealt" : "mDamageDealt",
                       "magicDamageDealtToChampions" : "mDamagetoChamp",
                       "magicDamageTaken" : "mDamageTaken",
                       "physicalDamageDealt" : "pDamageDealt",
                       "physicalDamageDealtToChampions" : "pDamagetoChamp",
                       "physicalDamageTaken" : "pDamageTaken",
                       "trueDamageDealt" : "tDamageDealt",
                       "trueDamageDealtToChampions" : "tDamagetoChamp",
                       "trueDamageTaken" : "tDamageTaken",
                       "teamId" : "team_id",
                       "summoner1Id" : "spell1",
                       "summoner2Id" : "spell2"}
        
    def make_summoners_data(self, match_info):
        info_pd = pd.DataFrame(match_info["info"]["participants"])
        summoners_data = info_pd[list(self.CHAMP_FIELD_MAPPING.keys())]
        print(match_info["metadata"]["participants"])
        summoners_data["puuid"] = match_info["metadata"]["participants"]
        summoners_data["match_id"] = match_info["metadata"]["matchId"]
        perks_data = info_pd["perks"].apply(pd.Series)

        summoners_data["main_runes_style"] = perks_data["styles"].apply(lambda x: x[0]["style"] if len(x) > 0 else None)
        summoners_data["second_runes_style"] = perks_data["styles"].apply(lambda x: x[1]["style"] if len(x) > 0 else None)

        main_runes = perks_data['styles'].apply(lambda x: x[0]['selections'] if len(x) > 0 else [])
        secondary_runes = perks_data["styles"].apply(lambda x: x[1]["selections"] if len(x) > 0 else [])

        for i in range(4):
            summoners_data[f'main_rune{i+1}'] = main_runes.apply(lambda x: x[i]['perk'] if len(x) > i else None)

        for i in range(2):
            summoners_data[f'secondary_rune{i+1}'] = secondary_runes.apply(lambda x: x[i]['perk'] if len(x) > i else None)

        return summoners_data

    def make_match_data(self, match_info):
        winner_id = None
        for team in match_info['info']['teams']:
            if team['win']:
                winner_id = team['teamId']
                break
            
        match_data = {
            'match_id': match_info['metadata']['matchId'],
            'gameDuration': match_info['info']['gameDuration'],
            'gameMode': match_info['info']['gameMode'],
            'gameVersion': match_info['info']['gameVersion'],
            'queueId': match_info['info']['queueId'],
            'winnerId': winner_id
        }
        return pd.DataFrame([match_data])
    
    
    def make_db(self, LOL_db):
        LOL_db.make_db()

    def truncate_db(self, LOL_db):
        LOL_db.truncate_db()

    def add_data(self, summoners_data, match_data, LOL_db):
        LOL_db.add_data(summoners_data, match_data)
    