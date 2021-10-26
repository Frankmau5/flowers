import pygame
import sys

class NewGame:
    def __init__(self):
        self.Running = True
        self.GameMode = "MainMenu"
        self.ScreenWidth = 1280
        self.ScreenHight = 720
        
        pygame.init()
        pygame.font.init()
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
            if self.GameMode == "MainMenu":
                self.Modes["MainMenu"].Draw()
                self.Modes["MainMenu"].Update()

            if self.GameMode == "EndScreen":
                self.Modes["EndScreen"].Draw()
                self.Modes["EndScreen"].Update()

            if self.GameMode == "GameScreen":
                self.Modes["GameScreen"].Draw()
                self.Modes["GameScreen"].Update()

            self.CheckIfScreenChange()


    def CheckIfScreenChange(self):
        if self.Modes[self.GameMode].ScreenNeedsToChange:
            screenName = self.Modes[self.GameMode].ScreenToChangeToo
            self.GameMode = screenName
            
            # reset the screen change back to start
            self.Modes[self.GameMode].ScreenToChangeToo = ""
            self.Modes[self.GameMode].ScreenNeedsToChange = False

    def GetFonts(self):
        for f in pygame.font.get_fonts():
            print(f)

class MainMenu(object):
    def __init__(self, screen, sWidth ):
        self.CurrentScreen = screen
        self.ScreenWidth = sWidth
        self.Background = None
        self.ScreenNeedsToChange = False
        self.ScreenToChangeToo = ""
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
        GameName = self.FontBig.render(f"Flowers", 1, self.TextColor)
        StartGame = self.FontSmall.render(f"Press space to start!", 1, self.TextColor)

        self.CurrentScreen.blit(self.Background, (0,0))
        self.CurrentScreen.blit(GameName, ((self.GameNameWidth + 40), 10))
        self.CurrentScreen.blit(StartGame, (self.GameNameWidth, 650))
        pygame.display.update()

    def Update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    print("Space")
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

    def Update(self):
       for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    print("Space")
                    self.ScreenNeedsToChange = True
                    self.ScreenToChangeToo = "MainMenu"


class GameScreen(object):
    def __init__(self, screen, sWidth, score=0):
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
        self.CurrentScreen.blit(self.Background, (0,0))
        pygame.display.update()

    def Update(self):
       for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
