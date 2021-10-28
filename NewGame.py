import pygame
import random
import sys
#pyinstaller -F --add-data 'imgs\*;.'  .\main.py
class NewGame:
    def __init__(self):
        self.Running = True
        self.GameMode = "MainMenu"
        self.ScreenWidth = 1280
        self.ScreenHight = 720
        self.FPS = 0

        
        pygame.init()
        pygame.font.init()
        self.Clock = pygame.time.Clock()
        self.Screen = pygame.display.set_mode([self.ScreenWidth, self.ScreenHight])
        self.Modes = self.LoadModes()
        

    def LoadModes(self):
        modes = dict()
        modes["MainMenu"] = MainMenu(self.Screen, self.ScreenWidth)
        modes["EndScreen"] = EndScreen(self.Screen, self.ScreenWidth, 0)
        modes["GameScreen"] = GameScreen(self.Screen, self.ScreenWidth)
        
        return modes

    def StartMainLoop(self):
        while self.Running:
            self.FPS = self.Clock.get_fps()
            if self.GameMode == "MainMenu":
                self.Modes["MainMenu"].Draw()
                self.Modes["MainMenu"].Update(self.FPS)

            if self.GameMode == "EndScreen":
                self.Modes["EndScreen"].Draw()
                self.Modes["EndScreen"].Update(self.FPS)

            if self.GameMode == "GameScreen":
                self.Modes["GameScreen"].Draw()
                self.Modes["GameScreen"].Update(self.FPS)

            self.CheckIfScreenChange()
            print(f"FPS: {self.FPS}")
            self.Clock.tick()

    def CheckIfScreenChange(self):
        if self.Modes[self.GameMode].ScreenNeedsToChange:
            screenName = self.Modes[self.GameMode].ScreenToChangeToo
            self.GameMode = screenName

            if self.GameMode == "EndScreen":
                self.Modes["EndScreen"].UserScore = self.Modes["GameScreen"].UserScore
                self.Modes["GameScreen"] = GameScreen(self.Screen, self.ScreenWidth)
            
            # reset the screen change back to start
            self.Modes[self.GameMode].ScreenToChangeToo = ""
            self.Modes[self.GameMode].ScreenNeedsToChange = False

    def GetFonts(self):
        for f in pygame.font.get_fonts():
            print(f)



class MainMenu(object):
    def __init__(self, screen, sWidth):
        self.CurrentScreen = screen
        self.ScreenWidth = sWidth
        self.Background = None
        self.ScreenNeedsToChange = False
        self.ScreenToChangeToo = ""
        self.TextColor = 110, 68, 255
        self.Cloud1XY = (float(10),float(10))
        self.Cloud2XY = (float(380),float(130))
        self.Cloud3XY = (float(1000),float(80))
        self.CloudSpeed = float(0.230)
        self.Load()
        

    def Load(self):
        self.Background = pygame.image.load("imgs/background.png")
        self.cloud1 = pygame.image.load("imgs/cloud1.png")
        self.cloud2 = pygame.image.load("imgs/cloud2.png")
        self.cloud3 = pygame.image.load("imgs/cloud3.png")
        self.FontBig = pygame.font.Font("fonts/SanMarinoBeach.ttf",82)
        self.FontSmall = pygame.font.Font("fonts/SanMarinoBeach.ttf",38)
        self.GameNameWidth = (self.ScreenWidth / 2) - 240
    
    def ClearScreen(self):
        black = 0, 0, 0
        self.CurrentScreen.fill(black)

    def Draw(self):
        GameName = self.FontBig.render(f"Flowers", 1, self.TextColor)
        StartGame = self.FontSmall.render(f"Press space to start!", 1, self.TextColor)

        self.CurrentScreen.blit(self.Background, (0,0))
        self.CurrentScreen.blit(self.cloud1, self.Cloud1XY)
        self.CurrentScreen.blit(self.cloud2, self.Cloud2XY)
        self.CurrentScreen.blit(self.cloud3, self.Cloud3XY)

        self.CurrentScreen.blit(GameName, ((self.GameNameWidth + 40), 10))
        self.CurrentScreen.blit(StartGame, (self.GameNameWidth, 650))
        pygame.display.update()

    def UpdateClouds(self):
        a, b = self.Cloud1XY
        a = a + self.CloudSpeed 
        if a > 1380:
            a = float(-400)
        self.Cloud1XY = (a,b)

        a, b = self.Cloud2XY
        a = a + self.CloudSpeed + float(0.02)
        if a > 1380:
            a = float(-400)
        self.Cloud2XY = (a,b)

        a, b = self.Cloud3XY
        a = a + self.CloudSpeed - float(0.02)
        if a > 1380:
            a = float(-100)
        self.Cloud3XY = (a,b)

    def Update(self,fps):
        self.UpdateClouds()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    #print("Space")
                    self.ScreenNeedsToChange = True
                    self.ScreenToChangeToo = "GameScreen"


