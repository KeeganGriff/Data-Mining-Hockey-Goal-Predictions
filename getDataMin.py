import requests
import pandas as pd
from datetime import datetime, timedelta

team_url = "https://statsapi.web.nhl.com/api/v1/teams"
player_url = "https://statsapi.web.nhl.com/api/v1/people"
schedule_url = "https://statsapi.web.nhl.com/api/v1/schedule"
game_url = "https://statsapi.web.nhl.com/api/v1/game"
standings_url = "https://statsapi.web.nhl.com/api/v1/standings"

def getTeamGameStats(team_id, game_id):
    game = getGame(game_id)
    date = game['gameData']['datetime']['dateTime'].split("T")[0]

    ishome = game['gameData']['teams']['home']['id'] == int(team_id)
    if ishome:
        team = game['liveData']['boxscore']['teams']['home']
        opponent = game['liveData']['boxscore']['teams']['away']
    else:
        team = game['liveData']['boxscore']['teams']['away']
        opponent = game['liveData']['boxscore']['teams']['home']

    # dict_keys(['team', 'teamStats', 'players', 'goalies', 'skaters', 'onIce', 'onIcePlus', 'scratches', 'penaltyBox', 'coaches'])
    # print(team['teamStats'])
    # print()

    # Add all game stats to the dataframe games
    game_data = {'Date': date, 'game_id': game_id}
    team_data = {'Team': team['team']['name'], 'Home': ishome, 'Team Goals': team['teamStats']['teamSkaterStats']['goals'], 'Team Shots': team['teamStats']['teamSkaterStats']['shots'], 'Team PIM': team['teamStats']['teamSkaterStats']['pim'], 'Team PPG': team['teamStats']['teamSkaterStats']['powerPlayGoals'], 'Team PP Opportunities': team['teamStats']['teamSkaterStats']['powerPlayOpportunities'], 'Team Blocked': team['teamStats']['teamSkaterStats']['blocked']}
    opponent_data = {'Opponent': opponent['team']['name'], 'Opponent Goals': opponent['teamStats']['teamSkaterStats']['goals'], 'Opponent Shots': opponent['teamStats']['teamSkaterStats']['shots'], 'Opponent PIM': opponent['teamStats']['teamSkaterStats']['pim'], 'Opponent PPG': opponent['teamStats']['teamSkaterStats']['powerPlayGoals'], 'Opponent PP Opportunities': opponent['teamStats']['teamSkaterStats']['powerPlayOpportunities'], 'Opponent Blocked': opponent['teamStats']['teamSkaterStats']['blocked']}
    return {**game_data, **team_data, **opponent_data}


def getTeamStatsDateRange(team_id, startDate, endDate):
    if endDate < startDate:
        return pd.DataFrame()
    schedule = getScheduleTeamDateRange(team_id, startDate, endDate)
    gameLog = []
    for date in schedule['dates']:
        game_id = str(date['games'][0]['gamePk'])

        gameLog.append(getTeamGameStats(team_id, game_id))

    return pd.DataFrame(gameLog)

def sumTeamGameStats(team_id, startDate, endDate):
    teamStats = getTeamStatsDateRange(team_id, startDate, endDate)
    if teamStats.empty:
        return {'Team GP': 0, 'Team Goals': 0, 'Team Shots': 0, 'Team PIM': 0, 'Team PPG': 0, 'Team PP Opportunities': 0, 'Team Blocked': 0, 'Opponent GP': 0, 'Opponent Goals': 0, 'Opponent Shots': 0, 'Opponent PIM': 0, 'Opponent PPG': 0, 'Opponent PP Opportunities': 0, 'Opponent Blocked': 0}
    teamStats = teamStats.drop(['Date', 'game_id', 'Team', 'Home', 'Opponent'], axis=1)
    teamStats['Team GP'] = 1
    teamStats['Opponent GP'] = 1
    return teamStats.sum()
            
