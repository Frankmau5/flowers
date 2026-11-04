from array import array
import json
import math
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
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
        self.Sound = SoundFX()
        self.Clock = pygame.time.Clock()
        self.Screen = pygame.display.set_mode([self.ScreenWidth, self.ScreenHight])
        self.Modes = self.LoadModes()
        

    def LoadModes(self):
        modes = dict()
        modes["MainMenu"] = MainMenu(self.Screen, self.ScreenWidth, self.Sound)
        modes["EndScreen"] = EndScreen(self.Screen, self.ScreenWidth, 0, self.Sound)
        modes["GameScreen"] = GameScreen(self.Screen, self.ScreenWidth, 0, self.Sound)
        
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
            self.Clock.tick(60)

    def CheckIfScreenChange(self):
        if self.Modes[self.GameMode].ScreenNeedsToChange:
            screenName = self.Modes[self.GameMode].ScreenToChangeToo
            self.GameMode = screenName

            if self.GameMode == "GameScreen":
                self.Modes["GameScreen"] = GameScreen(self.Screen, self.ScreenWidth, 0, self.Sound)
                pygame.event.clear(pygame.USEREVENT)
                pygame.time.set_timer(pygame.USEREVENT, 1000)

            if self.GameMode == "EndScreen":
                pygame.time.set_timer(pygame.USEREVENT, 0)
                score = self.Modes["GameScreen"].UserScore
                self.Modes["EndScreen"].SetFinalScore(score)
                self.Modes["GameScreen"] = GameScreen(self.Screen, self.ScreenWidth, 0, self.Sound)
            
            # reset the screen change back to start
            self.Modes[self.GameMode].ScreenToChangeToo = ""
            self.Modes[self.GameMode].ScreenNeedsToChange = False

    def GetFonts(self):
        for f in pygame.font.get_fonts():
            print(f)


class SoundFX(object):
    def __init__(self):
        self.Enabled = False
        self.Sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.Enabled = True
            self.Sounds["select"] = self._make_tone([660], 0.06, 0.25)
            self.Sounds["swap"] = self._make_tone([440, 554], 0.05, 0.25)
            self.Sounds["shuffle"] = self._make_tone([330, 440, 554, 660], 0.04, 0.25)
            self.Sounds["tick"] = self._make_tone([880], 0.04, 0.2)
            self.Sounds["levelup"] = self._make_tone([523, 659, 784, 1046], 0.08, 0.35)
            for combo in range(1, 8):
                base = 440 * (1.12 ** (combo - 1))
                self.Sounds[f"match_{combo}"] = self._make_tone([base, base * 1.25, base * 1.5], 0.06, 0.32)
        except Exception:
            self.Enabled = False

    def _make_tone(self, freqs, duration_per_note, volume=0.3):
        sample_rate = 22050
        buf = array("h")
        for freq in freqs:
            n_samples = int(sample_rate * duration_per_note)
            for i in range(n_samples):
                env = 1.0 - (i / max(1, n_samples))
                val = int(32767 * volume * env * math.sin(2.0 * math.pi * freq * i / sample_rate))
                buf.append(val)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def Play(self, name):
        if self.Enabled and name in self.Sounds:
            try:
                self.Sounds[name].play()
            except Exception:
                pass

    def PlayMatch(self, combo):
        idx = max(1, min(7, combo))
        self.Play(f"match_{idx}")


class HighScoreManager(object):
    FILE_PATH = "highscores.json"

    @classmethod
    def LoadScores(cls):
        if os.path.exists(cls.FILE_PATH):
            try:
                with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return [int(x) for x in data[:5]]
            except Exception:
                pass
        return []

    @classmethod
    def AddScore(cls, score):
        scores = cls.LoadScores()
        scores.append(int(score))
        scores = sorted(scores, reverse=True)[:5]
        try:
            with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(scores, f)
        except Exception:
            pass
        return scores


