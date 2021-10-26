import pygame
import random
import time

class Game:
    def __init__(self):
        print("Loaded")
        self.screen_width = 1280
        self.screen_hight = 720
        self.running = True
        self.board_row = 12
        self.board_col = 22
        self.clicked_flowers = []
        self.matches = []
        self.score = 0
        self.seconds = 0
        self.gamemode = "MainMenu"
        self.end_time = 600
        self.version = "0.1.0-01.21"

        pygame.init()
        print("pygame loaded")
        #self.font = pygame.font.SysFont("verdana",22)
        #self.font2 = pygame.font.SysFont("verdana",16)
        self.screen = pygame.display.set_mode([self.screen_width, self.screen_hight])
        #self.board = self.mk_board()
        #self.background = pygame.image.load("background0.png")
        #self.white = pygame.Color(255,255,255)
        #self.black = pygame.Color(0,0,0)
        #self.title = self.mk_title()
        #self.start_text = self.mk_start()
        #self.start_btn = pygame.Surface((225,37))
        #self.start_text_x = 520 
        #self.start_text_y = 280
        #self.start_rect = self.start_btn.get_rect(center=(self.start_text_x,self.start_text_y))
        #self.start_time = 0
        print("game loaded")
        
        self.MenuScreen = MainMenu(self.screen)

    def StartMainLoop(self):
        while self.running:
            if self.gamemode == "MainMenu":
                self.MenuScreen.Draw()
                self.MenuScreen.Update()
                

    def run_mainloop(self):
        clock_fps = pygame.time.Clock()
        self.count = 0
        self.start_time = pygame.time.get_ticks()
        
        while self.running:
            if self.gamemode == "start":
                self.menu_draw()
                pygame.display.update()
                self.process_input()

#            if self.gamemode == "end":
#                self.end_draw()
#                pygame.display.update()
#                self.process_input()
#
#            if self.gamemode == "game":
#                self.draw()
#                pygame.display.update()
#                self.process_input()
#                self.check_clicked_flowers()
#                self.check_board()
#            
#                self.seconds = (pygame.time.get_ticks() - self.start_time) / 1000
#                if self.seconds > self.end_time:
#                    #End game
#                    self.gamemode = "end"
#            
#                if self.count < 10:
#                    self.score = 0
#                    self.count +=1
#
            clock_fps.tick(30)
        pygame.quit()

    def draw(self):
        x = 775
        y = 100
        
        s_label = self.font.render("Score {}".format(self.score), 1, self.white)
        t = int(self.seconds)
        tt = self.end_time - t
        c_min = int(tt / 60)
        c_sec = int(tt % 60)
        timer_label = self.font.render("Time {}:{}".format(c_min,c_sec),1, self.white)

        self.screen.blit(self.background, (0,0))
        self.screen.blit(s_label, (1080,10))
        self.screen.blit(timer_label,(1080,35))
        for r in self.board:
            y += 40
            x = 100
            for c in r:
                img = c.surf
                x += 40
                c.set_xy(x,y)
                c.rect.update(x,y,35,35)
                self.screen.blit(img,(x,y))

    def process_input(self):
        x, y = pygame.mouse.get_pos()
        if self.gamemode == "game":
            for r in self.board:
                for c in r:
                    if c.rect.collidepoint((x,y)):
                        self.row_temp = self.board.index(r)
                        self.col_temp = r.index(c)
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONUP:
                if self.gamemode == "game":
                    self.clicked_flowers.append((self.row_temp, self.col_temp))
                if self.gamemode == "start":
                    x,y = pygame.mouse.get_pos()
                    if self.start_rect.collidepoint((x,y)):
                        self.gamemode = "game"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if self.gamemode == "end":
                    if event.key == pygame.K_SPACE:
                        self.restart_game()
                        self.end_time = (pygame.time.get_ticks() + (600 * 1000)) / 1000
                        self.gamemode = "game"

    def check_clicked_flowers(self):
        if len(self.clicked_flowers) == 2:
            one_row, one_col = self.clicked_flowers[0]
            two_row, two_col = self.clicked_flowers[1]
            if one_row == two_row or one_col == two_col:
                if two_row == one_row + 1 or one_row == two_row + 1:
                    self.move_flowers()
                if two_col == one_col + 1 or one_col == two_col + 1:
                    self.move_flowers()
            self.clicked_flowers.clear()

    def check_board(self):
        for row in range(self.board_row - 2):
            for col in range(self.board_col):

                if self.board[row][col].name == self.board[row + 1][col].name and self.board[row][col].name == self.board[row + 2][col].name:
                    a = [(row,col),(row + 1,col),(row + 2,col)]
                    self.matches.append(a)
                    self.score += 75
        
        self.replace_matches()
        # check cols
        for col in range(self.board_col - 2):
            for row in range(self.board_row):

                if self.board[row][col].name == self.board[row][col + 1].name and self.board[row][col].name == self.board[row][col + 2].name:
                    a = [(row,col),(row,col + 1), (row, col + 2)]
                    self.matches.append(a)
                    self.score += 64
        self.replace_matches()

    def replace_matches(self):
        for m in self.matches:
            for a in m:
                row,col = a
                item = self.board[row][col]
                self.board[row].remove(item)
                f = self.mk_flower()
                count = 0
                for r in self.board:
                    if count == row:
                        r.insert(col,f)
                    count +=1
        self.matches.clear()

    def move_flowers(self):
        one_row, one_col = self.clicked_flowers[0]
        two_row, two_col = self.clicked_flowers[1]
        self.board[one_row][one_col], self.board[two_row][two_col] = self.board[two_row][two_col], self.board[one_row][one_col] 

    def mk_board(self):
        b = []
        for r in range(self.board_row):
            b.append([])
        for row in b:
            for c in range(self.board_col):
                row.append(self.mk_flower())
        return b

    def mk_flower(self):
        num = random.randint(0,4)
        img = None
        sprit = None
        if num == 0:
            img = pygame.image.load("flower-r.png")
            sprit = Flower("red")
        if num == 1:
            img = pygame.image.load("flower-b.png")
            sprit = Flower("blue")
        if num == 2:
            img = pygame.image.load("flower-p.png")
            sprit = Flower("purple")
        if num == 3:
            img = pygame.image.load("flower-y.png")
            sprit = Flower("yellow")
        if num == 4:
            img = pygame.image.load("flower-g.png")
            sprit = Flower("green")
        sprit.set_surf(img)
        return sprit

    def restart_game(self):
        self.screen_width = 1280
        self.screen_hight = 720
        self.running = True
        self.board_row = 12
        self.board_col = 22
        self.clicked_flowers = []
        self.matches = []
        self.score = 0
        self.seconds = 0
        self.gamemode = "game"
        self.board = self.mk_board()
        self.start_text_x = 520
        self.start_text_y = 280
        self.start_time = 0
        self.count = 0



### helpers
    def get_fonts(self):
        for f in pygame.font.get_fonts():
            print(f)
    



class Flower(pygame.sprite.Sprite):
    def __init__(self,name):
        super(Flower,self).__init__()
        self.surf = None
        self.X = None
        self.Y = None
        self.rect = None
        self.name = name
        self.ID = random.randint(10000,10000000)

    def set_surf(self, img):
        self.surf = img

    def set_xy(self,x,y):
        self.X = x
        self.Y = y
        self.rect = self.surf.get_rect(center=(x,y))