def getTeamRoster(game_id, team='home'):
    game = getGame(game_id)
    return game['liveData']['boxscore']['teams'][team]['players']

def getPlayer(player_id):
    player = requests.get(player_url + "/" + player_id).json()
    return player

def getPlayerGameLog(player_id, season):
    player_stats = requests.get(player_url + "/" + player_id + "/stats?stats=gameLog&season=" + season).json()
    return player_stats

def getPlayerGameLogDateRange(player_id, startDate, endDate):
    player_stats = requests.get(player_url + "/" + player_id + "/stats?stats=gameLog&startDate=" + startDate + "&endDate=" + endDate).json()
    return player_stats

def getPlayerSeasonStats(player_id, season):
    player_stats = requests.get(player_url + "/" + player_id + "/stats?stats=statsSingleSeason&season=" + season).json()
    return player_stats

def getPlayerCareerStats(player_id):
    player_stats = requests.get(player_url + "/" + player_id + "/stats?stats=careerRegularSeason").json()
    return player_stats

def getPlayerGameStats(player_id, game_id):
    game = getGame(game_id)
    date = game['gameData']['datetime']['dateTime'].split("T")[0]

    # If player_id doesn't have ID at the start add it
    if player_id[0]+player_id[1] != 'ID':
        player_id = 'ID' + player_id

    # Get team roster to find player's team
    home_roster = getTeamRoster(game_id, 'home')
    ishome = player_id in home_roster.keys()
    if ishome:
        player = home_roster[player_id]
    else:
        player = game['liveData']['boxscore']['teams']['away']['players'][player_id]

    player['stats']['skaterStats']['timeOnIce'] = int(player['stats']['skaterStats']['timeOnIce'].split(":")[0])*60 + int(player['stats']['skaterStats']['timeOnIce'].split(":")[1])
    player['stats']['skaterStats']['powerPlayTimeOnIce'] = int(player['stats']['skaterStats']['powerPlayTimeOnIce'].split(":")[0])*60 + int(player['stats']['skaterStats']['powerPlayTimeOnIce'].split(":")[1])
    player['stats']['skaterStats']['shortHandedTimeOnIce'] = int(player['stats']['skaterStats']['shortHandedTimeOnIce'].split(":")[0])*60 + int(player['stats']['skaterStats']['shortHandedTimeOnIce'].split(":")[1])
    player['stats']['skaterStats']['evenTimeOnIce'] = int(player['stats']['skaterStats']['evenTimeOnIce'].split(":")[0])*60 + int(player['stats']['skaterStats']['evenTimeOnIce'].split(":")[1])
   
    player_stats = player['stats']['skaterStats']
    return {'Date': date, 'game_id': game_id, 'Goals': player_stats['goals'], 'Assists': player_stats['assists'], 'Scored': player_stats['goals'] > 0, 'Shots': player_stats['shots'], 'PIM': player_stats['penaltyMinutes'], 'PPG': player_stats['powerPlayGoals'], 'PPA': player_stats['powerPlayAssists'], 'PP TOI': player_stats['powerPlayTimeOnIce'], 'EV TOI': player_stats['evenTimeOnIce']}
    
