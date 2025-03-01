import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from io import StringIO
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, TextBox
from unidecode import unidecode

### DEAFULT SETTINGS
name = 'Victor Wembanyama'
minutes = 30
last_games = 10
line = [20.5, 20.5, 5.5, 12.5]
stat = ['PTS', 'FGA', 'AST', 'TRB'] 

### CREATING LINK TO THE PLAYER'S GAMELOG SITE
def player_gen(player): 
    player = player.lower()
    first_name = player[:2]
    last_name = re.sub("(^\\w+)", '', player) #getting the player's surname
    try:
        last_name = last_name[1:6]
    except IndexError:
        last_name = last_name
    return (first_name, last_name)

link_name = player_gen(name)

### GETTING THE TABLE OF PLAYER'S GAMELOG
def getting_table(link_name, player):
    i = 1
    while i > 0:
        url = f'https://www.basketball-reference.com/players/{link_name[1][0]}/{link_name[1]}{link_name[0]}0{i}/gamelog/2025'
        print(url)
        print(name)
        data = requests.get(url)
        soup = BeautifulSoup(data.text, features='lxml')

        link = soup.find_all('a', href = True)
        link = [l.text for l in link if 'Overview' in l.text]
        player_name = ' '.join(link[0].split(' ')[:-1])
        if unidecode(player_name.lower()) != player.lower(): #making sure we get the right player
            i += 1
            continue

        table = soup.find('table', id = 'pgl_basic')
        df = pd.read_html(StringIO(str(table)))[0]
        i = 0
    return df

table = getting_table(link_name, name)

### CLEANING THE DATAFRAME
def cleaning(df):
    df = df.rename(columns={'Unnamed: 5': 'Where', 'Unnamed: 7': 'Result'})
    to_drop = [i for i, n in enumerate(list(df['G'])) if (n == 'G') | pd.isna(n)] # dropping the repeating column names rows and rows with 'Inactive', 'Did Not Play' etc.
    df = df.drop(index = to_drop)
    df['MP'] = list(game_time.split(':')[0] for game_time in df['MP'])
    df.iloc[:, 8:-1] = df.iloc[:, 8:-1].astype('float')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Age'] = list(age.split('-')[0] for age in df['Age']) #simplifing player's age
    df['PTS + TRB'] = df['PTS'] + df['TRB']
    df['AST + TRB'] = df['AST'] + df['TRB']
    df['PTS + AST'] = df['PTS'] + df['AST']
    df['PTS + AST + TRB'] = df['PTS'] + df['AST'] + df['TRB']
    df['STL + BLK'] = df['STL'] + df['BLK']
    return df

df = cleaning(table)

