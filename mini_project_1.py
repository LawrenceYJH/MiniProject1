import sqlite3
import sys
import datetime
# to make input password invisble
import getpass
connection = None
cursor = None
# when user start session, s_num will be implement,base on the largest sno of user + 1
# when user logout without ending session, s_num temporary store in a list
# if user choose to exist program, will be handled in main function
s_num = None
uid_list = [] #store uid if user logout without ending session and not ending the program
sno_list = [] #store sno if user logout withoug ending session and program

def connect():
    '''
    Function that connect python to sql database
    It allows passing value as command line argument
    Parameters: None
    Returns: None
    '''
    global connection, cursor
    # to pass filename as commend argument
    path = sys.argv[1]
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute(' PRAGMA forteign_keys=ON; ')
    connection.commit()
    return

def main_screen():
    '''
    Function that prompt user to choose to login, register, or exit
    It also end all session when exit
    Parameters: None
    Returns: None
    '''    
    global connection, cursor,uid_list,sno_list
    run = True
    while run:
        # keep run untill user choose to leave
        choice = input("\nPlease choose the following:\n1.Login\n2.Register\n3.Exit\n")
        if choice == '1':
            login()
        elif choice == '2':
            register()
        elif choice == '3':
            #when user choose to exist the program, end all stored session number with
            #corresponding uid in uid_list
            if sno_list != []:
                now = datetime.datetime.now()
                current = now.strftime('%Y-%m-%d %H:%M:%S')                  
                for i in range(len(sno_list)): 
                    u = uid_list[i]
                    s = sno_list[i]
                    cursor.execute('''update sessions set end = ? where uid = ? AND sno = ?''',\
                                   (current,u,s),)
                    connection.commit()
                    print('You sucessfully close session for user ' + u + '.' )                    

            run = False
        else:
            print('Invalid option, please try again.\n')
def login():
    '''
    prompt user to input id and password, check if there are any matching results
    If result match, allow user to login as user or artist based on the result
    Parameters: None
    Returns: None
    '''    
    global connection, cursor
    run = True
    while run:
        input_id = input('\nPlease enter a valid id\n')
        # since id is case-insensitive, make all input lowercase
        input_id = input_id.lower()
        # make password invisble
        pwd = getpass.getpass('Please enter your password\n')
        cursor.execute('''SELECT * FROM artists  
                          WHERE lower(aid) = ? 
                          AND pwd = ?''',(input_id,pwd),)
        artist = cursor.fetchall()
        cursor.execute('''SELECT * FROM users 
                          WHERE lower(uid) = ? 
                          AND pwd = ?''',(input_id,pwd),)
        user = cursor.fetchall()
        # if there is no matching user/artist in database
        if artist == [] and user == []:
            print('Invalid id or password, please try again.\n')
        elif artist != []:
            # if same uid and aid exist in two tables
            if user != []:
                print('\nPlease choose to login as user or artist.')
                choice = input('1.Login as user\n2.Login as artist\n')
                if choice == '1':      
                    user_login(input_id)
                elif choice == '2':
                    artist_login(input_id)
                else:
                    print('Invalid options, please try again.\n')
            else:
                artist_login(input_id)
        elif user != []:
            user_login(input_id)
        connection.commit()
        run = False
    return

def user_login(uid):
    '''
    Function that allow user choose to start end session/search for songs or playlist or artist
    Parameters: uid: from user id
    Returns: None
    '''    
    global s_num, uid_list, sno_list
    # if user logout without closing the program, find sno when same user login again
    if uid in uid_list:
        index = uid_list.index(uid)
        s_num = sno_list[index]
        # once a user's sno and uid are found, remove them from the list
        uid_list.remove(uid)
        sno_list.remove(s_num)    
    # keep guding user to input untill they choose to log out
    while True:
        option = input('\nPlease choose the following option.\
        \n1.Start a session\n2.Search for songs and playlists\
        \n3.Search for artist\n4.End session\n5.Log out\n')
        if option == '1':
            start_session(uid)
        elif option == '2':
            search_SandP(uid)
        elif option == '3':
            search_artist(uid)
        elif option == '4':
            end_session(uid)
        elif option == '5': 
            if s_num != None:
                uid_list.append(uid)
                sno_list.append(s_num)
                s_num = None
            return
        else:
            print('Invalid option\n')
    return