def getPlayerGameStatsDirect(player_id, game):
    date = game['gameData']['datetime']['dateTime'].split("T")[0]
    game_id = str(game['gamePk'])

    # If player_id doesn't have ID at the start add it
    if player_id[0]+player_id[1] != 'ID':
        player_id = 'ID' + player_id

    # Get team roster to find player's team
    home_roster = game['liveData']['boxscore']['teams']['home']['players']
    ishome = player_id in home_roster.keys()
    if ishome:
        player = home_roster[player_id]
    else:
        player = game['liveData']['boxscore']['teams']['away']['players'][player_id]

    # MAYBE SHOULD BE NONE CAUSE IT'S AN ERROR
    if 'skaterStats' not in player['stats'].keys():
        return {}

    player['stats']['skaterStats']['timeOnIce'] = int(player['stats']['skaterStats']['timeOnIce'].split(":")[0])*60 + int(player['stats']['skaterStats']['timeOnIce'].split(":")[1])
    player['stats']['skaterStats']['powerPlayTimeOnIce'] = int(player['stats']['skaterStats']['powerPlayTimeOnIce'].split(":")[0])*60 + int(player['stats']['skaterStats']['powerPlayTimeOnIce'].split(":")[1])
    player['stats']['skaterStats']['shortHandedTimeOnIce'] = int(player['stats']['skaterStats']['shortHandedTimeOnIce'].split(":")[0])*60 + int(player['stats']['skaterStats']['shortHandedTimeOnIce'].split(":")[1])
    player['stats']['skaterStats']['evenTimeOnIce'] = int(player['stats']['skaterStats']['evenTimeOnIce'].split(":")[0])*60 + int(player['stats']['skaterStats']['evenTimeOnIce'].split(":")[1])
   
    player_stats = player['stats']['skaterStats']
    return {'Date': date, 'game_id': game_id, 'ID': player_id, 'Goals': player_stats['goals'], 'Assists': player_stats['assists'], 'Scored': player_stats['goals'] > 0, 'Shots': player_stats['shots'], 'PIM': player_stats['penaltyMinutes'], 'PPG': player_stats['powerPlayGoals'], 'PPA': player_stats['powerPlayAssists'], 'PP TOI': player_stats['powerPlayTimeOnIce'], 'EV TOI': player_stats['evenTimeOnIce']}
    

def getGameAllPlayersStats(game_id):

    game = getGame(game_id)

    game_players = {"home": {}, "away": {}}

    for team in ["home", "away"]:
        for player in game['liveData']['boxscore']['teams'][team]['players']:
            if player[0]+player[1] != 'ID':
                player = 'ID' + player
            game_players[team][player] = getPlayerGameStatsDirect(player, game)

    return game_players

def getPlayerGameStatsDateRange(player_id, startDate, endDate):
    schedule = getPlayerGameLogDateRange(player_id, startDate, endDate)
    gameLog = []
    for date in schedule['dates']:
        game_id = str(date['games'][0]['gamePk'])

        gameLog.append(getPlayerGameStats(player_id, game_id))

    return pd.DataFrame(gameLog)

def sumPlayerGameStats(player_id, startDate, endDate):
    player_stats = getPlayerGameStatsDateRange(player_id, startDate, endDate)
    if player_stats.empty:
        return {'Goals': 0, 'Assists': 0, 'Scored': 0, 'Shots': 0, 'PIM': 0, 'PPG': 0, 'PPA': 0, 'PP TOI': 0, 'EV TOI': 0}
    player_stats = player_stats.drop(['Date', 'game_id'], axis=1)
    player_stats['GP'] = 1
    return player_stats.sum()

def getScheduleSeason(season, gameType="R"):
    schedule = requests.get(schedule_url + "?season=" + season + "&gameType=" + gameType).json()
    return schedule

def getScheduleTeamSeason(team_id, season):
    schedule = requests.get(schedule_url + "?teamId=" + team_id + "&season=" + season).json()
    return schedule

def getScheduleTeamDateRange(team_id, startDate, endDate, gameType="R"):
    schedule = requests.get(schedule_url + "?teamId=" + team_id + "&startDate=" + startDate + "&endDate=" + endDate + "&gameType=" + gameType).json()
    return schedule

def getScheduleDateRange(startDate, endDate, gameType="R"):
    schedule = requests.get(schedule_url + "?startDate=" + startDate + "&endDate=" + endDate + "&gameType=" + gameType).json()
    return schedule

def getSeasonStartDate(season):
    schedule = getScheduleSeason(season)
    return schedule['dates'][0]['date']