class EndScreen(object):
    def __init__(self, screen, sWidth, score):
        self.CurrentScreen = screen
        self.ScreenWidth = sWidth
        self.UserScore = score
        self.ScreenNeedsToChange = False
        self.ScreenToChangeToo = ""
        self.Background = None
        self.TextColor = 110, 68, 255
        self.Load()


    def Load(self):
        self.Background = pygame.image.load("imgs/background-main-menu.png")
        self.FontBig = pygame.font.Font("fonts/SanMarinoBeach.ttf",82)
        self.FontSmall = pygame.font.Font("fonts/SanMarinoBeach.ttf",38)
        self.GameNameWidth = (self.ScreenWidth / 2) - 240
    
    def ClearScreen(self):
        black = 0, 0, 0
        self.CurrentScreen.fill(black)

    def Draw(self):
        msg1 = self.FontBig.render(f"Your score was {self.UserScore}", 1, self.TextColor)
        msg2 = self.FontSmall.render("Press esc to quit game or press space to start again",1,self.TextColor)

        self.ClearScreen()
        self.CurrentScreen.blit(self.Background, (0,0))
        self.CurrentScreen.blit(msg1, (10,120))
        self.CurrentScreen.blit(msg2,(10,600))
        pygame.display.update()

    def Update(self, fps):
       for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    #print("Space")
                    self.ScreenNeedsToChange = True
                    self.ScreenToChangeToo = "MainMenu"