class ScreenShader(object):
    def __init__(self, width=1280, height=720):
        self.Width = width
        self.Height = height
        self.Particles = [
            [
                random.uniform(0, width),
                random.uniform(0, height),
                random.uniform(0.6, 1.8),
                random.uniform(3.0, 7.0),
                random.uniform(0, math.pi * 2),
                random.choice([(255, 220, 130), (255, 160, 220), (160, 220, 255), (190, 255, 180)]),
            ]
            for _ in range(45)
        ]

    def DrawAtmosphere(self, screen):
        t = pygame.time.get_ticks() * 0.003

        # Animated atmospheric color-grade & sunbeam overlay
        overlay = pygame.Surface((self.Width, self.Height), pygame.SRCALPHA)
        for i in range(5):
            beam_x = int(200 + i * 240 + math.sin(t + i) * 60)
            beam_alpha = int(18 + 12 * math.sin(t * 1.3 + i))
            points = [(beam_x - 60, 0), (beam_x + 60, 0), (beam_x + 220, self.Height), (beam_x - 20, self.Height)]
            pygame.draw.polygon(overlay, (255, 245, 200, beam_alpha), points)
        screen.blit(overlay, (0, 0))

        # Floating glowing pollen / petal particles
        particle_layer = pygame.Surface((self.Width, self.Height), pygame.SRCALPHA)
        for p in self.Particles:
            px, py, speed, radius, phase, color = p
            py -= speed
            px += math.sin(t * 1.2 + phase) * 0.8
            if py < -20:
                py = float(self.Height + 20)
                px = random.uniform(0, self.Width)
            p[0], p[1] = px, py

            glow_alpha = int(90 + 80 * math.sin(t * 2.0 + phase))
            r, g, b = color
            pygame.draw.circle(particle_layer, (r, g, b, glow_alpha // 3), (int(px), int(py)), int(radius * 2.4))
            pygame.draw.circle(particle_layer, (r, g, b, glow_alpha), (int(px), int(py)), int(radius))
            pygame.draw.circle(particle_layer, (255, 255, 255, 210), (int(px), int(py)), max(1, int(radius * 0.45)))
        screen.blit(particle_layer, (0, 0))

    def DrawGlowText(
        self,
        screen,
        font,
        text,
        x,
        y,
        main_color=(245, 235, 255),
        glow_color=(95, 45, 190),
        offset=2,
        max_width=None,
        center_width=None,
    ):
        surf = font.render(text, True, main_color)
        glow = font.render(text, True, glow_color)
        if max_width is not None and surf.get_width() > max_width:
            scale = max_width / float(surf.get_width())
            new_w = max(1, int(surf.get_width() * scale))
            new_h = max(1, int(surf.get_height() * scale))
            surf = pygame.transform.smoothscale(surf, (new_w, new_h))
            glow = pygame.transform.smoothscale(glow, (new_w, new_h))
        draw_x = int(x + (center_width - surf.get_width()) / 2) if center_width is not None else int(x)
        draw_y = int(y)
        for ox, oy in (
            (-offset, 0),
            (offset, 0),
            (0, -offset),
            (0, offset),
            (-offset + 1, -offset + 1),
            (offset - 1, -offset + 1),
            (-offset + 1, offset - 1),
            (offset - 1, offset - 1),
        ):
            screen.blit(glow, (draw_x + ox, draw_y + oy))
        screen.blit(surf, (draw_x, draw_y))

    def DrawGlowPanel(self, screen, x, y, w, h, hovered=False):
        t = pygame.time.get_ticks() * 0.003
        pulse = (math.sin(t * 1.5) + 1.0) * 0.5
        panel = pygame.Surface((w + 32, h + 32), pygame.SRCALPHA)
        bg_alpha = 200 if hovered else 160
        pygame.draw.rect(panel, (35, 20, 80, bg_alpha), (16, 16, w, h), border_radius=20)
        for layer in range(4, 0, -1):
            spread = layer * 3
            a = int((45 if hovered else 25) * (5 - layer) / 4)
            pygame.draw.rect(
                panel,
                (190, 130, 255, a),
                (16 - spread, 16 - spread, w + spread * 2, h + spread * 2),
                width=3,
                border_radius=20 + spread,
            )
        border_col = (255, 230, 150, 255) if hovered else (200, 165, 255, int(190 + 60 * pulse))
        pygame.draw.rect(panel, border_col, (16, 16, w, h), width=3, border_radius=20)
        screen.blit(panel, (x - 16, y - 16))



class MainMenu(object):
    def __init__(self, screen, sWidth, sound=None):
        self.CurrentScreen = screen
        self.ScreenWidth = sWidth
        self.Sound = sound
        self.Background = None
        self.ScreenNeedsToChange = False
        self.ScreenToChangeToo = ""
        self.TextColor = 110, 68, 255
        self.Cloud1XY = (float(10),float(10))
        self.Cloud2XY = (float(380),float(130))
        self.Cloud3XY = (float(1000),float(80))
        self.CloudSpeed = float(2.0)
        self.Shader = ScreenShader(sWidth, 720)
        self.Load()
        

    def Load(self):
        self.Background = pygame.image.load("imgs/background.png")
        self.cloud1 = pygame.image.load("imgs/cloud1.png")
        self.cloud2 = pygame.image.load("imgs/cloud2.png")
        self.cloud3 = pygame.image.load("imgs/cloud3.png")
        font_path = "fonts/GameFont.ttf" if os.path.exists("fonts/GameFont.ttf") else "fonts/SanMarinoBeach.ttf"
        self.FontBig = pygame.font.Font(font_path, 92)
        self.FontSmall = pygame.font.Font(font_path, 36)
        self.GameNameWidth = (self.ScreenWidth / 2) - 240
    
    def ClearScreen(self):
        black = 0, 0, 0
        self.CurrentScreen.fill(black)

    def DrawMenuShader(self):
        t = pygame.time.get_ticks() * 0.003
        self.Shader.DrawAtmosphere(self.CurrentScreen)

        # Glowing shader title & interactive start banner
        title_str = "Flowers"
        title_surf = self.FontBig.render(title_str, True, (245, 235, 255))
        tx = int((self.ScreenWidth - title_surf.get_width()) / 2)
        ty = int(24 + math.sin(t * 1.6) * 6)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontBig, title_str, tx, ty, offset=4)

        # Start button with hover & pulsing neon border shader
        start_str = "Click or press space to start!"
        start_surf = self.FontSmall.render(start_str, True, (250, 245, 255))
        bw = start_surf.get_width() + 56
        bh = start_surf.get_height() + 28
        bx = int((self.ScreenWidth - bw) / 2)
        by = 615
        btn_rect = pygame.Rect(bx, by, bw, bh)
        hovered = btn_rect.collidepoint(pygame.mouse.get_pos())

        self.Shader.DrawGlowPanel(self.CurrentScreen, bx, by, bw, bh, hovered=hovered)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, start_str, bx + 28, by + 14, offset=2)

    def Draw(self):
        self.CurrentScreen.blit(self.Background, (0,0))
        self.CurrentScreen.blit(self.cloud1, self.Cloud1XY)
        self.CurrentScreen.blit(self.cloud2, self.Cloud2XY)
        self.CurrentScreen.blit(self.cloud3, self.Cloud3XY)

        self.DrawMenuShader()
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
                    if self.Sound:
                        self.Sound.Play("select")
                    self.ScreenNeedsToChange = True
                    self.ScreenToChangeToo = "GameScreen"

            if event.type == pygame.MOUSEBUTTONUP:
                if self.Sound:
                    self.Sound.Play("select")
                self.ScreenNeedsToChange = True
                self.ScreenToChangeToo = "GameScreen"


class EndScreen(object):
    def __init__(self, screen, sWidth, score, sound=None):
        self.CurrentScreen = screen
        self.ScreenWidth = sWidth
        self.UserScore = score
        self.Sound = sound
        self.HighScores = HighScoreManager.LoadScores()
        self.ScreenNeedsToChange = False
        self.ScreenToChangeToo = ""
        self.Background = None
        self.TextColor = 110, 68, 255
        self.Shader = ScreenShader(sWidth, 720)
        self.Load()

    def SetFinalScore(self, score):
        self.UserScore = score
        self.HighScores = HighScoreManager.AddScore(score)

    def Load(self):
        self.Background = pygame.image.load("imgs/background-main-menu.png")
        font_path = "fonts/GameFont.ttf" if os.path.exists("fonts/GameFont.ttf") else "fonts/SanMarinoBeach.ttf"
        self.FontBig = pygame.font.Font(font_path, 72)
        self.FontSmall = pygame.font.Font(font_path, 34)
        self.FontTiny = pygame.font.Font(font_path, 26)
        self.GameNameWidth = (self.ScreenWidth / 2) - 240
    
    def ClearScreen(self):
        black = 0, 0, 0
        self.CurrentScreen.fill(black)

    def Draw(self):
        t = pygame.time.get_ticks() * 0.003
        msg1_str = f"Your Score: {self.UserScore}"
        msg2_str = "Press ESC to quit or Click / Space to play again"
        msg1_surf = self.FontBig.render(msg1_str, True, (245, 235, 255))
        msg2_surf = self.FontSmall.render(msg2_str, True, (245, 235, 255))

        self.ClearScreen()
        self.CurrentScreen.blit(self.Background, (0,0))
        self.Shader.DrawAtmosphere(self.CurrentScreen)

        pw = max(460, msg1_surf.get_width() + 64)
        px = int((self.ScreenWidth - pw) / 2)
        ty = int(50 + math.sin(t * 1.6) * 6)
        self.Shader.DrawGlowPanel(self.CurrentScreen, px, ty - 16, pw, msg1_surf.get_height() + 32)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontBig, msg1_str, px, ty, offset=3, max_width=pw - 32, center_width=pw)

        # High scores leaderboard panel
        hs_w, hs_h = 460, 290
        hs_x = int((self.ScreenWidth - hs_w) / 2)
        hs_y = 225
        self.Shader.DrawGlowPanel(self.CurrentScreen, hs_x, hs_y, hs_w, hs_h)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, "Top High Scores", hs_x, hs_y + 18, main_color=(255, 235, 150), offset=2, center_width=hs_w)
        for idx, hs in enumerate(self.HighScores[:5]):
            color = (255, 240, 140) if hs == self.UserScore and self.UserScore > 0 else (240, 230, 255)
            self.Shader.DrawGlowText(
                self.CurrentScreen,
                self.FontTiny,
                f"#{idx + 1}    {hs} pts",
                hs_x,
                hs_y + 80 + idx * 40,
                main_color=color,
                offset=2,
                center_width=hs_w,
            )

        bw = min(1100, msg2_surf.get_width() + 64)
        bh = msg2_surf.get_height() + 28
        bx = int((self.ScreenWidth - bw) / 2)
        by = 590
        hovered = pygame.Rect(bx, by, bw, bh).collidepoint(pygame.mouse.get_pos())
        self.Shader.DrawGlowPanel(self.CurrentScreen, bx, by, bw, bh, hovered=hovered)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, msg2_str, bx, by + 14, offset=2, max_width=bw - 32, center_width=bw)
        pygame.display.update()

    def Update(self, fps):
       for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    #print("Space")
                    if self.Sound:
                        self.Sound.Play("select")
                    self.ScreenNeedsToChange = True
                    self.ScreenToChangeToo = "MainMenu"

            if event.type == pygame.MOUSEBUTTONUP:
                if self.Sound:
                    self.Sound.Play("select")
                self.ScreenNeedsToChange = True
                self.ScreenToChangeToo = "MainMenu"


