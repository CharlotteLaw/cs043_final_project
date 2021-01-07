import wsgiref.simple_server
import urllib.parse
import http.cookies
from GameDatabase import GameDb
from GameService import GameService
from HtmlUtils import HtmlUtils

gameDb = GameDb()
htmlUtils = HtmlUtils()
gameService = GameService()

#This function is the main event loop for the web application.
#This function takes care of the game flow.
def application(environ, start_response):

    headers = [('Content-Type', 'text/html; charset=utf-8')]

    path = environ['PATH_INFO']
    params = urllib.parse.parse_qs(environ['QUERY_STRING'])
    un = params['username'][0] if 'username' in params else None
    pw = params['password'][0] if 'password' in params else None
    gameId = params['gameId'][0] if 'gameId' in params else 0
    move = params['move'][0] if 'move' in params else  0

    if path == '/register' and un and pw:
        result = gameDb.registerUser(un, pw)
        start_response('200 OK', headers)

        #I used ... and .. to work around some encoding issues relating to string concatenation.
        #... represents } and .. represents {
        if result == True:
            page = htmlUtils.getRegisterPage1().format(un)
            page = page.replace('...', '}')
            page = page.replace('..', '{')
            return [page.encode()]

        else:
            #return 'Sorry, username {} is taken'.format(un)
            page = htmlUtils.getRegisterFail().format(un)
            page = page.replace('...', '}')
            page = page.replace('..', '{')
            return [page.encode()]

    elif path == '/login' and un and pw:
        user = gameDb.login(un, pw)
        if user:
            win = user[0][2]
            lose = user[0][3]
            headers.append(('Set-Cookie', 'session={}:{}'.format(un, pw)))
            headers.append(('Set-Cookie', 'score={}:{}'.format(win, lose)))
            headers.append(('Set-Cookie', 'username={}'.format(un)))
            start_response('200 OK', headers)
            #return ['User {} successfully logged in. <a href="/account">Account</a>'.format(un).encode()]

            page = htmlUtils.getLoginPage1().format(un)

            page = page.replace('...', '}')
            page = page.replace('..', '{')

            return [page.encode()]

        else:
            start_response('200 OK', headers)
            page = htmlUtils.getLoginFail().format(un)

            page = page.replace('...', '}')
            page = page.replace('..', '{')

            return [page.encode()]

    elif path == '/logout':
        if 'HTTP_COOKIE' in environ:
            cookies = http.cookies.SimpleCookie()
            cookies.load(environ['HTTP_COOKIE'])
            [win, lose] = cookies['score'].value.split(':')
            un = cookies['username'].value
            gameDb.logout(un, win, lose)
        start_response('200 OK', headers)
        return ['''
        
        <style>
        div{
        width: 450px;
        height: 115px;
        text-align: center;
        margin-left:auto;
        margin-right:auto;
        font-size: 400%;
        }
        
        h1{
        text-align: center;
        margin-left:auto;
        margin-right:auto;
        font-size: 250%;
        }
        </style>
        
        <br>
        <br>


        <div class="highlight3" style="background: linear-gradient(to bottom, lightblue 0%, white 80%)">Tic Tac Toe!</div><br>
        
        
        
        <h1>Logged out. <a href="/">Login</a></h1>'''.encode()]

    elif path == '/account':
         start_response('200 OK', headers)

         if 'HTTP_COOKIE' not in environ:
             return ['Not logged in <a href="/">Login</a>'.encode()]

         cookies = http.cookies.SimpleCookie()
         cookies.load(environ['HTTP_COOKIE'])
         if 'session' not in cookies:
             return [htmlUtils.getNotLoginPage().encode()]

         [un, pw] = cookies['session'].value.split(':')

         if gameDb.isValidUser(un, pw):
             win = 0
             lose = 0

             #Win and lose is stored as a coookie but the game currently doesn't keep track of the win and lose score.
             #This is merely a placeholder for future advancements.
             if 'HTTP_COOKIE' in environ:
                 [win_cookie, lose_cookie] = cookies['score'].value.split(':')
                 win = int(win_cookie)
                 lose = int(lose_cookie)

             gameId = gameService.loadJoinableGames(gameDb, un)

             page = htmlUtils.getAccountPage(un, win, lose, gameId)
             return [page.encode()]
         else:
             return [htmlUtils.getNotLoginPage().encode()]

    elif path == '/game':
        if 'HTTP_COOKIE' not in environ :
            return ['Not logged in <a href="/">Login</a>'.encode()]

        cookies = http.cookies.SimpleCookie()
        cookies.load(environ['HTTP_COOKIE'])
        if 'session' not in cookies :
            return [htmlUtils.getNotLoginPage().encode()]

        [un, pw] = cookies['session'].value.split(':')


        [gameBoard, user_x, user_o, next_turn] = gameService.getLatestGameStatus(gameDb, gameId)

        if user_x == un:
            print("{}(X) - in game {}".format(un, gameId))
        elif user_o == un:
            print("{}(O) - in game {}".format(un, gameId))
        else:
            print("Second user {} joined game {}".format(un, gameId))
            gameService.addSecondUserToGame(gameDb, un, gameId)
            user_o = un
            gameService.deleteJoinedGame1(gameDb, gameId)

        if gameBoard.isBoardFull == True or gameBoard.isWinner('X') == True or gameBoard.isWinner('X') == True:
            gameService.deleteJoinedGame1(gameDb, gameId)

        # take care of move
        if move != 0 and (un == user_x and next_turn == 'X' or un == user_o and next_turn == 'O'):
            if (gameBoard.isSpaceFree(int(move))):
                # make move
                letter = 'X'
                nextTurn = 'O'
                if un == user_o:
                    letter = 'O'
                    nextTurn = 'X'
                gameBoard.makeMove(letter, int(move))
                gameService.saveGame(gameDb, gameId, gameBoard, nextTurn)
            else:
                print("move already made, just refreshing")

        win1 = gameBoard.isWinner('X')
        win2 = gameBoard.isWinner('O')
        start_response('200 OK', headers)
       # headers.append(('Set-Cookie', 'score={}:{}'.format(win1, win2)))
        page = htmlUtils.getGamePage(gameId, un, user_x, user_o, win1, win2, next_turn, gameBoard)
        return [page.encode()]

    elif path == '/':
         page = htmlUtils.getLoginPage()
             #.format(environ['QUERY_STRING'])
         start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
         return [page.encode()]

    elif path == '/create':
        start_response('200 OK', headers)
        gameId = gameService.createGame(gameDb, un)
        #page = htmlUtils.getGamePage(gameId, un, '?', False, False)
        #page = htmlUtils.getAccountPage(un, win, lose,gameId)
        page = htmlUtils.getCreatePage().format(un)
        page = page.replace('...', '}')
        page = page.replace('..', '{')
        return [page.encode()]

    else:
         start_response('404 Not Found', headers)
         return [htmlUtils.getNotFoundPage().encode()]


httpd = wsgiref.simple_server.make_server('', 8003, application)
httpd.serve_forever()