def getGame(game_id):
    game = requests.get(game_url + "/" + game_id + "/feed/live").json()
    return game

def createPlayerDataset(player_id, season):
    player = getPlayer(player_id)
    # print(player['people'][0]['fullName'] + ":")
    # print()
    games = []
    gameLog = getPlayerGameLog(player_id, season)
    seasonStart = getSeasonStartDate(season)

    teamGameStatsTotal = {}
    playerGameStatsTotal = {}
    previousGameID = None
    previousDate = None

    # Add each game to the dataframe games and include all game stats and if the player scored or not
    for i in range(len(gameLog['stats'][0]['splits'])-1, 0, -1):
        date = gameLog['stats'][0]['splits'][i]['date']
        game_id = str(gameLog['stats'][0]['splits'][i]['game']['gamePk'])
        ishome = gameLog['stats'][0]['splits'][i]['isHome']

        gameTeam = getGame(game_id)
        if ishome:
            playerTeam = gameTeam['liveData']['boxscore']['teams']['home']
            opponentTeam = gameTeam['liveData']['boxscore']['teams']['away']
        else:
            playerTeam = gameTeam['liveData']['boxscore']['teams']['away']
            opponentTeam = gameTeam['liveData']['boxscore']['teams']['home']

        # Use python library to decrease the date by 1 day
        previousDate = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)
        previousDate = previousDate.strftime('%Y-%m-%d')

        # NEED TO CHECK FOR TEAMS PREVIOS GAME
        if i < len(gameLog['stats'][0]['splits'])-1 and previousGameID != str(gameLog['stats'][0]['splits'][i+1]['game']['gamePk']):
            # Get stats between previous date and current game date
            playerTeamStats = getTeamStatsDateRange(str(playerTeam['team']['id']), previousDate, date)
            print(playerTeamStats)
        elif previousGameID != None:
            playerTeamStats = getTeamGameStats(str(playerTeam['team']['id']), previousGameID)
            teamGameStatsTotal['Team_Team GP'] += 1
        else:
            playerTeamStats = {'Team GP': 0, 'Team Goals': 0, 'Team Shots': 0, 'Team PIM': 0, 'Team PPG': 0, 'Team PP Opportunities': 0, 'Team Blocked': 0, 'Opponent GP': 0, 'Opponent Goals': 0, 'Opponent Shots': 0, 'Opponent PIM': 0, 'Opponent PPG': 0, 'Opponent PP Opportunities': 0, 'Opponent Blocked': 0}
        playerTeamStats = {'Team_' + key: value for key, value in playerTeamStats.items() if key not in ['Date', 'game_id', 'Team', 'TeamID', 'Home', 'Team Faceoff Win %', 'Opponent', 'OpponentID', 'Opponent Faceoff Win %']}
        for key, value in playerTeamStats.items():
            if key in teamGameStatsTotal:
                teamGameStatsTotal[key] += value
            else:
                teamGameStatsTotal[key] = value

        # teamGameStatsTotal = sumTeamGameStats(str(playerTeam['team']['id']), seasonStart, previousDate)
        opponentGameStatsTotal = sumTeamGameStats(str(opponentTeam['team']['id']), seasonStart, previousDate)

        # teamGameStatsTotal = {('Team_' + key): value for key, value in teamGameStatsTotal.items()}
        opponentGameStatsTotal = {('Opponent_' + key): value for key, value in opponentGameStatsTotal.items()}
        
        playerGameStats = getPlayerGameStats(player_id, game_id)
        Scored = playerGameStats['Scored']
        playerGameStats = {key: value for key, value in playerGameStats.items() if key not in ['Date', 'game_id', 'Scored']}
        for key, value in playerGameStats.items():
            if 'Total_' + key in playerGameStatsTotal:
                playerGameStatsTotal['Total_' + key] += value
            else:
                playerGameStatsTotal['Total_' + key] = value


        game_data = {'Date': date, 'game_id': game_id}
        player_game_data = {'Scored': Scored, 'Goals': playerGameStats['Goals'], 'Assists': playerGameStats['Assists']}
        games.append({**game_data, **player_game_data, **playerGameStatsTotal, **teamGameStatsTotal, **opponentGameStatsTotal})

        previousGameID = game_id

    games = pd.DataFrame(games)

    return games