class GameScreen(object):
    COLOR_MAP = {
        "red": (255, 90, 90),
        "blue": (90, 175, 255),
        "green": (110, 255, 130),
        "purple": (210, 110, 255),
        "yellow": (255, 235, 95),
    }

    def __init__(self, screen, sWidth, score=0, sound=None):
        self.CurrentScreen = screen
        self.ScreenWidth = sWidth
        self.UserScore = score
        self.Sound = sound
        self.CurrentTime = 180
        self.ScreenNeedsToChange = False
        self.ScreenToChangeToo = ""
        self.Background = None
        self.TextColor = 110, 68, 255
        self.BoardRow = 8
        self.BoardCol = 10
        self.CellSize = 75
        self.FlowerSize = 60
        self.BoardStartX = 80
        self.BoardStartY = 60
        self.Board = None
        self.FlowersSeletced = list()
        self.AnimData = None # None mean not anim needed
        self.FlowerMatchSpeedAnim = float(5.0)
        self.FallSpeed = float(9.0)
        self.IsFalling = False
        self.Flower1OldPos = 0
        self.Flower2OldPos = 0
        self.MatchesFound = list()
        self.UserFirstMove = False
        self.ComboCount = 0
        self.Level = 1
        self.LevelTarget = 1500
        self.ShufflesLeft = 3
        self.ShuffleBtnRect = pygame.Rect(875, 515, 355, 58)
        self.HelpBtnRect = pygame.Rect(875, 595, 355, 58)
        self.ShowHowToPlay = True
        self.HowToPlayCloseRect = pygame.Rect(410, 580, 460, 62)
        self.FloatingTexts = list()
        self.BurstParticles = list()
        self.DragStartCell = None
        self.LastActionTime = pygame.time.get_ticks()
        self.HintPair = None
        self.FPS = 0
        self.Shader = ScreenShader(sWidth, 720)
        self.Load()
        
    def Load(self):
        self.Background = pygame.image.load("imgs/background-main-menu.png")
        size = (self.FlowerSize, self.FlowerSize)
        self.RFlower = pygame.transform.smoothscale(pygame.image.load("imgs/flower-r.png"), size)
        self.BFlower = pygame.transform.smoothscale(pygame.image.load("imgs/flower-b.png"), size)
        self.GFlower = pygame.transform.smoothscale(pygame.image.load("imgs/flower-g.png"), size)
        self.PFlower = pygame.transform.smoothscale(pygame.image.load("imgs/flower-p.png"), size)
        self.YFlower = pygame.transform.smoothscale(pygame.image.load("imgs/flower-y.png"), size)
        font_path = "fonts/GameFont.ttf" if os.path.exists("fonts/GameFont.ttf") else "fonts/SanMarinoBeach.ttf"
        self.FontBig = pygame.font.Font(font_path, 56)
        self.FontSmall = pygame.font.Font(font_path, 30)
        self.FontTiny = pygame.font.Font(font_path, 21)
        self.GameNameWidth = (self.ScreenWidth / 2) - 240
        self.Board = self.BuildBoard()
        while self.HasMatch():
            self.CheckBoard()
            self.DeleteAndReplaceFlowers(instant=True)
    
    def ClearScreen(self):
        black = 0, 0, 0
        self.CurrentScreen.fill(black)

    def CellToXY(self, r_idx, c_idx):
        pad = (self.CellSize - self.FlowerSize) // 2
        x = self.BoardStartX + c_idx * self.CellSize + pad
        y = self.BoardStartY + r_idx * self.CellSize + pad
        return float(x), float(y)

    def BuildBoard(self):
        # r = row, c = col
        Board = list()

        for _r in range(self.BoardRow):
            Board.append(list())

        for r_idx, r in enumerate(Board):
            for c_idx in range(self.BoardCol):
                x, y = self.CellToXY(r_idx, c_idx)
                r.append(self.CreateFlower(x, y))
        
        return Board

    def CreateFlower(self, x, y, special=None):
        num = random.randint(0,4)
        img = None
        sprite = None

        if num == 0:
            sprite = Flower("red", x, y, self.FlowerSize, self.FlowerSize)
            img = self.RFlower
        if num == 1:
            sprite = Flower("blue", x, y, self.FlowerSize, self.FlowerSize)
            img = self.BFlower
        if num == 2:
            sprite = Flower("purple", x, y, self.FlowerSize, self.FlowerSize)
            img = self.PFlower
        if num == 3:
            sprite = Flower("yellow", x, y, self.FlowerSize, self.FlowerSize)
            img = self.YFlower
        if num == 4:
            sprite = Flower("green", x, y, self.FlowerSize, self.FlowerSize)
            img = self.GFlower

        sprite.SetSurf(img)
        sprite.Special = special
        return sprite

    def GetFlowerSurfByName(self, name):
        return {
            "red": self.RFlower,
            "blue": self.BFlower,
            "green": self.GFlower,
            "purple": self.PFlower,
            "yellow": self.YFlower,
        }[name]

    def HasMatch(self):
        for row in range(self.BoardRow - 2):
            for col in range(self.BoardCol):
                if self.Board[row][col].Name == self.Board[row + 1][col].Name and self.Board[row][col].Name == self.Board[row + 2][col].Name:
                    return True
        for col in range(self.BoardCol - 2):
            for row in range(self.BoardRow):
                if self.Board[row][col].Name == self.Board[row][col + 1].Name and self.Board[row][col].Name == self.Board[row][col + 2].Name:
                    return True
        return False

    def FindHintMove(self):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(self.BoardRow):
            for c in range(self.BoardCol):
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.BoardRow and 0 <= nc < self.BoardCol:
                        self.Board[r][c], self.Board[nr][nc] = self.Board[nr][nc], self.Board[r][c]
                        matched = self.HasMatch()
                        self.Board[r][c], self.Board[nr][nc] = self.Board[nr][nc], self.Board[r][c]
                        if matched:
                            return ((r, c), (nr, nc))
        return None

    def ShuffleBoard(self):
        if self.Sound:
            self.Sound.Play("shuffle")
        flat = [flower for row in self.Board for flower in row]
        random.shuffle(flat)
        idx = 0
        for r_idx in range(self.BoardRow):
            for c_idx in range(self.BoardCol):
                f = flat[idx]
                idx += 1
                tx, ty = self.CellToXY(r_idx, c_idx)
                f.X = tx
                f.Y = ty - self.CellSize * 2
                f.TargetX = tx
                f.TargetY = ty
                f.Rect.update(f.X, f.Y, self.FlowerSize, self.FlowerSize)
                self.Board[r_idx][c_idx] = f
        while self.HasMatch():
            self.CheckBoard()
            self.DeleteAndReplaceFlowers(instant=True)
        self.IsFalling = True
        self.FlowersSeletced.clear()
        self.HintPair = None
        self.LastActionTime = pygame.time.get_ticks()
        self.AddFloatingText("SHUFFLED!", 450, 340, (180, 235, 255))

    def AddFloatingText(self, text, x, y, color=(255, 245, 160)):
        self.FloatingTexts.append([text, float(x), float(y), 255, color])

    def SpawnBurst(self, x, y, color_name):
        base_r, base_g, base_b = self.COLOR_MAP.get(color_name, (255, 220, 150))
        cx = x + self.FlowerSize * 0.5
        cy = y + self.FlowerSize * 0.5
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2.0, 6.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 1.5
            radius = random.uniform(4.0, 8.0)
            self.BurstParticles.append([cx, cy, vx, vy, radius, 255, (base_r, base_g, base_b)])

    def CheckMove(self):
        RowOneNumber, ColOneNumber = self.FlowersSeletced[0]
        RowTwoNumber, ColTwoNumber = self.FlowersSeletced[1]

        if RowOneNumber is None or ColOneNumber is None or RowTwoNumber is None or ColTwoNumber is None:
            return None

        if (RowOneNumber, ColOneNumber) == (RowTwoNumber, ColTwoNumber):
            return None

        dr = abs(RowOneNumber - RowTwoNumber)
        dc = abs(ColOneNumber - ColTwoNumber)
        # Allow orthogonal (horizontal/vertical) AND diagonal neighbor movement
        if max(dr, dc) != 1:
            return None

        flower1 = self.Board[RowOneNumber][ColOneNumber]
        flower2 = self.Board[RowTwoNumber][ColTwoNumber]
        target1_x, target1_y = self.CellToXY(RowTwoNumber, ColTwoNumber)
        target2_x, target2_y = self.CellToXY(RowOneNumber, ColOneNumber)
        self.Flower1OldPos = (flower1.X, flower1.Y)
        self.Flower2OldPos = (flower2.X, flower2.Y)

        flower1.TargetX, flower1.TargetY = target1_x, target1_y
        flower2.TargetX, flower2.TargetY = target2_x, target2_y

        tmp = self.Board[RowOneNumber][ColOneNumber]
        self.Board[RowOneNumber][ColOneNumber] = self.Board[RowTwoNumber][ColTwoNumber]
        self.Board[RowTwoNumber][ColTwoNumber] = tmp

        self.UserFirstMove = True
        self.ComboCount = 0
        self.HintPair = None
        self.LastActionTime = pygame.time.get_ticks()
        if self.Sound:
            self.Sound.Play("swap")

        return (flower1, flower2, target1_x, target1_y, target2_x, target2_y)
    
    def CheckBoard(self):
        # Check for matches in Row (vertical runs of 3)
        for row in range(self.BoardRow - 2):
            for col in range(self.BoardCol):
                if self.Board[row][col].Name == self.Board[row + 1][col].Name and self.Board[row][col].Name == self.Board[row + 2][col].Name:
                    a = [(row,col),(row + 1,col),(row + 2,col)]
                    self.MatchesFound.append(a)
        # Check for matches in Col (horizontal runs of 3)
        for col in range(self.BoardCol - 2):
            for row in range(self.BoardRow):
                if self.Board[row][col].Name == self.Board[row][col + 1].Name and self.Board[row][col].Name == self.Board[row][col + 2].Name:
                    a = [(row,col),(row,col + 1), (row, col + 2)]
                    self.MatchesFound.append(a)
    
    def DeleteAndReplaceFlowers(self, instant=False):
        if not self.MatchesFound:
            if not instant:
                self.ComboCount = 0
            return

        # Count how many 3-runs each coordinate participates in to detect 4+, 5+, and L/T shapes
        coord_counts = {}
        seen = set()
        ordered_positions = []
        for matchItem in self.MatchesFound:
            for pos in matchItem:
                coord_counts[pos] = coord_counts.get(pos, 0) + 1
                if pos not in seen:
                    seen.add(pos)
                    ordered_positions.append(pos)

        self.MatchesFound.clear()

        # Expand special power-up flowers that are part of the match
        expanded = list(ordered_positions)
        expanded_set = set(ordered_positions)
        idx = 0
        while idx < len(expanded):
            r, c = expanded[idx]
            idx += 1
            fl = self.Board[r][c]
            if fl is None:
                continue
            if fl.Special == "line":
                for cc in range(self.BoardCol):
                    if (r, cc) not in expanded_set:
                        expanded_set.add((r, cc))
                        expanded.append((r, cc))
                for rr in range(self.BoardRow):
                    if (rr, c) not in expanded_set:
                        expanded_set.add((rr, c))
                        expanded.append((rr, c))
            elif fl.Special == "bomb":
                for rr in range(max(0, r - 1), min(self.BoardRow, r + 2)):
                    for cc in range(max(0, c - 1), min(self.BoardCol, c + 2)):
                        if (rr, cc) not in expanded_set:
                            expanded_set.add((rr, cc))
                            expanded.append((rr, cc))
            elif fl.Special == "rainbow":
                target_color = fl.Name
                for rr in range(self.BoardRow):
                    for cc in range(self.BoardCol):
                        if self.Board[rr][cc].Name == target_color and (rr, cc) not in expanded_set:
                            expanded_set.add((rr, cc))
                            expanded.append((rr, cc))

        if instant:
            for r, c in expanded:
                tx, ty = self.CellToXY(r, c)
                self.Board[r][c] = self.CreateFlower(tx, ty)
            return

        # Determine if this match earns a new special power-up flower
        spawn_special = None
        spawn_pos = ordered_positions[0]
        spawn_color = self.Board[spawn_pos[0]][spawn_pos[1]].Name
        if len(ordered_positions) >= 6:
            spawn_special = "bomb"
        elif len(ordered_positions) == 5:
            spawn_special = "rainbow"
        elif len(ordered_positions) == 4:
            spawn_special = "line"

        if self.UserFirstMove:
            self.ComboCount += 1
            if self.Sound:
                self.Sound.PlayMatch(self.ComboCount)

            points_earned = len(expanded) * 100 * self.ComboCount
            self.UserScore += points_earned

            avg_x = sum(self.Board[r][c].X for r, c in expanded) / len(expanded)
            avg_y = sum(self.Board[r][c].Y for r, c in expanded) / len(expanded)
            label = f"+{points_earned}" if self.ComboCount == 1 else f"+{points_earned} ({self.ComboCount}x COMBO!)"
            self.AddFloatingText(label, avg_x, avg_y, (255, 245, 140))

            if len(ordered_positions) >= 4:
                self.CurrentTime += 3
                self.AddFloatingText("+3s TIME BONUS!", avg_x, avg_y - 32, (150, 255, 190))

            if self.UserScore >= self.LevelTarget:
                self.Level += 1
                self.LevelTarget += self.Level * 1800
                self.CurrentTime += 25
                self.ShufflesLeft = min(5, self.ShufflesLeft + 1)
                if self.Sound:
                    self.Sound.Play("levelup")
                self.AddFloatingText(f"LEVEL {self.Level}! +25s", 380, 300, (255, 210, 255))

        for r, c in expanded:
            fl = self.Board[r][c]
            if self.UserFirstMove:
                self.SpawnBurst(fl.X, fl.Y, fl.Name)
            self.Board[r][c] = None

        if self.UserFirstMove and spawn_special is not None:
            sr, sc = spawn_pos
            tx, ty = self.CellToXY(sr, sc)
            special_flower = Flower(spawn_color, tx, ty, self.FlowerSize, self.FlowerSize)
            special_flower.SetSurf(self.GetFlowerSurfByName(spawn_color))
            special_flower.Special = spawn_special
            self.Board[sr][sc] = special_flower

        # Apply column gravity so existing flowers slide down and new ones drop from the top
        for c in range(self.BoardCol):
            remaining = [self.Board[r][c] for r in range(self.BoardRow - 1, -1, -1) if self.Board[r][c] is not None]
            missing_count = self.BoardRow - len(remaining)
            for idx_from_bottom, fl in enumerate(remaining):
                target_r = self.BoardRow - 1 - idx_from_bottom
                tx, ty = self.CellToXY(target_r, c)
                fl.TargetX = tx
                fl.TargetY = ty
                self.Board[target_r][c] = fl
            for m in range(missing_count):
                target_r = missing_count - 1 - m
                tx, ty = self.CellToXY(target_r, c)
                start_y = self.BoardStartY - (m + 1) * self.CellSize
                new_fl = self.CreateFlower(tx, start_y)
                new_fl.TargetX = tx
                new_fl.TargetY = ty
                self.Board[target_r][c] = new_fl

        self.IsFalling = True
        self.LastActionTime = pygame.time.get_ticks()

    def UpdateFallingFlowers(self):
        still_falling = False
        s = self.FlowerSize
        for row in self.Board:
            for fl in row:
                if abs(fl.Y - fl.TargetY) > 0.5:
                    still_falling = True
                    if fl.Y < fl.TargetY:
                        fl.Y = min(fl.TargetY, fl.Y + self.FallSpeed)
                    else:
                        fl.Y = max(fl.TargetY, fl.Y - self.FallSpeed)
                    fl.Rect.update(fl.X, fl.Y, s, s)
                else:
                    fl.Y = fl.TargetY
                    fl.Rect.update(fl.X, fl.Y, s, s)
        self.IsFalling = still_falling
                    
    def MoveFlowerPairAnim(self, flower1, flower2, target1_x, target1_y, target2_x, target2_y):
        s = self.FlowerSize
        speed = self.FlowerMatchSpeedAnim

        for fl, tx, ty in ((flower1, target1_x, target1_y), (flower2, target2_x, target2_y)):
            if abs(fl.X - tx) <= speed:
                fl.X = tx
            elif fl.X < tx:
                fl.X += speed
            else:
                fl.X -= speed

            if abs(fl.Y - ty) <= speed:
                fl.Y = ty
            elif fl.Y < ty:
                fl.Y += speed
            else:
                fl.Y -= speed

            fl.Rect.update(fl.X, fl.Y, s, s)
    
    def UpdateScore(self,name):
        self.UserScore += 100

    def DrawSpecialBadge(self, flower, draw_x, draw_y):
        if not flower.Special:
            return
        t = pygame.time.get_ticks() * 0.008
        cx = int(draw_x + self.FlowerSize * 0.5)
        cy = int(draw_y + self.FlowerSize * 0.5)
        badge = pygame.Surface((self.FlowerSize + 16, self.FlowerSize + 16), pygame.SRCALPHA)
        bcx = (self.FlowerSize + 16) // 2
        bcy = (self.FlowerSize + 16) // 2
        if flower.Special == "line":
            pygame.draw.circle(badge, (255, 240, 120, 190), (bcx, bcy), self.FlowerSize // 2 + 4, width=3)
            pygame.draw.line(badge, (255, 255, 200, 210), (4, bcy), (self.FlowerSize + 12, bcy), 3)
            pygame.draw.line(badge, (255, 255, 200, 210), (bcx, 4), (bcx, self.FlowerSize + 12), 3)
        elif flower.Special == "bomb":
            rad = int(self.FlowerSize // 2 + 3 + math.sin(t * 2.0) * 3)
            pygame.draw.circle(badge, (255, 110, 220, 210), (bcx, bcy), rad, width=4)
            pygame.draw.circle(badge, (120, 245, 255, 190), (bcx, bcy), rad - 5, width=2)
        elif flower.Special == "rainbow":
            for i in range(3):
                r = int(127 + 127 * math.sin(t + i * 2.0))
                g = int(127 + 127 * math.sin(t + i * 2.0 + 2.1))
                b = int(127 + 127 * math.sin(t + i * 2.0 + 4.2))
                pygame.draw.circle(badge, (r, g, b, 210), (bcx, bcy), self.FlowerSize // 2 + 6 - i * 3, width=2)
        self.CurrentScreen.blit(badge, (cx - bcx, cy - bcy))

    def DrawSelectedFlowerShader(self, flower, draw_x=None, draw_y=None):
        fx = flower.X if draw_x is None else draw_x
        fy = flower.Y if draw_y is None else draw_y
        t = pygame.time.get_ticks() * 0.008
        pulse = (math.sin(t) + 1.0) * 0.5

        mask = pygame.mask.from_surface(flower.Surf)
        w, h = flower.Surf.get_size()

        # Soft outer aura + glowing silhouette outline around the flower petals
        outer_alpha = int(60 + 50 * pulse)
        outer_glow = mask.to_surface(setcolor=(255, 230, 120, outer_alpha), unsetcolor=(0, 0, 0, 0))
        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
            self.CurrentScreen.blit(outer_glow, (fx + ox, fy + oy))

        inner_alpha = int(150 + 90 * pulse)
        inner_glow = mask.to_surface(setcolor=(255, 255, 200, inner_alpha), unsetcolor=(0, 0, 0, 0))
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            self.CurrentScreen.blit(inner_glow, (fx + ox, fy + oy))

        # Per-pixel additive brightness & sweeping shimmer shader on the flower surface
        shaded = flower.Surf.copy()
        boost = int(35 + 50 * pulse)
        shaded.fill((boost, boost, int(boost * 0.6), 0), special_flags=pygame.BLEND_RGB_ADD)

        # Diagonal sweeping sheen clipped to the flower mask
        sheen_pos = ((pygame.time.get_ticks() // 15) % (w + h + 20)) - 10
        sheen = pygame.Surface((w, h), pygame.SRCALPHA)
        for x in range(w):
            for y in range(h):
                if mask.get_at((x, y)):
                    dist = abs((x + y) - sheen_pos)
                    if dist < 6:
                        intensity = int((6 - dist) * 18)
                        sheen.set_at((x, y), (intensity, intensity, intensity, 0))
        shaded.blit(sheen, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.DrawSpecialBadge(flower, fx, fy)
        self.CurrentScreen.blit(shaded, (fx, fy))

    def DrawBoardBorderShader(self):
        board_w = self.BoardCol * self.CellSize
        board_h = self.BoardRow * self.CellSize
        bx = self.BoardStartX
        by = self.BoardStartY
        t = pygame.time.get_ticks() * 0.004

        # Semi-transparent shaded board backdrop & checkerboard tiles
        backdrop = pygame.Surface((board_w + 24, board_h + 24), pygame.SRCALPHA)
        pygame.draw.rect(backdrop, (20, 14, 48, 175), (0, 0, board_w + 24, board_h + 24), border_radius=16)
        for r in range(self.BoardRow):
            for c in range(self.BoardCol):
                cx = 12 + c * self.CellSize
                cy = 12 + r * self.CellSize
                tile_alpha = 70 if (r + c) % 2 == 0 else 40
                pygame.draw.rect(
                    backdrop,
                    (75, 55, 145, tile_alpha),
                    (cx + 2, cy + 2, self.CellSize - 4, self.CellSize - 4),
                    border_radius=10,
                )
        self.CurrentScreen.blit(backdrop, (bx - 12, by - 12))

        # Multi-layered animated shader glow border around the board
        glow_surf = pygame.Surface((board_w + 48, board_h + 48), pygame.SRCALPHA)
        pulse = (math.sin(t * 1.5) + 1.0) * 0.5
        for layer in range(6, 0, -1):
            spread = layer * 3
            r_col = int(130 + 95 * math.sin(t + layer * 0.3))
            g_col = int(90 + 80 * math.sin(t + 2.0 + layer * 0.3))
            b_col = int(220 + 35 * math.cos(t + layer * 0.2))
            alpha = int((28 + 20 * pulse) * (7 - layer) / 6)
            rect = pygame.Rect(
                12 - spread,
                12 - spread,
                board_w + 24 + spread * 2,
                board_h + 24 + spread * 2,
            )
            pygame.draw.rect(glow_surf, (r_col, g_col, b_col, alpha), rect, width=4, border_radius=16 + spread)

        # Bright inner core border
        core_r = int(190 + 65 * pulse)
        core_g = int(170 + 70 * pulse)
        pygame.draw.rect(
            glow_surf,
            (core_r, core_g, 255, 235),
            (12, 12, board_w + 24, board_h + 24),
            width=3,
            border_radius=16,
        )
        self.CurrentScreen.blit(glow_surf, (bx - 24, by - 24))

    def DrawEffects(self):
        # Burst particles
        if self.BurstParticles:
            p_surf = pygame.Surface((self.ScreenWidth, 720), pygame.SRCALPHA)
            alive = []
            for p in self.BurstParticles:
                px, py, vx, vy, radius, alpha, col = p
                px += vx
                py += vy
                vy += 0.22
                alpha -= 9
                if alpha > 0:
                    p[0], p[1], p[3], p[5] = px, py, vy, alpha
                    alive.append(p)
                    r, g, b = col
                    pygame.draw.circle(p_surf, (r, g, b, max(0, alpha // 2)), (int(px), int(py)), int(radius * 1.8))
                    pygame.draw.circle(p_surf, (r, g, b, max(0, alpha)), (int(px), int(py)), int(radius))
                    pygame.draw.circle(p_surf, (255, 255, 255, max(0, alpha)), (int(px), int(py)), max(1, int(radius * 0.4)))
            self.BurstParticles = alive
            self.CurrentScreen.blit(p_surf, (0, 0))

        # Floating score/combo/bonus popups
        if self.FloatingTexts:
            alive_texts = []
            for ft in self.FloatingTexts:
                text, fx, fy, alpha, color = ft
                fy -= 1.4
                alpha -= 5
                if alpha > 0:
                    ft[2], ft[3] = fy, alpha
                    alive_texts.append(ft)
                    surf = self.FontSmall.render(text, True, color)
                    surf.set_alpha(alpha)
                    glow = self.FontSmall.render(text, True, (60, 20, 120))
                    glow.set_alpha(alpha)
                    self.CurrentScreen.blit(glow, (int(fx) + 2, int(fy) + 2))
                    self.CurrentScreen.blit(surf, (int(fx), int(fy)))
            self.FloatingTexts = alive_texts

    def DrawBoard(self):
        self.DrawBoardBorderShader()
        selected_positions = set(self.FlowersSeletced)
        hint_positions = set(self.HintPair) if self.HintPair else set()
        t = pygame.time.get_ticks() * 0.015

        for r_idx, row in enumerate(self.Board):
            for c_idx, flower in enumerate(row):
                draw_x, draw_y = flower.X, flower.Y
                if (r_idx, c_idx) in hint_positions:
                    draw_x += math.sin(t) * 3.5
                    hint_ring = pygame.Surface((self.FlowerSize + 16, self.FlowerSize + 16), pygame.SRCALPHA)
                    pygame.draw.circle(
                        hint_ring,
                        (120, 255, 240, 180),
                        ((self.FlowerSize + 16) // 2, (self.FlowerSize + 16) // 2),
                        self.FlowerSize // 2 + 4,
                        width=3,
                    )
                    self.CurrentScreen.blit(hint_ring, (draw_x - 8, draw_y - 8))

                if (r_idx, c_idx) in selected_positions:
                    self.DrawSelectedFlowerShader(flower, draw_x, draw_y)
                else:
                    self.DrawSpecialBadge(flower, draw_x, draw_y)
                    self.CurrentScreen.blit(flower.Surf, (draw_x, draw_y))

        self.DrawEffects()

    def DrawHowToPlayModal(self):
        # Dim background overlay
        dim = pygame.Surface((self.ScreenWidth, 720), pygame.SRCALPHA)
        dim.fill((12, 6, 30, 185))
        self.CurrentScreen.blit(dim, (0, 0))

        mx, my = 180, 55
        mw, mh = 920, 610
        self.Shader.DrawGlowPanel(self.CurrentScreen, mx, my, mw, mh)

        self.Shader.DrawGlowText(
            self.CurrentScreen,
            self.FontBig,
            "How to Play Flowers",
            mx,
            my + 22,
            main_color=(255, 240, 160),
            offset=3,
            max_width=mw - 48,
            center_width=mw,
        )

        lines = [
            ("Goal:", "Match 3 or more flowers of the same color in a row or column!", (180, 245, 255)),
            ("8-Way Swap:", "Click 2 neighbors OR click & drag horizontally, vertically, or diagonally.", (245, 235, 255)),
            ("Sunburst (4-Match):", "Clears its entire row & column and awards +3s bonus time!", (255, 235, 140)),
            ("Rainbow (5-Match):", "Clears every flower of its color across the entire board!", (255, 195, 245)),
            ("Bloom Bomb (6+ / L-T):", "Blasts a 3x3 area of flowers around the bomb!", (160, 255, 210)),
            ("Combos & Levels:", "Chain cascades boost your multiplier (2x, 3x...). Level up for +25s!", (245, 235, 255)),
            ("Hints & Shuffle:", "Wait 6s for an auto-hint wiggle, or press [R] / Shuffle when stuck.", (220, 215, 255)),
        ]

        y_cursor = my + 110
        for heading, desc, col in lines:
            self.Shader.DrawGlowText(
                self.CurrentScreen,
                self.FontSmall,
                heading,
                mx + 38,
                y_cursor,
                main_color=col,
                offset=2,
                max_width=275,
            )
            self.Shader.DrawGlowText(
                self.CurrentScreen,
                self.FontTiny,
                desc,
                mx + 320,
                y_cursor + 6,
                main_color=(245, 240, 255),
                offset=1,
                max_width=mw - 350,
            )
            y_cursor += 58

        hovered = self.HowToPlayCloseRect.collidepoint(pygame.mouse.get_pos())
        self.Shader.DrawGlowPanel(
            self.CurrentScreen,
            self.HowToPlayCloseRect.x,
            self.HowToPlayCloseRect.y,
            self.HowToPlayCloseRect.width,
            self.HowToPlayCloseRect.height,
            hovered=hovered,
        )
        self.Shader.DrawGlowText(
            self.CurrentScreen,
            self.FontSmall,
            "Got It - Let's Play! (Click / Space)",
            self.HowToPlayCloseRect.x,
            self.HowToPlayCloseRect.y + 13,
            main_color=(255, 245, 190) if hovered else (245, 235, 255),
            offset=2,
            max_width=self.HowToPlayCloseRect.width - 28,
            center_width=self.HowToPlayCloseRect.width,
        )

    def Draw(self):
        self.CurrentScreen.blit(self.Background, (0,0))
        self.Shader.DrawAtmosphere(self.CurrentScreen)

        hud_x, hud_y, hud_w, hud_h = 875, 60, 355, 425
        pad_x = hud_x + 22
        inner_w = hud_w - 44

        # Main HUD panel
        self.Shader.DrawGlowPanel(self.CurrentScreen, hud_x, hud_y, hud_w, hud_h)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, f"Level {self.Level}", pad_x, 76, main_color=(180, 240, 255), offset=2, max_width=inner_w)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, "Score", pad_x, 122, offset=2, max_width=inner_w)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, f"{self.UserScore}", pad_x, 162, main_color=(255, 240, 170), offset=2, max_width=inner_w)

        # Level Progress Bar
        prev_target = (self.Level - 1) * 1500 if self.Level > 1 else 0
        span = max(1, self.LevelTarget - prev_target)
        prog = max(0.0, min(1.0, (self.UserScore - prev_target) / span))
        bar_x, bar_y, bar_w, bar_h = pad_x, 215, inner_w, 20
        pygame.draw.rect(self.CurrentScreen, (25, 15, 55), (bar_x, bar_y, bar_w, bar_h), border_radius=10)
        if prog > 0:
            pygame.draw.rect(self.CurrentScreen, (140, 235, 255), (bar_x, bar_y, int(bar_w * prog), bar_h), border_radius=10)
        pygame.draw.rect(self.CurrentScreen, (210, 180, 255), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=10)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontTiny, f"Next Level: {self.LevelTarget}", pad_x, 244, offset=1, max_width=inner_w)

        time_col = (255, 110, 110) if self.CurrentTime <= 10 else (245, 235, 255)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, f"Time: {self.CurrentTime}s", pad_x, 288, main_color=time_col, offset=2, max_width=inner_w)
        if self.ComboCount > 1:
            self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, f"Combo: {self.ComboCount}x!", pad_x, 336, main_color=(255, 220, 120), offset=2, max_width=inner_w)

        self.Shader.DrawGlowText(self.CurrentScreen, self.FontTiny, "8-Way & Drag Swap Enabled", pad_x, 392, main_color=(210, 210, 255), offset=1, max_width=inner_w)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontTiny, "4+: Line / Bomb / Rainbow", pad_x, 428, main_color=(210, 210, 255), offset=1, max_width=inner_w)

        # Interactive Shuffle button
        hovered_shuffle = self.ShuffleBtnRect.collidepoint(pygame.mouse.get_pos()) and self.ShufflesLeft > 0 and not self.ShowHowToPlay
        self.Shader.DrawGlowPanel(
            self.CurrentScreen,
            self.ShuffleBtnRect.x,
            self.ShuffleBtnRect.y,
            self.ShuffleBtnRect.width,
            self.ShuffleBtnRect.height,
            hovered=hovered_shuffle,
        )
        self.Shader.DrawGlowText(
            self.CurrentScreen,
            self.FontSmall,
            f"Shuffle ({self.ShufflesLeft}) [R]",
            self.ShuffleBtnRect.x,
            self.ShuffleBtnRect.y + 12,
            offset=2,
            max_width=self.ShuffleBtnRect.width - 28,
            center_width=self.ShuffleBtnRect.width,
        )

        # Interactive How to Play button
        hovered_help = self.HelpBtnRect.collidepoint(pygame.mouse.get_pos()) and not self.ShowHowToPlay
        self.Shader.DrawGlowPanel(
            self.CurrentScreen,
            self.HelpBtnRect.x,
            self.HelpBtnRect.y,
            self.HelpBtnRect.width,
            self.HelpBtnRect.height,
            hovered=hovered_help,
        )
        self.Shader.DrawGlowText(
            self.CurrentScreen,
            self.FontSmall,
            "How to Play [H]",
            self.HelpBtnRect.x,
            self.HelpBtnRect.y + 12,
            offset=2,
            max_width=self.HelpBtnRect.width - 28,
            center_width=self.HelpBtnRect.width,
        )
       
        self.DrawBoard()
        if self.ShowHowToPlay:
            self.DrawHowToPlayModal()
        pygame.display.update()

    def GetCellAtPos(self, x, y):
        for r_idx, _r in enumerate(self.Board):
            for c_idx, flowerObj in enumerate(_r):
                if flowerObj.Rect.collidepoint((x, y)):
                    return r_idx, c_idx
        return None, None

    def Update(self, fps):
        self.FPS = fps
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if self.ShowHowToPlay:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_h):
                    if self.Sound:
                        self.Sound.Play("select")
                    self.ShowHowToPlay = False
                    self.LastActionTime = pygame.time.get_ticks()
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.Sound:
                        self.Sound.Play("select")
                    self.ShowHowToPlay = False
                    self.LastActionTime = pygame.time.get_ticks()
                continue

            if event.type == pygame.USEREVENT:
                self.CurrentTime -= 1
                if 0 < self.CurrentTime <= 10 and self.Sound:
                    self.Sound.Play("tick")
                if self.CurrentTime <= 0:
                    self.ScreenNeedsToChange = True
                    self.ScreenToChangeToo = "EndScreen"
            if event.type == pygame.KEYDOWN and self.AnimData is None and not self.IsFalling:
                if event.key == pygame.K_r and self.ShufflesLeft > 0:
                    self.ShufflesLeft -= 1
                    self.ShuffleBoard()
                elif event.key == pygame.K_h:
                    if self.Sound:
                        self.Sound.Play("select")
                    self.ShowHowToPlay = True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.AnimData is None and not self.IsFalling:
                mx, my = event.pos
                if self.ShuffleBtnRect.collidepoint((mx, my)) and self.ShufflesLeft > 0:
                    self.ShufflesLeft -= 1
                    self.ShuffleBoard()
                elif self.HelpBtnRect.collidepoint((mx, my)):
                    if self.Sound:
                        self.Sound.Play("select")
                    self.ShowHowToPlay = True
                else:
                    r_click, c_click = self.GetCellAtPos(mx, my)
                    if r_click is not None:
                        self.DragStartCell = (r_click, c_click)

            if event.type == pygame.MOUSEMOTION and self.DragStartCell is not None and self.AnimData is None and not self.IsFalling:
                mx, my = event.pos
                r_cur, c_cur = self.GetCellAtPos(mx, my)
                if r_cur is not None and (r_cur, c_cur) != self.DragStartCell:
                    sr, sc = self.DragStartCell
                    if max(abs(r_cur - sr), abs(c_cur - sc)) == 1:
                        self.FlowersSeletced = [(sr, sc), (r_cur, c_cur)]
                        self.AnimData = self.CheckMove()
                        self.FlowersSeletced.clear()
                        self.DragStartCell = None

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.AnimData is None and not self.IsFalling and self.DragStartCell is not None:
                    mx, my = event.pos
                    RowNumberClick, ColNumberClick = self.GetCellAtPos(mx, my)
                    if RowNumberClick is not None and ColNumberClick is not None:
                        clicked_pos = (RowNumberClick, ColNumberClick)
                        if clicked_pos != self.DragStartCell and max(abs(clicked_pos[0] - self.DragStartCell[0]), abs(clicked_pos[1] - self.DragStartCell[1])) == 1:
                            self.FlowersSeletced = [self.DragStartCell, clicked_pos]
                            self.AnimData = self.CheckMove()
                            self.FlowersSeletced.clear()
                        elif len(self.FlowersSeletced) == 1 and self.FlowersSeletced[0] == clicked_pos:
                            self.FlowersSeletced.clear()
                        else:
                            if self.Sound:
                                self.Sound.Play("select")
                            self.FlowersSeletced.append(clicked_pos)
                            if len(self.FlowersSeletced) == 2:
                                self.AnimData = self.CheckMove()
                                if self.AnimData is None:
                                    self.FlowersSeletced = [clicked_pos]
                                else:
                                    self.FlowersSeletced.clear()
                self.DragStartCell = None

        if self.AnimData is not None:
            flower1, flower2, target1_x, target1_y, target2_x, target2_y = self.AnimData
            self.MoveFlowerPairAnim(flower1, flower2, target1_x, target1_y, target2_x, target2_y)
            if (
                abs(flower1.X - target1_x) < 0.5
                and abs(flower1.Y - target1_y) < 0.5
                and abs(flower2.X - target2_x) < 0.5
                and abs(flower2.Y - target2_y) < 0.5
            ):
                self.AnimData = None
        elif self.IsFalling:
            self.UpdateFallingFlowers()
        else:
            # check board for matches
            self.CheckBoard()
            self.DeleteAndReplaceFlowers()
            if not self.IsFalling and not self.ShowHowToPlay:
                now = pygame.time.get_ticks()
                if self.HintPair is None and now - self.LastActionTime > 6000:
                    self.HintPair = self.FindHintMove()
                    if self.HintPair is None:
                        self.ShuffleBoard()


class Flower(pygame.sprite.Sprite):
    def __init__(self, name, x, y, w=35, h=35):
        super(Flower,self).__init__()
        self.Surf = None
        self.X = float(x)
        self.Y = float(y)
        self.TargetX = float(x)
        self.TargetY = float(y)
        self.Rect = pygame.Rect(x,y,w,h)
        self.Name = name
        self.Special = None
        self.ID = random.randint(10000,10000000) # Not sure if i really need this.

    def SetSurf(self, img):
        self.Surf = img

    def SetXY(self,x,y):
        self.X = float(x)
        self.Y = float(y)
        self.TargetX = float(x)
        self.TargetY = float(y)
        self.Rect = pygame.Rect(x,y,self.Rect.width,self.Rect.height)