### CREATING A PLOT
def plot(used_df, last_games, line, stat, player, minutes):

    global fig, text_box_min, text_box_player, text_box_games, buttons1, buttons2, buttons3, buttons4, text_box_line1, text_box_line2, text_box_line3, text_box_line4
    plt.close()

    used_df = used_df[used_df['MP'] >= int(minutes)]

    fig, ax = plt.subplots(2, 2, figsize = (10,3))

    n = 0
    for i in range(0, 2):
        for j in range(0, 2):
            values = used_df[f'{stat[n]}'].iloc[-last_games:]
            colors = ['red' if used_df[f'{stat[n]}'].iloc[-min(last_games, len(used_df))+z] <= line[n] else 'green' for z in range(0, min(last_games, len(used_df)))]
            ax[i,j].bar(x = used_df['Rk'].iloc[-last_games:], height = values, color = colors)
            ax[i, j].set_xticks(range(min(last_games, len(used_df))))
            ax[i,j].set_xticklabels(used_df['Opp'].iloc[-last_games:])
            ax[i,j].set_ylim(0, max(values)+5)
            ax[i,j].axhline(y = line[n], color = 'black', alpha = 0.5)
            ax[i,j].bar_label(ax[i,j].containers[0])
            ax[i,j].set_ylabel(stat[n])
            n += 1

    plt.suptitle(f'{player} last {len(used_df['Rk'].iloc[-last_games:])} games with {minutes}+ minutes')

    box_min = plt.axes([0.05, 0.03, 0.1, 0.03])  
    text_box_min = TextBox(box_min, "Minutes: ", initial = minutes)
    text_box_min.on_submit(submit_min)

    box_player = plt.axes([0.3, 0.03, 0.35, 0.03])  
    text_box_player = TextBox(box_player, "Player: ", initial = name)
    text_box_player.on_submit(submit_player)

    box_games = plt.axes([0.8, 0.03, 0.1, 0.03])  
    text_box_games = TextBox(box_games, "Last games: ", initial= last_games)
    text_box_games.on_submit(submit_games)

    labels1 = ['PTS', 'FG', '3P', 'FT']
    buttons1 = RadioButtons(ax=fig.add_axes([0, 0.6, 0.09, 0.2]), labels=labels1, active=labels1.index(stat[0]))
    buttons1.on_clicked(clicked_buttons1)

    labels2 = ['FGA', '3PA', 'FTA', 'PTS + AST + TRB']
    buttons2 = RadioButtons(ax=fig.add_axes([0.91, 0.6, 0.09, 0.2]), labels=labels2, active=labels2.index(stat[1]))
    buttons2.on_clicked(clicked_buttons2)

    labels3 = ['AST', 'STL', 'BLK', 'PTS + AST', 'STL + BLK']
    buttons3 = RadioButtons(ax=fig.add_axes([0, 0.2, 0.09, 0.2]), labels=labels3, active=labels3.index(stat[2]))
    buttons3.on_clicked(clicked_buttons3)

    labels4 = ['TRB', 'TOV', 'PF', 'PTS + TRB', 'AST + TRB']
    buttons4 = RadioButtons(ax=fig.add_axes([0.91, 0.2, 0.09, 0.2]), labels=labels4, active=labels4.index(stat[3]))
    buttons4.on_clicked(clicked_buttons4)

    box_line1 = plt.axes([0, 0.8, 0.09, 0.03])  
    text_box_line1 = TextBox(box_line1, "", initial = line[0])
    text_box_line1.on_submit(submit_line1)

    box_line2 = plt.axes([0.91, 0.8, 0.09, 0.03])  
    text_box_line2 = TextBox(box_line2, "", initial = line[1])
    text_box_line2.on_submit(submit_line2)

    box_line3 = plt.axes([0, 0.4, 0.09, 0.03])  
    text_box_line3 = TextBox(box_line3, "", initial = line[2])
    text_box_line3.on_submit(submit_line3)

    box_line4 = plt.axes([0.91, 0.4, 0.09, 0.03])  
    text_box_line4 = TextBox(box_line4, "", initial = line[3])
    text_box_line4.on_submit(submit_line4)


    manager = plt.get_current_fig_manager()
    manager.window.state('zoomed')

    plt.show()

### MAKING ALL BUTTONS AND BOXES WORK
def new_dataframe():
    new_link_name = player_gen(name)
    new_table = getting_table(new_link_name, name)
    new_df = cleaning(new_table)
    return new_df

def submit_min(num):
    global minutes
    minutes = num
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, name, minutes)

def submit_player(play):
    global name
    name = play
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, play, minutes)

def submit_games(games):
    global last_games
    new_df = new_dataframe()
    last_games = int(games)
    plot(new_df, last_games, line, stat, name, minutes)

def clicked_buttons1(opt):
    global stat
    stat[0] = opt
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, name, minutes)

def clicked_buttons2(opt):
    global stat
    stat[1] = opt
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, name, minutes)

def clicked_buttons3(opt):
    global stat
    stat[2] = opt
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, name, minutes)

def clicked_buttons4(opt):
    global stat
    stat[3] = opt
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, name, minutes)

def submit_line1(num):
    global line
    line[0] = float(num)
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, name, minutes)

def submit_line2(num):
    global line
    line[1] = float(num)
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, name, minutes)

def submit_line3(num):
    global line
    line[2] = float(num)
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, name, minutes)

def submit_line4(num):
    global line
    line[3] = float(num)
    new_df = new_dataframe()
    plot(new_df, last_games, line, stat, name, minutes)

plot(df, last_games, line, stat, name, minutes)