def createSeasonDatabase(season, gameType="R"):
    # Loop through season schedule and add each game to the dataframe games and include each player on each team and track them in a dictionary
    schedule = getScheduleSeason(season, gameType)
    data = []
    playerGameStatsTotal = {}
    playerPrevSeasonStatsTotal = {}
    teamGameStatsTotal = {}
    opponent = {'home': 'away', 'away': 'home'}
    for date in schedule['dates']:
        print(date['date'])
        for game in date['games']:
            # print(game['gamePk'])
            game_id = str(game['gamePk'])
            teams = {'home': game['teams']['home']['team']['id'], 'away': game['teams']['away']['team']['id']}
            team_stats = {'home': getTeamGameStats(str(teams['home']), game_id), 'away': getTeamGameStats(str(teams['away']), game_id)}
            roster = {"home": getTeamRoster(game_id, 'home'), "away": getTeamRoster(game_id, 'away')}
            # print(roster['home']['ID8478508'])
            # game_players = {"home": {}, "away": {}}
            game_players = getGameAllPlayersStats(game_id)
            for team in ["home", "away"]:
                for player in roster[team]:
                    position = roster[team][player]['position']['abbreviation']
                    if position != 'G' and position != 'N/A':
                        if player[0]+player[1] != 'ID':
                            player = 'ID' + player
                        if player not in playerGameStatsTotal.keys():
                            playerGameStatsTotal[player] = {}
                            previousSeason = str(int(season[:4])-1) + str(int(season[4:])-1)
                            prev_season = getPlayerSeasonStats(player[2:], previousSeason)
                            if not prev_season['stats'][0]['splits']:
                                playerPrevSeasonStatsTotal[player] = {}
                            else:
                                prev_stats = prev_season['stats'][0]['splits'][0]['stat']
                                # print(prev_stats)
                                prev_stats['timeOnIce'] = int(prev_stats['timeOnIce'].split(":")[0])*60 + int(prev_stats['timeOnIce'].split(":")[1])
                                prev_stats['powerPlayTimeOnIce'] = int(prev_stats['powerPlayTimeOnIce'].split(":")[0])*60 + int(prev_stats['powerPlayTimeOnIce'].split(":")[1])
                                prev_stats['shortHandedTimeOnIce'] = int(prev_stats['shortHandedTimeOnIce'].split(":")[0])*60 + int(prev_stats['shortHandedTimeOnIce'].split(":")[1])
                                prev_stats['evenTimeOnIce'] = int(prev_stats['evenTimeOnIce'].split(":")[0])*60 + int(prev_stats['evenTimeOnIce'].split(":")[1])
                                
                                player_stats = prev_stats
                                playerPrevSeasonStatsTotal[player] = {'Prev_Season_GP': player_stats['games'], 'Prev_Season_Goals': player_stats['goals'], 'Prev_Season_Assists': player_stats['assists'], 'Prev_Season_Shots': player_stats['shots'], 'Prev_Season_PIM': player_stats['penaltyMinutes'], 'Prev_Season_PPG': player_stats['powerPlayGoals'], 'Prev_Season_PPA': player_stats['powerPlayPoints']-player_stats['powerPlayGoals'], 'Prev_Season_PP TOI': player_stats['powerPlayTimeOnIce'], 'Prev_Season_EV TOI': player_stats['evenTimeOnIce']}
                        if teams[team] not in teamGameStatsTotal.keys():
                            teamGameStatsTotal[teams[team]] = {}
                        team_total_stats = {'Team_' + key: value for key, value in teamGameStatsTotal[teams[team]].items()}
                        opponent_total_stats = {'Opponent_' + key: value for key, value in teamGameStatsTotal[teams[team]].items()}
                        data.append({**game_players[team][player], **playerGameStatsTotal[player], **playerPrevSeasonStatsTotal[player], **team_total_stats, **opponent_total_stats})
            for team in ["home", "away"]:
                for player in roster[team]:
                    position = roster[team][player]['position']['abbreviation']
                    if position != 'G' and position != 'N/A':
                        if player[0]+player[1] != 'ID':
                            player = 'ID' + player
                        game_players[team][player] = {key: value for key, value in game_players[team][player].items() if key not in ['Date', 'game_id', 'Scored']}
                        if 'Total_GP' not in playerGameStatsTotal[player].keys():
                            playerGameStatsTotal[player]['Total_GP'] = 1
                        else:
                            playerGameStatsTotal[player]['Total_GP'] += 1
                        for key, value in game_players[team][player].items():
                            if key in playerGameStatsTotal[player]:
                                playerGameStatsTotal[player]['Total_'+key] += value
                            else:
                                playerGameStatsTotal[player]['Total_'+key] = value
                if not teamGameStatsTotal[teams[team]]:
                    teamGameStatsTotal[teams[team]] = team_stats[team]
                    teamGameStatsTotal[teams[team]]['Team_GP'] = 1
                else:
                    teamGameStatsTotal[teams[team]]['Team_GP'] += 1
                    for key, value in team_stats[team].items():
                        if key in teamGameStatsTotal[teams[team]]:
                            teamGameStatsTotal[teams[team]][key] += value
                        else:
                            teamGameStatsTotal[teams[team]][key] = value
    data = pd.DataFrame(data)
    return data