class GameScreen(object):
    def __init__(self, screen, sWidth, score=0):
        self.CurrentScreen = screen
        self.ScreenWidth = sWidth
        self.UserScore = score
        self.CurrentTime = 180
        self.ScreenNeedsToChange = False
        self.ScreenToChangeToo = ""
        self.Background = None
        self.TextColor = 110, 68, 255
        self.BoardRow = 11
        self.BoardCol = 17
        self.Board = None
        self.FlowersSeletced = list()
        self.AnimData = None # None mean not anim needed
        self.FlowerMatchSpeedAnim = float(0.5)
        self.Flower1OldPos = 0
        self.Flower2OldPos = 0
        self.MatchesFound = list()
        self.UserFirstMove = False
        self.FPS = 0
        self.Load()
        
    def Load(self):
        self.Background = pygame.image.load("imgs/background-main-menu.png")
        self.RFlower = pygame.image.load("imgs/flower-r.png")
        self.BFlower = pygame.image.load("imgs/flower-b.png")
        self.GFlower = pygame.image.load("imgs/flower-g.png")
        self.PFlower = pygame.image.load("imgs/flower-p.png")
        self.YFlower = pygame.image.load("imgs/flower-y.png")
        self.FontBig = pygame.font.Font("fonts/SanMarinoBeach.ttf",82)
        self.FontSmall = pygame.font.Font("fonts/SanMarinoBeach.ttf",28)
        self.GameNameWidth = (self.ScreenWidth / 2) - 240
        self.Board = self.BuildBoard()
        pygame.time.set_timer(pygame.USEREVENT, 1000)
    
    def ClearScreen(self):
        black = 0, 0, 0
        self.CurrentScreen.fill(black)

    def BuildBoard(self):
        # r = row, c = col
        Board = list()
        x = 150
        y = 0

        for _r in range(self.BoardRow):
            Board.append(list())

        for r in Board:
            y += 50
            x = 50
            for _c in range(self.BoardCol):
                x += 50
                r.append(self.CreateFlower(x, y))
        
        return Board

    def CreateFlower(self, x, y):
        num = random.randint(0,4)
        img = None
        sprite = None

        if num == 0:
            sprite = Flower("red", x, y)
            img = self.RFlower
        if num == 1:
            sprite = Flower("blue", x, y)
            img = self.BFlower
        if num == 2:
            sprite = Flower("purple", x, y)
            img = self.PFlower
        if num == 3:
            sprite = Flower("yellow", x, y)
            img = self.YFlower
        if num == 4:
            sprite = Flower("green", x, y)
            img = self.GFlower

        sprite.SetSurf(img)
        return sprite

    def CheckMove(self):
        self.UserFirstMove = True
        RowOneNumber, ColOneNumber = self.FlowersSeletced[0]
        RowTwoNumber, ColTwoNumber = self.FlowersSeletced[1]

        # make sure the flower clicked are on same row or col
        if RowOneNumber == RowTwoNumber or ColOneNumber == ColTwoNumber:
            #print("Flower is on the same row or col ")
            if RowOneNumber == (RowTwoNumber + 1) or RowTwoNumber == (RowOneNumber + 1):
                #print("move because row")
                #print(f"f1  = {RowOneNumber}/{ColOneNumber} f2 = {RowTwoNumber}/{ColTwoNumber}")

                topFlower = None

                # get flower objs
                flower1 = self.Board[RowOneNumber][ColOneNumber]
                flower2 = self.Board[RowTwoNumber][ColTwoNumber]
                self.Flower1OldPos = flower1.Y
                self.Flower2OldPos = flower2.Y

                if self.Flower1OldPos > self.Flower2OldPos:
                    topFlower = 2
                else:
                    topFlower = 1

                # Move the flower obj place on the board obj 
                #print(f"board item 1 {self.Board[RowOneNumber][ColOneNumber].ID} {self.Board[RowOneNumber][ColOneNumber].Name}")
                #print(f"board item 2 {self.Board[RowTwoNumber][ColTwoNumber].ID} {self.Board[RowTwoNumber][ColTwoNumber].Name}")

                tmp = self.Board[RowOneNumber][ColOneNumber]
                self.Board[RowOneNumber][ColOneNumber] = self.Board[RowTwoNumber][ColTwoNumber]
                self.Board[RowTwoNumber][ColTwoNumber] = tmp

                #print("-------------")
                #print(f"board item 1 {self.Board[RowOneNumber][ColOneNumber].ID} {self.Board[RowOneNumber][ColOneNumber].Name}")
                #print(f"board item 2 {self.Board[RowTwoNumber][ColTwoNumber].ID} {self.Board[RowTwoNumber][ColTwoNumber].Name}")
                #ic(self.Board)
                return (flower1,flower2,"row", topFlower)




            if ColOneNumber == (ColTwoNumber + 1) or ColTwoNumber == (ColOneNumber + 1):
                #print("move because col")
                #get flower objs
                flower1 = self.Board[RowOneNumber][ColOneNumber]
                flower2 = self.Board[RowTwoNumber][ColTwoNumber]
                self.Flower1OldPos = flower1.X
                self.Flower2OldPos = flower2.X
                if self.Flower1OldPos > self.Flower2OldPos:
                    topFlower = 2
                else:
                    topFlower = 1
                # Move the flower obj place on the board obj
                #print(f"board item 1 {self.Board[RowOneNumber][ColOneNumber].Name}")
                #print(f"board item 2 {self.Board[RowTwoNumber][ColTwoNumber].Name}")

                tmp = self.Board[RowOneNumber][ColOneNumber]
                self.Board[RowOneNumber][ColOneNumber] = self.Board[RowTwoNumber][ColTwoNumber]
                self.Board[RowTwoNumber][ColTwoNumber] = tmp

                #print("-------------")
                #print(f"board item 1 {self.Board[RowOneNumber][ColOneNumber].Name}")
                #print(f"board item 2 {self.Board[RowTwoNumber][ColTwoNumber].Name}")
                return (flower1,flower2,"col", topFlower)
        return None
    
    def CheckBoard(self):
        # Check for matches in Row
        for row in range(self.BoardRow - 2):
            for col in range(self.BoardCol):
                if self.Board[row][col].Name == self.Board[row + 1][col].Name and self.Board[row][col].Name == self.Board[row + 2][col].Name:
                    a = [(row,col),(row + 1,col),(row + 2,col)]
                    self.MatchesFound.append(a)
        # Check for matches in Col
        for col in range(self.BoardCol - 2):
            for row in range(self.BoardRow):
                if self.Board[row][col].Name == self.Board[row][col + 1].Name and self.Board[row][col].Name == self.Board[row][col + 2].Name:
                    a = [(row,col),(row,col + 1), (row, col + 2)]
                    self.MatchesFound.append(a)
    
    def DeleteAndReplaceFlowers(self):
        for matchItem in self.MatchesFound:
            for pos in matchItem:

                row,col = pos

                flower = self.Board[row][col]
                x = flower.X
                y = flower.Y
                if self.UserFirstMove:
                    self.UpdateScore(flower.Name)
                self.Board[row].remove(flower)

                f = self.CreateFlower(x,y)
                count = 0
                
                for r in self.Board:
                    if count == row:
                        r.insert(col,f)
                    count +=1

        self.MatchesFound.clear()
                    
    def MoveFlowerPairAnim(self, flower1, flower2, rowOrCol, top):
        if rowOrCol == "row":
            X1 = flower1.Rect.x
            X2 =flower2.Rect.x

            if top == 1:
                flower1.Y = flower1.Y + self.FlowerMatchSpeedAnim
                flower1.Rect.update(X1,flower1.Y,35,35)
                
                flower2.Y = flower2.Y - self.FlowerMatchSpeedAnim
                flower2.Rect.update(X2,flower2.Y,35,35)

            elif top == 2:
                flower1.Y = flower1.Y - self.FlowerMatchSpeedAnim
                flower1.Rect.update(X1,flower1.Y,35,35)

                flower2.Y = flower2.Y + self.FlowerMatchSpeedAnim
                flower2.Rect.update(X2,flower2.Y,35,35)

        if rowOrCol == "col":
            Y1 = flower1.Rect.y
            Y2 =flower2.Rect.y
            if top == 1:
                flower1.X = flower1.X + self.FlowerMatchSpeedAnim
                flower1.Rect.update(flower1.X,Y1,35,35)
                flower2.X = flower2.X - self.FlowerMatchSpeedAnim
                flower2.Rect.update(flower2.X,Y2,35,35)

            elif top == 2:
                flower1.X = flower1.X - self.FlowerMatchSpeedAnim
                flower1.Rect.update(flower1.X,Y1,35,35)
                flower2.X = flower2.X + self.FlowerMatchSpeedAnim
                flower2.Rect.update(flower2.X,Y2,35,35)
    
    def UpdateScore(self,name):
        for char in name:
            v = ord(char)
            #print(f"int = {v} char {char}") # Bug somewhere not sure but this line will help to display bug
            self.UserScore += v
            break

    def DrawBoard(self):
        for row in self.Board:
            for flower in row:
                self.CurrentScreen.blit(flower.Surf,(flower.X ,flower.Y))

    def Draw(self):
        self.CurrentScreen.blit(self.Background, (0,0))
        ScoreText = self.FontSmall.render("Your score is ", 1, self.TextColor)
        Score = self.FontSmall.render(f"{self.UserScore}", 1, self.TextColor)
        Time = self.FontSmall.render(f"Time is {self.CurrentTime}", 1, self.TextColor)

        self.CurrentScreen.blit(ScoreText, (950,50))
        self.CurrentScreen.blit(Score, (950,120))
        self.CurrentScreen.blit(Time, (950,190))
       
        self.DrawBoard()
        pygame.display.update()

    def Update(self, fps):
        self.FPS = fps
        if self.AnimData is not None:
            flower1, flower2, rowOrCol, top = self.AnimData
            self.MoveFlowerPairAnim(flower1, flower2, rowOrCol, top)

            if rowOrCol == "row":
                if self.Flower1OldPos == flower2.Y  and self.Flower2OldPos == flower1.Y  :
                    self.AnimData = None # set self.AnimData to None to stop anim

            if rowOrCol == "col":
                if self.Flower1OldPos == flower2.X and self.Flower2OldPos == flower1.X:
                    self.AnimData = None # set self.AnimData to None to stop anim

        else:
            self.DeleteAndReplaceFlowers() # delete flower to quickly
            x, y = pygame.mouse.get_pos()
            RowNumberClick = None
            ColNumberClick = None

            # get mosue x and y each Update
            for _r in self.Board:
               for flowerObj in _r:
                   if flowerObj.Rect.collidepoint((x,y)):
                     RowNumberClick = self.Board.index(_r)
                     ColNumberClick = _r.index(flowerObj)

            for event in pygame.event.get():
                 if event.type == pygame.QUIT: sys.exit()
                 if event.type == pygame.USEREVENT:
                     self.CurrentTime -= 1
                     if self.CurrentTime <= 0:
                        self.ScreenNeedsToChange = True
                        self.ScreenToChangeToo = "EndScreen"


                 if event.type == pygame.MOUSEBUTTONUP:
                     #print(f"row = {RowNumberClick} col = {ColNumberClick}")
                     self.FlowersSeletced.append((RowNumberClick, ColNumberClick))
                     if len(self.FlowersSeletced) == 2:
                         # Only should have 2 item in list
                         self.AnimData = self.CheckMove() # <- calls a few methods 
                         self.FlowersSeletced.clear()
            # check board for matches
            self.CheckBoard()
            

class Flower(pygame.sprite.Sprite):
    def __init__(self, name, x, y, w=35, h=35):
        super(Flower,self).__init__()
        self.Surf = None
        self.X = float(x)
        self.Y = float(y)
        self.Rect = pygame.Rect(x,y,w,h)
        self.Name = name
        self.ID = random.randint(10000,10000000) # Not sure if i really need this.

    def SetSurf(self, img):
        self.Surf = img

    def SetXY(self,x,y):
        self.X = x
        self.Y = y
        self.Rect = self.Surf.get_rect(center=(x,y))

