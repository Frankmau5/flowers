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
        return modes

    def StartMainLoop(self):
        while self.Running:
            if self.GameMode == "MainMenu":
                self.Modes["MainMenu"].Draw()
                self.Modes["MainMenu"].Update()

    def GetFonts(self):
        for f in pygame.font.get_fonts():
            print(f)

class MainMenu(object):
    def __init__(self, screen, sWidth ):
        self.CurrentScreen = screen
        self.ScreenWidth = sWidth
        self.Background = None
        self.TextColor = 255,255,255
        #self.TextColor = 231,111,81
        self.Load()
        

    def Load(self):
        self.Background = pygame.image.load("imgs/background-main-menu.png")
        self.FontBig = pygame.font.Font("fonts/SanMarinoBeach.ttf",82)
        self.FontSmall = pygame.font.Font("fonts/SanMarinoBeach.ttf",38)
        self.GameNameWidth = (self.ScreenWidth / 2) - 240
    def ClearScreen(self):
        black = 0, 0, 0
        self.CurrentScreen.fill(black)
        pygame.display.update()

    def Draw(self):
        GameName = self.FontBig.render(f"Flowers", 1, self.TextColor)
        StartGame = self.FontSmall.render(f"Press space to start!", 1, self.TextColor)

        self.CurrentScreen.blit(self.Background, (0,0))
        self.CurrentScreen.blit(GameName, ((self.GameNameWidth + 50), 10))
        self.CurrentScreen.blit(StartGame, (self.GameNameWidth, 650))
        pygame.display.update()

    def Update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    print("Space")





class EndScreen(object):
    def __init__(self):
        pass

    def Draw(self):
        s_label = self.font.render("Score {}".format(self.score), 1, self.white)
        msg = self.font.render("Your score was {}.".format(self.score), 1, self.black)
        msg2 = self.font.render("Press esc to quit or press space to start again",1,self.black)
        self.screen.fill(self.white)
        self.screen.blit(self.background, (0,0))
        self.screen.blit(s_label, (1080,10))
        self.screen.blit(msg, (320,360))
        self.screen.blit(msg2,(320,380))

    def Update(self):
        pass

class GameScreen(object):
    def __init__(self):
        pass

    def Draw(self):
        pass

    def Update(self):
        pass