#Time the code run
import timeit
start = timeit.default_timer()
# "8478402" - McDavid, "8479328" - Makar
player = "8479328"
players = ["8479328", "8478402"]
season = "20222023"
seasons = ["20172018", "20182019", "20192020", "20202021", "20212022"]#, "20222023"]
# dataset = createPlayerDataset(player, season)
# # Save dataset to csv file
# dataset.to_csv("Datasets/" + player + "_" + season + ".csv", index=False)

dataset = createSeasonDatabase(season, "P")
# Save dataset to csv file
dataset.to_csv("Datasets/" + season + "_P.csv", index=False)

dataset = createSeasonDatabase(season)
# Save dataset to csv file
dataset.to_csv("Datasets/" + season + ".csv", index=False)

# lastTime = timeit.default_timer()
# for player in players:
#     print(player)
#     for season in seasons:
#         print(season)
#         dataset = createPlayerDataset(player, season)
#         dataset.to_csv("Datasets/" + player + "_" + season + ".csv", index=False)
#         print(season + " time taken: ", timeit.default_timer() - lastTime)
#         lastTime = timeit.default_timer()

# print("Total Time taken: ", timeit.default_timer() - start)

# lastTime = timeit.default_timer()
# for season in seasons:
#     print(season)
#     dataset = createSeasonDatabase(season)
#     dataset.to_csv("Datasets/" + season + ".csv", index=False)
#     print(season + " time taken: ", timeit.default_timer() - lastTime)
#     lastTime = timeit.default_timer()

# print("Total Time taken: ", timeit.default_timer() - start)

categories = ['Prev_Season', 'Total', 'Team', 'Opponent']

# Loop through columns and average each value for each category by the GP of the category
for column in dataset.columns:
    cat = column.split('_')[0]
    if cat == 'Prev':
        cat = column.split('_')[0] + '_' + column.split('_')[1]
    if cat in categories and column != cat + '_GP':
        dataset[column] = dataset[column]/dataset[cat + '_GP']

for cat in categories:
    dataset = dataset.drop([cat + '_GP'], axis=1)