def artist_login(aid):
    '''
    Function that allow artist to choose to add song, find_top
    Parameters: aid: artist id
    Returns: None
    '''    
    while True:
        option = input('\nPlease choose the following option\
        \n1.Add a song\n2.Find top fans and playlists\n3.Log out\n')
        if option == '1':
            add_song(aid)
        elif option == '2':
            find_top(aid)
        elif option == '3':
            return
        else:
            print('Invalid option.')

def start_session(uid):
    '''
    Function that allow user to start a session if there is no running session
    Parameters: uid: user id
    Returns: None
    '''    
    global connection, cursor, s_num
    # if there is existing sno, return
    if s_num != None:
        print('A section has already started, please close it before you start ohter one.')
        return
    cursor.execute('''select max(sno),uid from sessions where uid = ?;''',(uid,),)
    value = cursor.fetchall()
    # if user does not have any sno before
    if value[0][0] == None:
        s_num = 1
    else:
        # if user have sno, find the largest sno, add one as new sno
        s_num = int(value[0][0]) + 1
    now = datetime.datetime.now()
    current = now.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''INSERT INTO SESSIONS VALUES (:uid, :sno, :start, :end); ''',\
                   {'uid':uid, 'sno':s_num, 'start':current, 'end': None})
    connection.commit()

    print('You have started a new session.')
    return        

def search_SandP(uid):
    '''
    Function that allow user to search for songs or playlist base on the keywords
    User can also choose songs to perform songs action or playlist action
    Parameters: uid: user id
    Returns: None
    '''    
    global connection, cursor
    # to store input keyword
    key_list = []
    # to store matching output with order
    results = []
    while key_list == []:
        keyword = input("Please enter what you are looking for: ").lower()
        key_list = keyword.split()
    # make each keyword "%x% format"
    for i in range(0,len(key_list)):
        key_list[i] = '%' + key_list[i] + '%'
    keywords = tuple(key_list)    
    #------------for songs    
    s_query = ""
    # find all matching songs, sorted
    for i in range(len(key_list) - 1):
        s_query += "UNION ALL SELECT sid,title,duration FROM songs WHERE title LIKE ? "
    s_query = "SELECT sid,title,duration FROM songs WHERE title LIKE ? " + s_query
    s_query = "select s.sid, s.title, s.duration, 'songs' from \
    (" + s_query + ")s group by s.sid, s.title, s.duration order by count(*) desc"
    cursor.execute(s_query,keywords)    
    s_value = cursor.fetchall()
    #-----------for playlist
    p_query = ""
    #find all matching playlists, sorted
    for i in range(len(key_list) - 1):
        p_query += "UNION ALL select  p.pid,  p.title, sum(s.duration) as total\
                      from playlists p, plinclude pl, songs s\
                      where p.pid = pl.pid and pl.sid = s.sid\
                      and p.title like ?\
                      group by p.pid, p.title " 
    p_query = "select  p.pid,  p.title, sum(s.duration) as total\
                      from playlists p, plinclude pl, songs s\
                      where p.pid = pl.pid and pl.sid = s.sid\
                      and p.title like ? \
                      group by p.pid, p.title " + p_query
    p_query = "select p.pid, p.title, p.total,  'playlist' from ( " + p_query + \
        ")p group by p.pid, p.title, p.total order by count(*) desc"     
    cursor.execute(p_query,keywords)       
    p_value = cursor.fetchall()    

    # if no matching keyword
    if s_value == [] and p_value == []:
        print("Not such results.")
        return
    while s_value!= [] and p_value != []:
        # p_last and s_last represent the matching number
        p_last = p_value[-1][-2]
        s_last = s_value[-1][-2]
        # since s_value and p_value sorted in DESC, the last element is the smallest
        # hence smaller matching element will be append first
        # eventually have increasing order list
        if p_last <= s_last:
            item = p_value.pop()
            results.append(item)
        else:
            item = s_value.pop()
            results.append(item)
        # if one list done appending, the other list should be append without comparing   
    if s_value == []:
        for i in range(len(p_value)):
            last = p_value.pop()
            results.append(last)
    if p_value == []:
        for i in range(len(s_value)):
            last = s_value.pop()
            results.append(last)
    print('---')
    # an index to check pages
    index = 0
    # set True when user chose to leave
    select = False
    # reverse increasing order to desc
    results.reverse()
    length = len(results)
    while not select:
        temp = results[index:index+5]
        i = 1
        print('')
        for each in temp:
            print(str(i) + ':' + '| Id: ' + str(each[0]) + ' | Title: ' + str(each[1]) + \
                  ' | Duration: ' + str(each[2]) + ' | Type: ' + str(each[3]))
            i = i + 1
        if index+5 < length:
            next_page = True
            print('\nSelect 0 to the next page or')
        else:
            next_page = False
        option = input('\nChoose the following options or press x to exist: ')
        if next_page:
            if option == '0':
                index = index +5            

        if option == '1':
            print('select: ' +  " " +str(results[index][1]))
            pass_value = results[index][0]
            pass_type = results[index][-1]
            title = results[index][1]
            if pass_type == 'songs':
                song_select(uid,pass_value,title)
            elif pass_type == 'playlist':
                playlist_select(uid,pass_value,title)
            else:
                print('No such exist.')
        elif option == '2' and (index + 1)<length:
            print('select: ' +  ' ' +str(results[index+1][1]))
            pass_value = results[index+1][0]
            pass_type = results[index+1][-1]    
            title = results[index+1][1]
            if pass_type == 'songs':
                song_select(uid,pass_value,title)
            elif pass_type == 'playlist':
                playlist_select(uid,pass_value,title)
            else:
                print('No such exist.')
        elif option == '3' and (index + 2)<length:
            print('select: ' +  ' ' + str(results[index+2][1]))
            pass_value = results[index+2][0]
            pass_type = results[index+2][-1]
            title = results[index+2][1]
            if pass_type == 'songs':
                song_select(uid,pass_value,title)
            elif pass_type == 'playlist':
                playlist_select(uid,pass_value,title)
            else:
                print('No such exist.')
        elif option == '4' and (index + 3)<length:
            print('select: ' +  ' ' + str(results[index+3][1]))
            pass_value = results[index+3][0]
            pass_type = results[index+3][-1]
            title = results[index+3][1]
            if pass_type == 'songs':
                song_select(uid,pass_value,title)
            elif pass_type == 'playlist':
                playlist_select(uid,pass_value,title)
            else:
                print('No such exist.')
        elif option == '5' and (index + 4)<length:
            print('select: ' +  ' ' + str(results[index+4][1]))
            pass_value = results[index+4][0]
            pass_type = results[index+4][-1]
            title = results[index+4][1]
            if pass_type == 'songs':
                song_select(uid,pass_value,title)
            elif pass_type == 'playlist':
                playlist_select(uid,pass_value,title)
            else:
                print('No such exist.')           
        elif option == 'x':
            select = True
        else:
            if option != '0':
                print('Invalid input, please try again.\n')
            if not next_page:
                print('Invalid input, please try again.\n')

    connection.commit()
    return    


def search_artist(uid):
    '''
    Function that allow user to search for artist base on keywords
    User can also select artist to display all songs owned by artist and perform song actions
    Parameters: uid: from user id
    Returns: None
    '''    
    global connection, cursor
    # to store input keyword
    key_list = []
    keywords = []

    # keep prompting user to input 
    while key_list == []:
        keyword = input("Please enter what you are looking for: ").lower()
        key_list = keyword.split()
    # make each keyword "%x% format"
    length = len(key_list)
    for i in range(0,len(key_list)):
        key = '%' + key_list[i] + '%'
        keywords.append(key)
        keywords.append(key)      
    keywords = tuple(keywords) 
    query = ""
    for i in range(length-1):
        query += "UNION all select a.nationality, a.name,a.aid \
    from songs s, artists a , perform p \
    where s.sid = p.sid AND a.aid = p.aid and (a.name like ? or s.title like ? ) "
    query = "select a.nationality, a.name, a.aid \
        from songs s, artists a , perform p \
        where s.sid = p.sid AND a.aid = p.aid and (a.name like ? or s.title like ?) " + query  
    query = 'select  t.aid, t.name, t.nationality,  count(*)as num from ( ' + query + \
        ' )t group by t.aid, t.nationality, t.name order by count(*) desc '
    query = 'select s_table.name, s_table.nationality, count(*), s_table.aid \
    from  perform p, songs s, ( ' + query + ' )s_table \
    where s_table.aid = p.aid and s.sid = p.sid \
    group by s_table.name, s_table.nationality, s_table.aid order by num desc'
    #query = 'select s.name, s.nationality'
    cursor.execute(query,keywords)
    results = cursor.fetchall()
    index = 0
    length = len(results)
    select = False
    while not select:
        temp = results[index:index+5]
        i = 1
        print('')
        for each in temp:
            print(str(i) + ':' + 'Name: ' + each[0] + ' | Nationality: ' \
                  + each[1].upper() + ' | Number of songs: ' + str(each[2]))
            i = i + 1
        if index+5 < length:
            next_page = True
            print('\nSelect 0 to the next page or')
        else:
            next_page = False
        option = input('\nChoose the following options or press x to exist: ')
        if next_page:
            if option == '0':
                index = index +5
        if option == '1':
            print('select: ' +  " " +str(results[index][0]))
            choosen = results[index][-1]
            display_song(uid,choosen)
        elif option == '2' and (index + 1)<length:
            print('select: ' +  ' ' +str(results[index+1][0]))
            choosen = results[index+1][-1]
            display_song(uid,choosen)
        elif option == '3' and (index + 2)<length:
            print('select: ' +  ' ' + str(results[index+2][0]))
            choosen = results[index+2][-1]
            display_song(uid,choosen)
        elif option == '4' and (index + 3)<length:
            print('select: ' +  ' ' + str(results[index+3][0]))
            choosen = results[index+3][-1]
            display_song(uid,choosen)
        elif option == '5' and (index + 4)<length:
            print('select: ' +  ' ' + str(results[index+4][0]))
            choosen = results[index+4][-1]
            display_song(uid,choosen)
        elif option == 'x':
            select = True
        else:
            if option != '0':
                print('Invalid input, please try again.\n')
            if not next_page:
                print('Invalid input, please try again.\n')

    connection.commit()    
    return   

def display_song(uid,aid):
    '''
    Function that display songs in proper format, at most 5 songs per paeg
    Parameters: uid: from users id, aid: from artist id
    Returns: None
    '''    
    global connection,cursor
    cursor.execute('select s.sid, s.title, s.duration from songs s, perform p\
    where p.aid = ? and p.sid = s.sid',(aid,),)
    results = cursor.fetchall()
    index = 0
    length = len(results)
    select = False
    while not select:
        temp = results[index:index+5]
        i = 1
        print('')
        for each in temp:
            print(str(i) + ':' + '| Id: ' + str(each[0]) + ' | Title: ' + str(each[1]) + \
                  ' | Duration: ' + str(each[2]) )
            i = i + 1
        if index+5 < length:
            next_page = True
            print('\nSelect 0 to the next page or')
        else:
            next_page = False
        option = input('\nChoose the following options or press x to exist: ')
        if next_page:
            if option == '0':
                index = index +5
        if option == '1':
            print('select: ' +  " " +str(results[index][1]))
            pass_value = results[index][0]
            title = results[index][1]
            song_select(uid,pass_value,title)

        elif option == '2' and (index + 1)<length:
            print('select: ' +  ' ' +str(results[index+1][1]))
            pass_value = results[index+1][0]
            title = results[index+1][1]
            song_select(uid,pass_value,title)

        elif option == '3' and (index + 2)<length:
            print('select: ' +  ' ' + str(results[index+2][1]))
            pass_value = results[index+2][0]
            title = results[index+2][1]
            song_select(uid,pass_value,title)

        elif option == '4' and (index + 3)<length:
            print('select: ' +  ' ' + str(results[index+3][1]))
            pass_value = results[index+3][0]
            title = results[index+3][1]
            song_select(uid,pass_value,title)

        elif option == '5' and (index + 4)<length:
            print('select: ' +  ' ' + str(results[index+4][1]))
            pass_value = results[index+4][0]
            title = results[index+4][1]
            song_select(uid,pass_value,title)          
        elif option == 'x':
            select = True
        else:
            if option != '0':
                print('Invalid input, please try again.\n')
            if not next_page:
                print('Invalid input, please try again.\n')    
    connection.commit()
    return

def end_session(uid):
    '''
    Function that allow user to end running session
    If no running session, reject action
    Parameters: uid from user id
    Returns: None
    '''    
    global connection, cursor, s_num
    # if there is no existing session running, stop user from doing it
    if s_num == None:
        print('There is no existing session.')
        return
    now = datetime.datetime.now()
    current = now.strftime('%Y-%m-%d %H:%M:%S')    
    cursor.execute('''update sessions set end = ? where uid = ? AND sno = ?''',\
                   (current,uid,s_num),)
    print('You successfully close session. ' )
    s_num = None
    connection.commit()
    return

def add_song(aid):
    '''
    Function that allow artist to add song that belong to them
    It also check whehter songs with same duration and title in the database already
    Parameters: aid: from artist id
    Returns: None
    '''    
    global connection, cursor
    select = False
    while not select:
        title = input('Please enter the title of your song: ').lower()
        duration = input('Please enter the duration of your song: ')
        try:
            duration = int(duration)
            select = True
        except:
            print('Invalid input')
    cursor.execute('select * from songs s, perform p \
    where lower(s.title) = ? and s.duration = ? and p.aid = ? \
    and p.sid = s.sid',(title,duration,aid),)
    check = cursor.fetchall()
    if check != []:
        done = False
        while not done: 
            choice = input("A same song already exists, do you want to implement it as new song? \
            Choose 'Y' as 'Yes' and 'N' as 'No' ").lower()
            if choice == 'y':
                done = True
            elif choice == 'n':
                return
            else:
                print('Invalid input, please choose the correct option.')
    max_sid = cursor.execute('SELECT MAX(sid) FROM songs').fetchone()[0]
    new_sid = max_sid + 1
    # insert the new song into songs table
    add_song_query = "INSERT INTO songs VALUES (?, ?, ?)"
    t = (new_sid, title, duration)
    cursor.execute(add_song_query, t)
    # insert the new song into the artist's song list
    add_song_to_artists_query = "INSERT INTO perform VALUES (?, ?)"
    t = (aid, new_sid)  
    cursor.execute(add_song_to_artists_query, t)
    print(title + ' has been sucessfully added.')

    return 



def register():
    '''
    Function that allow people to register as new user
    After sucessfully registeation, will guid user to user_login 
    Parameters: None
    Returns: None
    '''    
    global connection, cursor
    exist = True
    while exist:
        # keep asking user to create a valid account
        uid = input('Please enter a id that you want to create:\n')
        cursor.execute('''SELECT * FROM users  
        WHERE uid = ? 
        ''',(uid,),)
        uid_list = cursor.fetchall()
        cursor.execute('''SELECT * FROM artists  
        WHERE aid = ? 
        ''',(uid,),)
        artist_list = cursor.fetchall()  
        # if id is available
        if uid_list == [] and artist_list == []:
            # uid must satisfied domain
            if len(uid)>= 1 and len(uid)<=4:
                exist = False
            else:
                print('Please enter a valid four character id.\n')
        else:
            print('ID already exist, please try another one.\n')
    name = input('This ID is available.\nPlease enter your name:\n')
    pwd = input('Please enter your password:\n')
    information = (uid,name,pwd)

    cursor.execute('''INSERT INTO users VALUES {}'''.format(information))
    print('Sucessfully created!')
    connection.commit()
    user_login(uid)
    return

def song_select(uid,sid,title):
    '''
    Prompt user input as user's action, user can choose if they want to listen the song
    or see more information about the song or add the song to playlist
    Parameters: uid, sid, title
    Returns: None
    '''     
    bad_inp = True
    while bad_inp:	
        bad_inp = False
        choice = input("1. listen this song\n2. see more informations\n3. add to playlist\n")
        print()
        if choice == "1":
            listen_query(uid, sid, title)
        elif choice == "2":
            get_more_info(sid)
            display_more_info(sid)
        elif choice == "3":
            add_to_pl_ui(sid, uid)
        else:
            print("invalid input")
            bad_inp = True
    return


def playlist_select(uid,pid,title):
    '''
    Function that shows all songs within the playlist
    Parameters: uid: user id, pid: playlist id, title: playlist title
    Returns: None
    '''    
    global connection, cursor, s_num
    cursor.execute('''select s.sid, s.title, s.duration \
    from plinclude p, songs s where s.sid = p.sid and p.pid = ? ''',(pid,),)
    results = cursor.fetchall()
    index = 0
    length = len(results)
    select = False
    while not select:
        temp = results[index:index+5]
        i = 1
        print('')
        for each in temp:
            print(str(i) + ':' + '| Id: ' + str(each[0]) + ' | Title: ' + str(each[1]) + \
                  ' | Duration: ' + str(each[2]) )
            i = i + 1
        if index+5 < length:
            next_page = True
            print('\nSelect 0 to the next page or')
        else:
            next_page = False
        option = input('\nChoose the following options or press x to exist: ')
        if next_page:
            if option == '0':
                index = index +5
        if option == '1':
            print('select: ' +  " " +str(results[index][1]))
            pass_value = results[index][0]
            title = results[index][1]
            song_select(uid,pass_value,title)

        elif option == '2' and (index + 1)<length:
            print('select: ' +  ' ' +str(results[index+1][1]))
            pass_value = results[index+1][0]
            title = results[index+1][1]
            song_select(uid,pass_value,title)

        elif option == '3' and (index + 2)<length:
            print('select: ' +  ' ' + str(results[index+2][1]))
            pass_value = results[index+2][0]
            title = results[index+2][1]
            song_select(uid,pass_value,title)

        elif option == '4' and (index + 3)<length:
            print('select: ' +  ' ' + str(results[index+3][1]))
            pass_value = results[index+3][0]
            title = results[index+3][1]
            song_select(uid,pass_value,title)

        elif option == '5' and (index + 4)<length:
            print('select: ' +  ' ' + str(results[index+4][1]))
            pass_value = results[index+4][0]
            title = results[index+4][1]
            song_select(uid,pass_value,title)          
        elif option == 'x':
            select = True
        else:
            if option != '0':
                print('Invalid input, please try again.\n')
            if not next_page:
                print('Invalid input, please try again.\n')

    connection.commit()
    return
#------------------------------------------------------------------------
def listen_query(uid, sid,title):	
    '''
    When a song is selected for listening, a listening event is recorded within the current session of the user (if a session 
    has already started for the user) or within a new session (if not). 
    a listening event is recorded by either inserting a row to table listen or increasing the listen count in this table by 1. 
    Parameters: uid, sid, title
    Returns: None
    '''    
    global connection, cursor, s_num 
    if s_num == None:
        start_session(uid)
    sno = s_num
    select_query = '''SELECT cnt FROM listen WHERE uid = ?
						AND sno	= ?
						AND sid	= ?'''


    update_query = '''UPDATE listen SET cnt = cnt+1 WHERE listen.uid = ?
						AND listen.sno = ?
						AND listen.sid = ?'''
    insert_query = "INSERT INTO listen VALUES (?, ?, ?, 1)"	# (uid, sno, sid,)
    # if the song was listened, select_query is not none.

    t = (uid, sno, sid)
    # run select query
    cursor.execute(select_query, t)
    result = cursor.fetchone()
    # if the result from fetchone() is empty, it will return None
    if result is None:
        # run insert_query, if user first time listen this song
        cursor.execute(insert_query, t)
    else:
        # run update_query, if user had listend before
        cur.execute(update_query, t)
    print('Now playing ' + title)
    connection.commit()
    return
#------------------------------------------------------------------
def get_more_info(sid):	
    '''
    Get more information about the song.
    More information for a song is the names of artists who performed it in addition to id, 
    title and duration of the song as well as the names of playlists the song is in (if any). 
    Parameters: sid
    Returns: (tuple(song_infomation), list(plylist_names))
    '''        
    global connection, cursor, s_num  
## song_info is a tuple of: (art_name, sid, title, duration)
## pl_names is a list of all playlist names which includes this song.
    # 两个query：
    song_info_query = '''SELECT a.name, s.sid, s.title, s.duration 
							FROM perform p, artists a, songs s 
							WHERE s.sid = ? 
								AND p.sid = s.sid
								AND p.aid = a.aid'''
    song_info  = cursor.execute(song_info_query, (sid,)).fetchone()

    pl_name_query = "SELECT title FROM playlists WHERE pid IN(SELECT pid FROM plinclude WHERE sid=?)"
    pl_names = [name for (name,) in cursor.execute(pl_name_query, (sid,)).fetchall()]
    return song_info, pl_names

# 用来展示数据，调用 get_more_info 的函数
def display_more_info(sid):	
    '''
    display the more informations about the song.
    Parameters: sid
    Returns: 0: success, -1: wrong sid
    '''     
    global connection, cursor, s_num 
    (song_info, pl_names) = get_more_info(sid)
    # song_info is a tuple of: (art_name, sid, title, duration)
    # pl_names is a list of all playlist names which includes this song.
    # if the sid is not in the database, then song_info will be None
    if song_info is None:
        print("song not in database!!")
        return -1
    # print song_info
    print("artist name: ", song_info[0])
    print("song id: ", song_info[1])
    print("song title: ", song_info[2])
    print("song duration: ", song_info[3])
    # print for playlist names which includes this song
    # do not print if there is no playlist
    if len(pl_names) != 0:
        print("this song is in the following playlists:")
        for title in pl_names:
            print(title)
    return 0
#-----------------------------------------------------------

# input uid, get a list of the playlists created by this user
def get_user_pl(uid):	# list of (pid, pl_name/title)
    '''
    Get the user's playlists.
    Parameters: uid
    Returns: list of (pid, pl_name/title)
    '''     
    global connection, cursor
    usr_pl_query = "SELECT pid, title FROM playlists WHERE uid=?"	# (uid,)
    pl_lists = cursor.execute(usr_pl_query, (uid,)).fetchall()
    return pl_lists

# add this song to playlist
# will prompt the user for which playlist to add
# user can also create a new playlist
def add_to_pl_ui(sid, uid):
    '''
    adding a song to a playlist, show what playlists the user has. The song can be added to an existing playlist owned by the user (if any) 
    or to a new playlist. When it is added to a new playlist, a new playlist would be created with a unique new id 
    and the uid set to the id of the user and a title will be obtained from input. 
    Parameters: sid, uid
    Returns: None
    '''     
    pl_lists = get_user_pl(uid)
    # [(pid, title)]
    op_num = 0
    print("you have following playlists")
    for row in pl_lists:	# row is pl_lists[i]
        print(op_num, row[1])
        op_num += 1
    print(op_num, "<create new playlist>")

    usr_in = input("Which play list you want to add to?")

    ### bad input handling ....
    ### condition: must be integer, 0<= number <= op_num
    bad_input = True
    while bad_input:
        try:
            usr_in = int(usr_in)
            if usr_in < 0 or usr_in > op_num:
                raise ValueError
            bad_input = False
        except ValueError:
            usr_in = input("Please enter a valid number")
    ### now usr_in is a good integer,
    ### and is a valid index of pl_lists

    if usr_in < op_num:		# user select an exisiting playlist
        pid = pl_lists[usr_in][0]	# pl_lists = [(pid, title)]
    if usr_in == op_num:	# create new pl
        pid = create_new_pl(uid)
    max_sorder = cursor.execute("SELECT MAX(sorder) FROM plinclude").fetchone()[0]
    new_sorder = max_sorder + 1    
    # add this sid into pid;
    success = add_to_pl(pid, sid, new_sorder)
    if success == 0:
        print("add song to playlist success")
    else:
        print("add song to playlist failed, unknown error")

    return

def add_to_pl(pid, sid, sorder):	
    '''
    Add the song into playlist
    Parameters: pid, sid, sorder
    Returns: 0: success, -1: fail
    '''     
    global connection, cursor
    try:
        t = (pid, sid, sorder)
        add_to_pl_query = "INSERT INTO plinclude VALUES (?, ?, ?)"
        cursor.execute(add_to_pl_query, t)
        connection.commit()
        return 0
    except:
        return -1	

def create_new_pl(uid):
    '''
    Taking uid of a user, create a new playlist for this user
    by looking into the database, find the largest pid, and add 1 to it to get the new pid
    Parameters: uid
    Returns: new_pid
    '''    
    global connection, cursor
    max_pid = cursor.execute('SELECT MAX(pid) FROM playlists').fetchone()[0]
    new_pid = max_pid + 1

    # get the title of the new playlist, do bad input handling
    pl_title = input("Please enter the title of the new playlist")
    bad_input = True
    while bad_input:
        if pl_title == '':
            pl_title = input("Please enter a valid title")
        else:
            bad_input = False
    add_new_pl_query = "INSERT INTO playlists VALUES (?, ?, ?)"
    t = (new_pid, pl_title, uid)
    cursor.execute(add_new_pl_query, t)
    connection.commit()

    return new_pid
#------------------------------------------------------------------------------------

def find_top(aid):
    '''
    Print top 3 fans and top 3 playlists.  
    Parameters: aid
    Returns: None

    '''    
    # get top 3 fans
    fans = top_fans(aid)	# fans = [(uid, total_listen_time)]
    # get top 3 playlists
    pl = top_pl(aid)		# pl = [(title, creater(user), total_songs)]
    # print
    print("Top 3 fans:")
    for i in range(len(fans)):
        print(fans[i][0], 'listened to your songs for', fans[i][1], 'seconds')
    print("Top 3 playlists:")
    for i in range(len(pl)):
        print(pl[i][0], 'is created by', pl[i][1], 'and has', pl[i][2], 'songs')

def top_fans(aid):
    '''
    Find top fans . 
    The artist would list top 3 users who 
    listen to their songs the longest time 
    If there are less than 3 such users, 
    fewer number of users can be returned. 
    Parameters: aid
    Returns: fans (list of tuples (uid, total_duration)

    '''        
    global connection, cursor
    top_fans_query = '''
					SELECT 
						uid, SUM(duration*cnt) AS total_duration 
					FROM listen NATURAL JOIN songs 
					WHERE sid IN 
						(SELECT sid FROM perform WHERE aid=?)
					GROUP BY uid ORDER BY total_duration DESC
                                        LIMIT 3
	'''
    t = (aid,)
    fans = cursor.execute(top_fans_query, t).fetchall()
    return fans	# list of tuples (uid, total_duration)


def top_pl(aid):# list of tuples (title, creater(user's name), total_songs)
    '''
    Find top playlists. 
    The artist would list top 3 playlists that include the largest number of their songs. 
    If there are less than 3 such playlists, 
    fewer number of playlists can be returned. 
    Parameters: aid
    Returns: pl -> (list of tuples (title, creater(user's name), total_songs))

    '''     
    global connection, cursor
    top_pl_query = '''
					SELECT
						pl.title, u.name, COUNT(s.sid) AS total_songs
					FROM playlists pl, users u, plinclude pi, songs s, perform p
					WHERE pl.pid = pi.pid AND pl.uid = u.uid AND pi.sid = s.sid AND p.sid = s.sid 
					AND p.aid = ?
					GROUP BY pl.title, u.name
					ORDER BY total_songs 
					DESC LIMIT 3					
	'''
    t = (aid,)
    pl = cursor.execute(top_pl_query, t).fetchall()
    return pl

#---------------------------------------------------------------------------
def main():
    global connection, cursor
    connect()
    main_screen()
    connection.commit()
    connection.close()

    return

if __name__ == "__main__":
    main()


#-----------------