from array import array
import json
import math
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ.setdefault("PULSE_PROP_application.name", "Flowers")
os.environ.setdefault("SDL_AUDIO_DEVICE_APP_NAME", "Flowers")
import pygame
import random
import sys
import webbrowser

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _SAVE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    os.chdir(sys._MEIPASS)
else:
    _SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(_SAVE_DIR)

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

            if self.GameMode == "MainMenu":
                self.Modes["MainMenu"].RefreshHighScores()

            if self.GameMode == "GameScreen":
                self.Modes["GameScreen"] = GameScreen(self.Screen, self.ScreenWidth, 0, self.Sound)
                pygame.event.clear(pygame.USEREVENT)
                pygame.time.set_timer(pygame.USEREVENT, 1000)

            if self.GameMode == "EndScreen":
                pygame.time.set_timer(pygame.USEREVENT, 0)
                self.Modes["GameScreen"].SaveCurrentScore()
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
            self.Sounds["select"] = self._make_tone([660], 0.065, 0.65)
            self.Sounds["swap"] = self._make_tone([440, 554], 0.06, 0.65)
            self.Sounds["shuffle"] = self._make_tone([330, 440, 554, 660], 0.055, 0.65)
            self.Sounds["tick"] = self._make_tone([880], 0.055, 0.55)
            self.Sounds["levelup"] = self._make_tone([523, 659, 784, 1046], 0.09, 0.75)
            self.Sounds["gameover"] = self._make_tone([659, 587, 523, 392], 0.12, 0.75)
            self.Sounds["zap"] = self._make_tone([1320, 988, 1568, 784, 1760], 0.05, 0.75)
            self.Sounds["rainbow"] = self._make_tone([523, 659, 784, 988, 1175, 1318, 1568], 0.05, 0.75)
            self.Sounds["bomb"] = self._make_bomb_sound(0.35, 0.85)
            for combo in range(1, 8):
                base = 440 * (1.12 ** (combo - 1))
                self.Sounds[f"match_{combo}"] = self._make_tone([base, base * 1.25, base * 1.5], 0.07, 0.72)
        except Exception:
            self.Enabled = False

    def _make_tone(self, freqs, duration_per_note, volume=0.65):
        init_info = pygame.mixer.get_init()
        sample_rate = init_info[0] if init_info else 44100
        channels = init_info[2] if init_info else 2
        buf = array("h")
        for freq in freqs:
            n_samples = int(sample_rate * duration_per_note)
            for i in range(n_samples):
                t = i / sample_rate
                env = (1.0 - (i / max(1, n_samples))) ** 0.8
                wave = 0.75 * math.sin(2.0 * math.pi * freq * t) + 0.25 * math.sin(4.0 * math.pi * freq * t)
                val = max(-32767, min(32767, int(32767 * volume * env * wave)))
                for _ in range(channels):
                    buf.append(val)
        snd = pygame.mixer.Sound(buffer=buf.tobytes())
        snd.set_volume(1.0)
        return snd

    def _make_bomb_sound(self, duration=0.32, volume=0.55):
        init_info = pygame.mixer.get_init()
        sample_rate = init_info[0] if init_info else 44100
        channels = init_info[2] if init_info else 2
        n_samples = int(sample_rate * duration)
        buf = array("h")
        rng = random.Random(42)
        for i in range(n_samples):
            t = i / sample_rate
            env = (1.0 - (i / max(1, n_samples))) ** 1.4
            # Pitch-dropping sub-bass boom + explosion crackle
            freq = 150.0 * ((1.0 - i / max(1, n_samples)) ** 0.7) + 38.0
            boom = math.sin(2.0 * math.pi * freq * t)
            noise = rng.uniform(-0.65, 0.65) * ((1.0 - i / max(1, n_samples)) ** 2.0)
            val = max(-32767, min(32767, int(32767 * volume * env * (0.72 * boom + 0.28 * noise))))
            for _ in range(channels):
                buf.append(val)
        snd = pygame.mixer.Sound(buffer=buf.tobytes())
        snd.set_volume(1.0)
        return snd

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
    FILE_PATH = os.path.join(_SAVE_DIR, "highscores.json")

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
    def SaveScoresList(cls, scores):
        scores = sorted([int(x) for x in scores if int(x) > 0], reverse=True)[:5]
        try:
            with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(scores, f)
        except Exception:
            pass
        return scores

    @classmethod
    def AddScore(cls, score):
        scores = cls.LoadScores()
        if int(score) > 0:
            scores.append(int(score))
        return cls.SaveScoresList(scores)


class ScreenShader(object):
    _PARALLAX_CACHE = None
    _PARALLAX_VIBRANT_CACHE = None
    _CLOUD_CACHE = None

    def __init__(self, width=1280, height=720):
        self.Width = width
        self.Height = height
        self._ensure_parallax_layers()
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

    @staticmethod
    def _scale_cloud(surf, factor=0.6):
        w = max(1, int(surf.get_width() * factor))
        h = max(1, int(surf.get_height() * factor))
        return pygame.transform.smoothscale(surf, (w, h))

    @staticmethod
    def _mute_surface(surf):
        muted = surf.copy()
        gray = pygame.transform.grayscale(muted)
        muted.fill((105, 105, 105, 255), special_flags=pygame.BLEND_RGBA_MULT)
        gray.fill((88, 88, 88, 255), special_flags=pygame.BLEND_RGBA_MULT)
        muted.blit(gray, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        return muted

    @classmethod
    def _ensure_parallax_layers(cls):
        if cls._PARALLAX_CACHE is not None:
            return
        target_size = (1360, 765)
        layers_muted = []
        layers_vibrant = []
        paths = [
            ("imgs/bg-layer1.jpeg", False),
            ("imgs/bg-layer2.jpeg", True),
            ("imgs/bg-layer3.jpeg", True),
        ]
        for path, key_white in paths:
            if not os.path.exists(path):
                continue
            raw_surf = pygame.image.load(path).convert_alpha()
            if key_white:
                keyed = pygame.Surface(raw_surf.get_size(), pygame.SRCALPHA)
                keyed.fill((0, 0, 0, 0))
                pygame.transform.threshold(
                    dest_surface=keyed,
                    surface=raw_surf,
                    search_color=(255, 255, 255, 255),
                    threshold=(22, 22, 26, 255),
                    set_color=None,
                    set_behavior=2,
                    inverse_set=False,
                )
                raw_surf = keyed
            scaled = pygame.transform.smoothscale(raw_surf, target_size)
            layers_vibrant.append(scaled)
            layers_muted.append(cls._mute_surface(scaled))
        cls._PARALLAX_VIBRANT_CACHE = layers_vibrant
        cls._PARALLAX_CACHE = layers_muted

        clouds = []
        for cpath in ("imgs/N-Cloud-1.png", "imgs/N-Cloud-2.png", "imgs/N-Cloud-3.png"):
            if os.path.exists(cpath):
                csurf = cls._scale_cloud(pygame.image.load(cpath).convert_alpha(), 0.6)
                muted_cloud = cls._mute_surface(csurf)
                muted_cloud.set_alpha(232)
                clouds.append(muted_cloud)
        cls._CLOUD_CACHE = clouds

    def DrawParallaxBackground(self, screen, clouds=None, muted=True):
        layer_list = self._PARALLAX_CACHE if muted else self._PARALLAX_VIBRANT_CACHE
        if not layer_list:
            return
        ticks = pygame.time.get_ticks()
        t = ticks * 0.0012
        mx, my = pygame.mouse.get_pos()
        norm_x = (mx - self.Width * 0.5) / (self.Width * 0.5)
        norm_y = (my - self.Height * 0.5) / (self.Height * 0.5)

        drift_x = math.sin(t) * 18.0
        drift_y = math.cos(t * 0.8) * 8.0

        if clouds is None and self._CLOUD_CACHE:
            sec = ticks * 0.06
            base_specs = [
                (40.0, 22.0, 0.42, 420.0, 0.0),
                (460.0, 135.0, 0.19, 260.0, 2.1),
                (940.0, 72.0, 0.30, 320.0, 4.2),
            ]
            clouds = []
            for idx_c, csurf in enumerate(self._CLOUD_CACHE):
                bx, by, spd, pad, phase = base_specs[min(idx_c, len(base_specs) - 1)]
                span = 1380.0 + pad
                breeze = math.sin(t * 0.55 + phase) * 18.0
                cx = ((bx + sec * spd + breeze + pad) % span) - pad
                cy = by + math.sin(t * 0.85 + phase) * 5.0
                clouds.append((csurf, (cx, cy)))

        cloud_parallax = [(0.38, 0.28), (0.24, 0.18), (0.31, 0.23)]
        parallax_factors = [(0.2, 0.15), (0.55, 0.4), (1.0, 0.75)]
        for idx, layer_surf in enumerate(layer_list):
            fx, fy = parallax_factors[min(idx, len(parallax_factors) - 1)]
            ox = int(-40 - (norm_x * 22.0 + drift_x) * fx)
            oy = int(-22 - (norm_y * 14.0 + drift_y) * fy)
            screen.blit(layer_surf, (ox, oy))
            if idx == 0 and clouds:
                for c_idx, (cloud_surf, cloud_xy) in enumerate(clouds):
                    cfx, cfy = cloud_parallax[min(c_idx, len(cloud_parallax) - 1)]
                    cox = int(cloud_xy[0] - (norm_x * 22.0 + drift_x) * cfx)
                    coy = int(cloud_xy[1] - (norm_y * 14.0 + drift_y) * cfy)
                    screen.blit(cloud_surf, (cox, coy))

        if muted:
            if not hasattr(self, "_mute_overlay") or self._mute_overlay.get_size() != (self.Width, self.Height):
                self._mute_overlay = pygame.Surface((self.Width, self.Height), pygame.SRCALPHA)
                self._mute_overlay.fill((24, 28, 42, 46))
            screen.blit(self._mute_overlay, (0, 0))

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
    TITLE_PALETTE = [
        ((245, 235, 255), (95, 45, 190)),
        ((255, 235, 130), (195, 95, 20)),
        ((140, 245, 255), (25, 105, 195)),
        ((255, 155, 220), (175, 30, 120)),
        ((155, 255, 175), (25, 145, 65)),
        ((255, 165, 135), (185, 45, 30)),
    ]

    def __init__(self, screen, sWidth, sound=None):
        self.CurrentScreen = screen
        self.ScreenWidth = sWidth
        self.Sound = sound
        self.Background = None
        self.ScreenNeedsToChange = False
        self.ScreenToChangeToo = ""
        self.TextColor = 110, 68, 255
        self.Cloud1XY = (float(40), float(22))
        self.Cloud2XY = (float(460), float(135))
        self.Cloud3XY = (float(940), float(72))
        self.CloudSpeed = float(0.42)
        self.TitleColorIndex = 0
        self.TitleRect = pygame.Rect(440, 20, 400, 105)
        self.TitleClickTimes = list()
        self.ShowCreditsModal = False
        self.CreditsUrlRect = pygame.Rect(440, 355, 400, 42)
        self.HighScores = HighScoreManager.LoadScores()
        self.Shader = ScreenShader(sWidth, 720)
        self.Load()

    def RefreshHighScores(self):
        self.HighScores = HighScoreManager.LoadScores()
        

    def Load(self):
        self.cloud1 = ScreenShader._scale_cloud(pygame.image.load("imgs/N-Cloud-1.png").convert_alpha(), 0.6)
        self.cloud2 = ScreenShader._scale_cloud(pygame.image.load("imgs/N-Cloud-2.png").convert_alpha(), 0.6)
        self.cloud3 = ScreenShader._scale_cloud(pygame.image.load("imgs/N-Cloud-3.png").convert_alpha(), 0.6)
        self.cloud1.set_alpha(232)
        self.cloud2.set_alpha(222)
        self.cloud3.set_alpha(228)
        font_path = "fonts/GameFont.ttf"
        self.FontBig = pygame.font.Font(font_path, 92)
        self.FontSmall = pygame.font.Font(font_path, 36)
        self.FontSub = pygame.font.Font(font_path, 27)
        self.GameNameWidth = (self.ScreenWidth / 2) - 240
    
    def ClearScreen(self):
        black = 0, 0, 0
        self.CurrentScreen.fill(black)

    def DrawMenuShader(self):
        t = pygame.time.get_ticks() * 0.003
        self.Shader.DrawAtmosphere(self.CurrentScreen)

        # Glowing shader title & subtitle
        title_str = "Flowers"
        main_col, glow_col = self.TITLE_PALETTE[self.TitleColorIndex]
        title_surf = self.FontBig.render(title_str, True, main_col)
        tx = int((self.ScreenWidth - title_surf.get_width()) / 2)
        ty = int(20 + math.sin(t * 1.6) * 6)
        self.TitleRect = pygame.Rect(tx - 12, ty - 6, title_surf.get_width() + 24, title_surf.get_height() + 12)
        self.Shader.DrawGlowText(
            self.CurrentScreen,
            self.FontBig,
            title_str,
            tx,
            ty,
            main_color=main_col,
            glow_color=glow_col,
            offset=4,
        )

        sub_str = "Swap blooms in 8 directions, trigger cascading combos & race the clock!"
        sub_surf = self.FontSub.render(sub_str, True, (255, 240, 175))
        sw = min(1120, sub_surf.get_width() + 48)
        sh = sub_surf.get_height() + 20
        sx = int((self.ScreenWidth - sw) / 2)
        sy = int(135 + math.sin(t * 1.6) * 4)
        self.Shader.DrawGlowPanel(self.CurrentScreen, sx, sy, sw, sh)
        self.Shader.DrawGlowText(
            self.CurrentScreen,
            self.FontSub,
            sub_str,
            sx,
            sy + 10,
            main_color=(255, 245, 190),
            offset=2,
            max_width=sw - 32,
            center_width=sw,
        )

        # Top 3 High Scores panel on Main Menu
        hs_w, hs_h = 430, 215
        hs_x = int((self.ScreenWidth - hs_w) / 2)
        hs_y = 285
        self.Shader.DrawGlowPanel(self.CurrentScreen, hs_x, hs_y, hs_w, hs_h)
        self.Shader.DrawGlowText(
            self.CurrentScreen,
            self.FontSmall,
            "Top 3 High Scores",
            hs_x,
            hs_y + 14,
            main_color=(255, 235, 150),
            offset=2,
            max_width=hs_w - 32,
            center_width=hs_w,
        )
        medal_colors = [(255, 235, 130), (225, 235, 255), (255, 195, 150)]
        for idx in range(3):
            score_txt = f"{self.HighScores[idx]} pts" if idx < len(self.HighScores) else "---"
            self.Shader.DrawGlowText(
                self.CurrentScreen,
                self.FontSub,
                f"#{idx + 1}    {score_txt}",
                hs_x,
                hs_y + 72 + idx * 44,
                main_color=medal_colors[idx],
                offset=2,
                max_width=hs_w - 32,
                center_width=hs_w,
            )

        # Start button with hover & pulsing neon border shader
        start_str = "Click or press space to start!"
        start_surf = self.FontSmall.render(start_str, True, (250, 245, 255))
        bw = start_surf.get_width() + 56
        bh = start_surf.get_height() + 28
        bx = int((self.ScreenWidth - bw) / 2)
        by = 615
        btn_rect = pygame.Rect(bx, by, bw, bh)
        hovered = btn_rect.collidepoint(pygame.mouse.get_pos()) and not self.ShowCreditsModal

        self.Shader.DrawGlowPanel(self.CurrentScreen, bx, by, bw, bh, hovered=hovered)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, start_str, bx + 28, by + 14, offset=2)

        if self.ShowCreditsModal:
            dim = pygame.Surface((self.ScreenWidth, 720), pygame.SRCALPHA)
            dim.fill((12, 6, 30, 185))
            self.CurrentScreen.blit(dim, (0, 0))
            mw, mh = 680, 330
            mx = int((self.ScreenWidth - mw) / 2)
            my = int((720 - mh) / 2)
            self.Shader.DrawGlowPanel(self.CurrentScreen, mx, my, mw, mh, hovered=True)
            self.Shader.DrawGlowText(
                self.CurrentScreen,
                self.FontBig,
                "Made by Frank Mulvie",
                mx,
                my + 30,
                main_color=(255, 240, 150),
                offset=3,
                max_width=mw - 48,
                center_width=mw,
            )
            self.Shader.DrawGlowText(
                self.CurrentScreen,
                self.FontSmall,
                "Version 1.0.0",
                mx,
                my + 125,
                main_color=(180, 240, 255),
                offset=2,
                max_width=mw - 48,
                center_width=mw,
            )
            self.CreditsUrlRect = pygame.Rect(mx + 120, my + 180, mw - 240, 44)
            url_hovered = self.CreditsUrlRect.collidepoint(pygame.mouse.get_pos())
            self.Shader.DrawGlowText(
                self.CurrentScreen,
                self.FontSmall,
                "https://knrf.itch.io/",
                mx,
                my + 185,
                main_color=(255, 235, 140) if url_hovered else (255, 185, 245),
                offset=2,
                max_width=mw - 48,
                center_width=mw,
            )
            self.Shader.DrawGlowText(
                self.CurrentScreen,
                self.FontSub,
                "Click anywhere or press Space to close",
                mx,
                my + 255,
                main_color=(230, 225, 255),
                offset=2,
                max_width=mw - 48,
                center_width=mw,
            )

    def Draw(self):
        self.Shader.DrawParallaxBackground(
            self.CurrentScreen,
            clouds=[
                (self.cloud1, self.Cloud1XY),
                (self.cloud2, self.Cloud2XY),
                (self.cloud3, self.Cloud3XY),
            ],
            muted=False,
        )

        self.DrawMenuShader()
        pygame.display.update()

    def UpdateClouds(self):
        t = pygame.time.get_ticks() * 0.0012
        a, _b = self.Cloud1XY
        a = a + 0.42 + math.sin(t * 0.55) * 0.08
        if a > 1380:
            a = float(-420)
        self.Cloud1XY = (a, 22.0 + math.sin(t * 0.85) * 5.0)

        a, _b = self.Cloud2XY
        a = a + 0.19 + math.sin(t * 0.55 + 2.1) * 0.05
        if a > 1380:
            a = float(-260)
        self.Cloud2XY = (a, 135.0 + math.sin(t * 0.85 + 2.1) * 3.5)

        a, _b = self.Cloud3XY
        a = a + 0.30 + math.sin(t * 0.55 + 4.2) * 0.06
        if a > 1380:
            a = float(-320)
        self.Cloud3XY = (a, 72.0 + math.sin(t * 0.85 + 4.2) * 4.5)

    def Update(self,fps):
        self.UpdateClouds()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()

            if self.ShowCreditsModal:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    if self.Sound:
                        self.Sound.Play("select")
                    self.ShowCreditsModal = False
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.Sound:
                        self.Sound.Play("select")
                    if self.CreditsUrlRect.collidepoint(event.pos):
                        webbrowser.open("https://knrf.itch.io/")
                    else:
                        self.ShowCreditsModal = False
                continue
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    #print("Space")
                    if self.Sound:
                        self.Sound.Play("select")
                    self.ScreenNeedsToChange = True
                    self.ScreenToChangeToo = "GameScreen"

            if event.type == pygame.MOUSEBUTTONUP:
                if self.TitleRect.collidepoint(event.pos):
                    self.TitleColorIndex = (self.TitleColorIndex + 1) % len(self.TITLE_PALETTE)
                    now = pygame.time.get_ticks()
                    self.TitleClickTimes = [ts for ts in self.TitleClickTimes if now - ts <= 30000]
                    self.TitleClickTimes.append(now)
                    if len(self.TitleClickTimes) >= 10:
                        self.ShowCreditsModal = True
                        self.TitleClickTimes.clear()
                        if self.Sound:
                            self.Sound.Play("levelup")
                    elif self.Sound:
                        self.Sound.Play("select")
                else:
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
        self.Cloud1XY = (float(40), float(22))
        self.Cloud2XY = (float(460), float(135))
        self.Cloud3XY = (float(940), float(72))
        self.Shader = ScreenShader(sWidth, 720)
        self.Load()

    def SetFinalScore(self, score):
        self.UserScore = score
        self.HighScores = HighScoreManager.LoadScores()

    def Load(self):
        self.cloud1 = ScreenShader._scale_cloud(pygame.image.load("imgs/N-Cloud-1.png").convert_alpha(), 0.6)
        self.cloud2 = ScreenShader._scale_cloud(pygame.image.load("imgs/N-Cloud-2.png").convert_alpha(), 0.6)
        self.cloud3 = ScreenShader._scale_cloud(pygame.image.load("imgs/N-Cloud-3.png").convert_alpha(), 0.6)
        self.cloud1.set_alpha(232)
        self.cloud2.set_alpha(222)
        self.cloud3.set_alpha(228)
        font_path = "fonts/GameFont.ttf"
        self.FontBig = pygame.font.Font(font_path, 72)
        self.FontSmall = pygame.font.Font(font_path, 34)
        self.FontTiny = pygame.font.Font(font_path, 26)
        self.GameNameWidth = (self.ScreenWidth / 2) - 240
    
    def ClearScreen(self):
        black = 0, 0, 0
        self.CurrentScreen.fill(black)

    def UpdateClouds(self):
        t = pygame.time.get_ticks() * 0.0012
        a, _b = self.Cloud1XY
        a = a + 0.42 + math.sin(t * 0.55) * 0.08
        if a > 1380:
            a = float(-420)
        self.Cloud1XY = (a, 22.0 + math.sin(t * 0.85) * 5.0)

        a, _b = self.Cloud2XY
        a = a + 0.19 + math.sin(t * 0.55 + 2.1) * 0.05
        if a > 1380:
            a = float(-260)
        self.Cloud2XY = (a, 135.0 + math.sin(t * 0.85 + 2.1) * 3.5)

        a, _b = self.Cloud3XY
        a = a + 0.30 + math.sin(t * 0.55 + 4.2) * 0.06
        if a > 1380:
            a = float(-320)
        self.Cloud3XY = (a, 72.0 + math.sin(t * 0.85 + 4.2) * 4.5)

    def Draw(self):
        t = pygame.time.get_ticks() * 0.003
        msg1_str = f"Your Score: {self.UserScore}"
        msg2_str = "Press ESC to quit or Click / Space to play again"
        msg1_surf = self.FontBig.render(msg1_str, True, (245, 235, 255))
        msg2_surf = self.FontSmall.render(msg2_str, True, (245, 235, 255))

        self.ClearScreen()
        self.Shader.DrawParallaxBackground(
            self.CurrentScreen,
            clouds=[
                (self.cloud1, self.Cloud1XY),
                (self.cloud2, self.Cloud2XY),
                (self.cloud3, self.Cloud3XY),
            ],
            muted=False,
        )
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
       self.UpdateClouds()
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
        "orange": (255, 145, 95),
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
        self.PreviousHighScores = HighScoreManager.LoadScores()
        self.BestScore = self.PreviousHighScores[0] if self.PreviousHighScores else 0
        self.ShufflesLeft = 3
        self.ShuffleBtnRect = pygame.Rect(875, 515, 355, 58)
        self.HelpBtnRect = pygame.Rect(875, 595, 355, 58)
        self.ShowHowToPlay = True
        self.HowToPlayCloseRect = pygame.Rect(410, 580, 460, 62)
        self.FloatingTexts = list()
        self.BurstParticles = list()
        self.SpecialEffects = list()
        self.ScreenShake = 0.0
        self.DragStartCell = None
        self.LastActionTime = pygame.time.get_ticks()
        self.HintPair = None
        self.IsTimeOver = False
        self.TimeOverStart = 0
        self.TimeOverFlowers = list()
        self.FPS = 0
        self.Shader = ScreenShader(sWidth, 720)
        self.Load()
        
    @staticmethod
    def _extract_sheet_flower(sheet, region_rect, target_size):
        sub = sheet.subsurface(region_rect)
        bb = sub.get_bounding_rect()
        if bb.width <= 0 or bb.height <= 0:
            return pygame.transform.smoothscale(sub, target_size)
        cropped = sub.subsurface(bb)
        side = max(bb.width, bb.height)
        square = pygame.Surface((side, side), pygame.SRCALPHA)
        square.blit(cropped, ((side - bb.width) // 2, (side - bb.height) // 2))
        return pygame.transform.smoothscale(square, target_size)

    def Load(self):
        size = (self.FlowerSize, self.FlowerSize)
        sheet = pygame.image.load("imgs/flower-sheet.png").convert_alpha()
        self.BFlower = self._extract_sheet_flower(sheet, (0, 0, 341, 350), size)
        self.GFlower = self._extract_sheet_flower(sheet, (341, 0, 341, 350), size)
        self.PFlower = self._extract_sheet_flower(sheet, (682, 0, 342, 350), size)
        self.RFlower = self._extract_sheet_flower(sheet, (0, 350, 341, 350), size)
        self.YFlower = self._extract_sheet_flower(sheet, (341, 350, 341, 350), size)
        self.OFlower = self._extract_sheet_flower(sheet, (682, 350, 342, 350), size)
        bomb_sheet = pygame.image.load("imgs/flower-bombs.png").convert_alpha()
        self.BFlowerBomb = self._extract_sheet_flower(bomb_sheet, (0, 0, 341, 350), size)
        self.GFlowerBomb = self._extract_sheet_flower(bomb_sheet, (341, 0, 341, 350), size)
        self.PFlowerBomb = self._extract_sheet_flower(bomb_sheet, (682, 0, 342, 350), size)
        self.RFlowerBomb = self._extract_sheet_flower(bomb_sheet, (0, 350, 341, 350), size)
        self.YFlowerBomb = self._extract_sheet_flower(bomb_sheet, (341, 350, 341, 350), size)
        self.OFlowerBomb = self._extract_sheet_flower(bomb_sheet, (682, 350, 342, 350), size)
        zap_sheet = pygame.image.load("imgs/flower-zap.png").convert_alpha()
        self.BFlowerZap = self._extract_sheet_flower(zap_sheet, (0, 0, 341, 350), size)
        self.GFlowerZap = self._extract_sheet_flower(zap_sheet, (341, 0, 341, 350), size)
        self.PFlowerZap = self._extract_sheet_flower(zap_sheet, (682, 0, 342, 350), size)
        self.RFlowerZap = self._extract_sheet_flower(zap_sheet, (0, 350, 341, 350), size)
        self.YFlowerZap = self._extract_sheet_flower(zap_sheet, (341, 350, 341, 350), size)
        self.OFlowerZap = self._extract_sheet_flower(zap_sheet, (682, 350, 342, 350), size)
        font_path = "fonts/GameFont.ttf"
        self.FontTimeOver = pygame.font.Font(font_path, 84)
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
        num = random.randint(0, 5)
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
        if num == 5:
            sprite = Flower("orange", x, y, self.FlowerSize, self.FlowerSize)
            img = self.OFlower

        sprite.Special = special
        sprite.SetSurf(self.GetFlowerSurfByName(sprite.Name, special))
        return sprite

    def GetFlowerSurfByName(self, name, special=None):
        if special == "bomb":
            return {
                "red": self.RFlowerBomb,
                "blue": self.BFlowerBomb,
                "green": self.GFlowerBomb,
                "purple": self.PFlowerBomb,
                "yellow": self.YFlowerBomb,
                "orange": self.OFlowerBomb,
            }[name]
        if special in ("zap", "line"):
            return {
                "red": self.RFlowerZap,
                "blue": self.BFlowerZap,
                "green": self.GFlowerZap,
                "purple": self.PFlowerZap,
                "yellow": self.YFlowerZap,
                "orange": self.OFlowerZap,
            }[name]
        return {
            "red": self.RFlower,
            "blue": self.BFlower,
            "green": self.GFlower,
            "purple": self.PFlower,
            "yellow": self.YFlower,
            "orange": self.OFlower,
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

    def SaveCurrentScore(self):
        if self.UserScore > 0:
            updated = HighScoreManager.SaveScoresList(self.PreviousHighScores + [self.UserScore])
            if updated:
                self.BestScore = updated[0]

    def AddFloatingText(self, text, x, y, color=(255, 245, 160)):
        w, h = self.FontSmall.size(text)
        min_x = float(self.BoardStartX + 6)
        max_x = float(self.BoardStartX + self.BoardCol * self.CellSize - w - 6)
        fx = max(min_x, min(float(x), max_x))
        fy = float(y)
        pad_x, pad_y = 14, 8

        # Push new popup vertically so its bounding box never overlaps any existing popup
        for _ in range(len(self.FloatingTexts) + 2):
            my_rect = pygame.Rect(int(fx) - pad_x // 2, int(fy) - pad_y // 2, w + pad_x, h + pad_y)
            collided = False
            for other in self.FloatingTexts:
                o_text, ox, oy, _o_alpha, _o_col = other
                ow, oh = self.FontSmall.size(o_text)
                o_rect = pygame.Rect(int(ox) - pad_x // 2, int(oy) - pad_y // 2, ow + pad_x, oh + pad_y)
                if my_rect.colliderect(o_rect):
                    fy = float(o_rect.top - h - pad_y)
                    collided = True
                    break
            if not collided:
                break

        if fy < 16.0:
            # If stacked above the top of the screen, place below the lowest colliding popup instead
            fy = float(y)
            for _ in range(len(self.FloatingTexts) + 2):
                my_rect = pygame.Rect(int(fx) - pad_x // 2, int(fy) - pad_y // 2, w + pad_x, h + pad_y)
                collided = False
                for other in self.FloatingTexts:
                    o_text, ox, oy, _o_alpha, _o_col = other
                    ow, oh = self.FontSmall.size(o_text)
                    o_rect = pygame.Rect(int(ox) - pad_x // 2, int(oy) - pad_y // 2, ow + pad_x, oh + pad_y)
                    if my_rect.colliderect(o_rect):
                        fy = float(o_rect.bottom + pad_y)
                        collided = True
                        break
                if not collided:
                    break

        self.FloatingTexts.append([text, fx, fy, 380.0, color])

    def SpawnZapShader(self, r, c):
        if self.Sound:
            self.Sound.Play("zap")
        fx, fy = self.CellToXY(r, c)
        cx = fx + self.FlowerSize * 0.5
        cy = fy + self.FlowerSize * 0.5
        self.SpecialEffects.append({
            "type": "zap",
            "r": r,
            "c": c,
            "cx": cx,
            "cy": cy,
            "timer": 0,
            "max_timer": 24,
        })
        # Electric sparks shooting along the row and column
        for _ in range(28):
            if random.random() < 0.5:
                px = random.uniform(self.BoardStartX, self.BoardStartX + self.BoardCol * self.CellSize)
                py = cy + random.uniform(-10, 10)
                vx = random.choice([-1, 1]) * random.uniform(3.0, 9.0)
                vy = random.uniform(-2.2, 2.2)
            else:
                px = cx + random.uniform(-10, 10)
                py = random.uniform(self.BoardStartY, self.BoardStartY + self.BoardRow * self.CellSize)
                vx = random.uniform(-2.2, 2.2)
                vy = random.choice([-1, 1]) * random.uniform(3.0, 9.0)
            col = random.choice([(255, 250, 110), (130, 245, 255), (255, 255, 230)])
            self.BurstParticles.append([px, py, vx, vy, random.uniform(3.5, 6.5), 255, col])

    def SpawnRainbowShader(self, r, c, target_cells):
        if self.Sound:
            self.Sound.Play("rainbow")
        fx, fy = self.CellToXY(r, c)
        cx = fx + self.FlowerSize * 0.5
        cy = fy + self.FlowerSize * 0.5
        targets = []
        rainbow_cols = [
            (255, 95, 120),
            (255, 175, 85),
            (255, 240, 100),
            (110, 245, 150),
            (95, 220, 255),
            (175, 130, 255),
            (255, 120, 225),
        ]
        for tr, tc in target_cells:
            tx, ty = self.CellToXY(tr, tc)
            tcx = tx + self.FlowerSize * 0.5
            tcy = ty + self.FlowerSize * 0.5
            targets.append((tcx, tcy))
            for _ in range(8):
                ang = random.uniform(0, math.pi * 2)
                spd = random.uniform(2.5, 7.0)
                self.BurstParticles.append([
                    tcx,
                    tcy,
                    math.cos(ang) * spd,
                    math.sin(ang) * spd - 1.2,
                    random.uniform(4.5, 8.0),
                    255,
                    random.choice(rainbow_cols),
                ])
        self.SpecialEffects.append({
            "type": "rainbow",
            "cx": cx,
            "cy": cy,
            "targets": targets,
            "timer": 0,
            "max_timer": 30,
        })

    def SpawnBombShader(self, r, c, r0, c0):
        if self.Sound:
            self.Sound.Play("bomb")
        fx, fy = self.CellToXY(r, c)
        cx = fx + self.FlowerSize * 0.5
        cy = fy + self.FlowerSize * 0.5
        bx = self.BoardStartX + c0 * self.CellSize
        by = self.BoardStartY + r0 * self.CellSize
        bw = min(5, self.BoardCol - c0) * self.CellSize
        bh = min(5, self.BoardRow - r0) * self.CellSize
        self.ScreenShake = max(self.ScreenShake, 10.0)
        self.SpecialEffects.append({
            "type": "bomb",
            "cx": cx,
            "cy": cy,
            "rect": (bx, by, bw, bh),
            "timer": 0,
            "max_timer": 28,
        })
        fire_cols = [(255, 120, 60), (255, 210, 80), (255, 90, 185), (255, 245, 200)]
        for _ in range(42):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(3.0, 11.5)
            self.BurstParticles.append([
                cx + random.uniform(-18, 18),
                cy + random.uniform(-18, 18),
                math.cos(ang) * spd,
                math.sin(ang) * spd - 1.5,
                random.uniform(5.5, 10.5),
                255,
                random.choice(fire_cols),
            ])

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
        for r, c in ordered_positions:
            fl = self.Board[r][c]
            if fl is None:
                continue
            if fl.Special in ("zap", "line"):
                if not instant and self.UserFirstMove:
                    self.SpawnZapShader(r, c)
                for cc in range(self.BoardCol):
                    if (r, cc) not in expanded_set:
                        expanded_set.add((r, cc))
                        expanded.append((r, cc))
                for rr in range(self.BoardRow):
                    if (rr, c) not in expanded_set:
                        expanded_set.add((rr, c))
                        expanded.append((rr, c))
            elif fl.Special == "bomb":
                r0 = max(0, min(self.BoardRow - 5, r - 2))
                c0 = max(0, min(self.BoardCol - 5, c - 2))
                if not instant and self.UserFirstMove:
                    self.SpawnBombShader(r, c, r0, c0)
                for rr in range(r0, min(self.BoardRow, r0 + 5)):
                    for cc in range(c0, min(self.BoardCol, c0 + 5)):
                        if (rr, cc) not in expanded_set:
                            expanded_set.add((rr, cc))
                            expanded.append((rr, cc))
            elif fl.Special == "rainbow":
                target_color = fl.Name
                rainbow_targets = []
                for rr in range(self.BoardRow):
                    for cc in range(self.BoardCol):
                        if self.Board[rr][cc].Name == target_color:
                            rainbow_targets.append((rr, cc))
                            if (rr, cc) not in expanded_set:
                                expanded_set.add((rr, cc))
                                expanded.append((rr, cc))
                if not instant and self.UserFirstMove:
                    self.SpawnRainbowShader(r, c, rainbow_targets)

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
            spawn_special = "zap"

        if self.UserFirstMove:
            self.ComboCount += 1
            if self.Sound:
                self.Sound.PlayMatch(self.ComboCount)

            points_earned = len(expanded) * 100 * self.ComboCount
            self.UserScore += points_earned
            self.SaveCurrentScore()

            avg_x = sum(self.Board[r][c].X for r, c in expanded) / len(expanded)
            avg_y = sum(self.Board[r][c].Y for r, c in expanded) / len(expanded)
            label = f"+{points_earned}" if self.ComboCount == 1 else f"+{points_earned} ({self.ComboCount}x COMBO!)"
            self.AddFloatingText(label, avg_x, avg_y, (255, 245, 140))

            MAX_TIME = 3599  # 59:59 maximum timer cap

            if len(ordered_positions) >= 5 and self.CurrentTime < MAX_TIME:
                added_bonus = min(3, MAX_TIME - self.CurrentTime)
                self.CurrentTime += added_bonus
                self.AddFloatingText(f"+{added_bonus}s TIME BONUS!", avg_x, avg_y - 32, (150, 255, 190))

            if self.UserScore >= self.LevelTarget:
                self.Level += 1
                self.LevelTarget += self.Level * 1800
                added_lvl = max(0, min(15, MAX_TIME - self.CurrentTime))
                self.CurrentTime += added_lvl
                self.ShufflesLeft = min(5, self.ShufflesLeft + 1)
                if self.Sound:
                    self.Sound.Play("levelup")
                lvl_msg = f"LEVEL {self.Level}! +{added_lvl}s" if added_lvl > 0 else f"LEVEL {self.Level}!"
                self.AddFloatingText(lvl_msg, 380, 300, (255, 210, 255))

        for r, c in expanded:
            fl = self.Board[r][c]
            if self.UserFirstMove:
                self.SpawnBurst(fl.X, fl.Y, fl.Name)
            self.Board[r][c] = None

        if self.UserFirstMove and spawn_special is not None:
            sr, sc = spawn_pos
            tx, ty = self.CellToXY(sr, sc)
            special_flower = Flower(spawn_color, tx, ty, self.FlowerSize, self.FlowerSize)
            special_flower.Special = spawn_special
            special_flower.SetSurf(self.GetFlowerSurfByName(spawn_color, spawn_special))
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
        self.HintPair = None
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
        self.LastActionTime = pygame.time.get_ticks()
                    
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
        if not flower.Special or flower.Special in ("bomb", "zap", "line"):
            return
        t = pygame.time.get_ticks() * 0.008
        cx = int(draw_x + self.FlowerSize * 0.5)
        cy = int(draw_y + self.FlowerSize * 0.5)
        if flower.Special == "rainbow":
            r = int(127 + 127 * math.sin(t))
            g = int(127 + 127 * math.sin(t + 2.1))
            b = int(127 + 127 * math.sin(t + 4.2))
            pygame.draw.circle(self.CurrentScreen, (r, g, b), (cx, cy), 7)

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

        self.CurrentScreen.blit(shaded, (fx, fy))
        self.DrawSpecialBadge(flower, fx, fy)

    BOARD_PULSE_PALETTE = [
        ((165, 95, 255), (38, 18, 72)),   # Electric Violet
        ((70, 225, 255), (14, 48, 68)),   # Cyan Frost
        ((255, 115, 200), (68, 18, 52)),  # Rose Magenta
        ((105, 250, 170), (16, 58, 38)),  # Emerald Mint
        ((255, 205, 95), (68, 46, 14)),   # Golden Amber
        ((255, 125, 110), (68, 22, 22)),  # Sunset Coral
    ]

    def DrawBoardBorderShader(self):
        board_w = self.BoardCol * self.CellSize
        board_h = self.BoardRow * self.CellSize
        bx = self.BoardStartX
        by = self.BoardStartY
        phase = pygame.time.get_ticks() * 0.0045
        pulse = (math.sin(phase - math.pi * 0.5) + 1.0) * 0.5
        cycle_idx = int(phase / (2.0 * math.pi)) % len(self.BOARD_PULSE_PALETTE)
        glow_rgb, base_rgb = self.BOARD_PULSE_PALETTE[cycle_idx]
        gr, gg, gb = glow_rgb
        br, bg_c, bb = base_rgb

        # Steady non-glowing play area backdrop & checkerboard tiles
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

        # Multi-layered animated shader glow radiating outwards from the border outline
        pad_out = 36
        glow_surf = pygame.Surface((board_w + 24 + pad_out * 2, board_h + 24 + pad_out * 2), pygame.SRCALPHA)
        for layer in range(8, 0, -1):
            spread = layer * 3
            alpha = int((26 + 38 * pulse) * (9 - layer) / 8)
            rect = pygame.Rect(
                pad_out - spread,
                pad_out - spread,
                board_w + 24 + spread * 2,
                board_h + 24 + spread * 2,
            )
            pygame.draw.rect(glow_surf, (gr, gg, gb, alpha), rect, width=4, border_radius=16 + spread)

        # Bright inner core border outline
        core_r = min(255, int(gr + (255 - gr) * (0.3 + 0.4 * pulse)))
        core_g = min(255, int(gg + (255 - gg) * (0.3 + 0.4 * pulse)))
        core_b = min(255, int(gb + (255 - gb) * (0.3 + 0.4 * pulse)))
        pygame.draw.rect(
            glow_surf,
            (core_r, core_g, core_b, 245),
            (pad_out, pad_out, board_w + 24, board_h + 24),
            width=3,
            border_radius=16,
        )
        self.CurrentScreen.blit(glow_surf, (bx - 12 - pad_out, by - 12 - pad_out))

    @staticmethod
    def _draw_lightning_bolt(surf, x1, y1, x2, y2, color, core_color, width=4, segments=12, jitter=11.0):
        pts = [(int(x1), int(y1))]
        dx = (x2 - x1) / segments
        dy = (y2 - y1) / segments
        px, py = (-dy, dx)
        plen = math.hypot(px, py) or 1.0
        px, py = px / plen, py / plen
        for i in range(1, segments):
            offset = random.uniform(-jitter, jitter)
            pts.append((int(x1 + dx * i + px * offset), int(y1 + dy * i + py * offset)))
        pts.append((int(x2), int(y2)))
        pygame.draw.lines(surf, color, False, pts, width + 4)
        pygame.draw.lines(surf, core_color, False, pts, max(2, width))

    def DrawEffects(self):
        # Special power-up shaders (Zap, Rainbow, Bomb)
        if self.SpecialEffects:
            fx_surf = pygame.Surface((self.ScreenWidth, 720), pygame.SRCALPHA)
            alive_fx = []
            board_w = self.BoardCol * self.CellSize
            board_h = self.BoardRow * self.CellSize
            rainbow_palette = [
                (255, 80, 110),
                (255, 165, 70),
                (255, 240, 90),
                (95, 245, 145),
                (85, 215, 255),
                (170, 120, 255),
                (255, 110, 220),
            ]
            for eff in self.SpecialEffects:
                eff["timer"] += 1
                t_cur = eff["timer"]
                t_max = eff["max_timer"]
                if t_cur > t_max:
                    continue
                alive_fx.append(eff)
                prog = t_cur / float(t_max)
                fade = 1.0 - prog
                etype = eff["type"]

                if etype == "zap":
                    cx, cy = int(eff["cx"]), int(eff["cy"])
                    r, c = eff["r"], eff["c"]
                    row_y = self.BoardStartY + r * self.CellSize
                    col_x = self.BoardStartX + c * self.CellSize
                    beam_alpha = int(175 * (fade ** 0.8))
                    core_alpha = int(245 * fade)

                    # Glowing plasma row & column beams
                    pygame.draw.rect(
                        fx_surf,
                        (255, 225, 70, beam_alpha // 2),
                        (self.BoardStartX, row_y + 8, board_w, self.CellSize - 16),
                        border_radius=12,
                    )
                    pygame.draw.rect(
                        fx_surf,
                        (255, 225, 70, beam_alpha // 2),
                        (col_x + 8, self.BoardStartY, self.CellSize - 16, board_h),
                        border_radius=12,
                    )
                    # Crackling horizontal & vertical lightning bolts
                    self._draw_lightning_bolt(
                        fx_surf,
                        self.BoardStartX,
                        cy,
                        self.BoardStartX + board_w,
                        cy,
                        (255, 230, 60, beam_alpha),
                        (255, 255, 235, core_alpha),
                        width=4,
                        segments=16,
                        jitter=13.0 * fade + 3.0,
                    )
                    self._draw_lightning_bolt(
                        fx_surf,
                        cx,
                        self.BoardStartY,
                        cx,
                        self.BoardStartY + board_h,
                        (120, 240, 255, beam_alpha),
                        (255, 255, 235, core_alpha),
                        width=4,
                        segments=14,
                        jitter=13.0 * fade + 3.0,
                    )
                    pygame.draw.circle(fx_surf, (255, 250, 150, beam_alpha), (cx, cy), int(38 * fade + 10))
                    pygame.draw.circle(fx_surf, (255, 255, 255, core_alpha), (cx, cy), int(18 * fade + 4))

                elif etype == "rainbow":
                    cx, cy = int(eff["cx"]), int(eff["cy"])
                    alpha = int(235 * fade)
                    # Expanding 7-color prismatic ring from source flower
                    base_rad = int(18 + prog * 360)
                    for idx, (rr, rg, rb) in enumerate(rainbow_palette):
                        rad = max(4, base_rad - idx * 5)
                        pygame.draw.circle(fx_surf, (rr, rg, rb, max(0, int(alpha * 0.75))), (cx, cy), rad, width=4)

                    # Prismatic laser ribbons shooting to every matched color flower
                    for idx, (tx, ty) in enumerate(eff["targets"]):
                        tx_i, ty_i = int(tx), int(ty)
                        col1 = rainbow_palette[(idx + t_cur) % len(rainbow_palette)]
                        col2 = rainbow_palette[(idx + t_cur + 2) % len(rainbow_palette)]
                        pygame.draw.line(fx_surf, (*col1, int(alpha * 0.7)), (cx, cy), (tx_i, ty_i), 7)
                        pygame.draw.line(fx_surf, (*col2, alpha), (cx, cy), (tx_i, ty_i), 3)
                        pygame.draw.line(fx_surf, (255, 255, 255, alpha), (cx, cy), (tx_i, ty_i), 1)
                        burst_r = int(12 + 16 * math.sin(prog * math.pi))
                        pygame.draw.circle(fx_surf, (*col1, int(alpha * 0.65)), (tx_i, ty_i), burst_r)
                        pygame.draw.circle(fx_surf, (255, 255, 255, alpha), (tx_i, ty_i), max(3, burst_r // 2))

                elif etype == "bomb":
                    cx, cy = int(eff["cx"]), int(eff["cy"])
                    bx, by, bw, bh = eff["rect"]
                    alpha = int(230 * (fade ** 0.85))
                    # Glowing 5x5 blast zone overlay
                    pygame.draw.rect(
                        fx_surf,
                        (255, 95, 50, int(120 * fade)),
                        (bx, by, bw, bh),
                        border_radius=18,
                    )
                    pygame.draw.rect(
                        fx_surf,
                        (255, 220, 110, alpha),
                        (bx, by, bw, bh),
                        width=4,
                        border_radius=18,
                    )
                    # Expanding fireball & concentric shockwave rings
                    max_rad = int(max(bw, bh) * 0.62)
                    shock_rad = max(8, int(prog * max_rad))
                    inner_rad = max(4, int((1.0 - prog * 0.5) * max_rad * 0.55))
                    pygame.draw.circle(fx_surf, (255, 110, 45, int(155 * fade)), (cx, cy), inner_rad)
                    pygame.draw.circle(fx_surf, (255, 235, 140, int(210 * fade)), (cx, cy), int(inner_rad * 0.6))
                    pygame.draw.circle(fx_surf, (255, 95, 195, alpha), (cx, cy), shock_rad, width=6)
                    pygame.draw.circle(fx_surf, (255, 245, 170, alpha), (cx, cy), max(4, shock_rad - 10), width=3)

            self.SpecialEffects = alive_fx
            self.CurrentScreen.blit(fx_surf, (0, 0))

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
                fy -= 0.75
                alpha -= 2.4
                if alpha > 0:
                    ft[2], ft[3] = fy, alpha
                    alive_texts.append(ft)
                    draw_alpha = min(255, int(alpha))
                    surf = self.FontSmall.render(text, True, color)
                    surf.set_alpha(draw_alpha)
                    glow = self.FontSmall.render(text, True, (60, 20, 120))
                    glow.set_alpha(draw_alpha)
                    self.CurrentScreen.blit(glow, (int(fx) + 2, int(fy) + 2))
                    self.CurrentScreen.blit(surf, (int(fx), int(fy)))
            self.FloatingTexts = alive_texts

    def TriggerTimeOver(self):
        if self.IsTimeOver:
            return
        self.CurrentTime = 0
        self.IsTimeOver = True
        self.TimeOverStart = pygame.time.get_ticks()
        self.AnimData = None
        self.IsFalling = False
        self.FlowersSeletced.clear()
        self.HintPair = None
        self.DragStartCell = None
        self.SaveCurrentScore()
        if self.Sound:
            self.Sound.Play("gameover")

        self.TimeOverFlowers = []
        for r_idx, row in enumerate(self.Board):
            for c_idx, flower in enumerate(row):
                if flower is None:
                    continue
                delay = (self.BoardRow - 1 - r_idx) * 3 + abs(c_idx - 4.5) * 1.5 + random.uniform(0, 4)
                vx = random.uniform(-3.6, 3.6)
                vy = random.uniform(-5.2, -1.5)
                ang_vel = random.choice([-1, 1]) * random.uniform(3.5, 9.5)
                self.TimeOverFlowers.append(
                    [flower.Surf, float(flower.X), float(flower.Y), vx, vy, 0.0, ang_vel, delay, flower.Name, False]
                )

    def DrawTimeOverShader(self):
        elapsed = pygame.time.get_ticks() - self.TimeOverStart
        t = elapsed * 0.004
        board_w = self.BoardCol * self.CellSize
        board_h = self.BoardRow * self.CellSize
        cx = self.BoardStartX + board_w // 2
        cy = self.BoardStartY + board_h // 2

        # Update & draw cascading tumbling flowers falling off the board
        alive_flowers = []
        for tf in self.TimeOverFlowers:
            surf, fx, fy, vx, vy, angle, ang_vel, delay, col_name, launched = tf
            if delay > 0:
                tf[7] = delay - 1.0
                jitter_x = fx + math.sin(elapsed * 0.05 + fy) * 2.5
                self.CurrentScreen.blit(surf, (int(jitter_x), int(fy)))
                alive_flowers.append(tf)
            else:
                if not launched:
                    tf[9] = True
                    if random.random() < 0.35:
                        self.SpawnBurst(fx, fy, col_name)
                fx += vx
                fy += vy
                vy += 0.58
                angle = (angle + ang_vel) % 360.0
                tf[1], tf[2], tf[4], tf[5] = fx, fy, vy, angle
                if fy < 790:
                    rot_surf = pygame.transform.rotate(surf, angle)
                    rect = rot_surf.get_rect(center=(int(fx + self.FlowerSize * 0.5), int(fy + self.FlowerSize * 0.5)))
                    self.CurrentScreen.blit(rot_surf, rect.topleft)
                    alive_flowers.append(tf)
        self.TimeOverFlowers = alive_flowers

        # Expanding shockwave rings + twilight shader wash over the board
        fx_surf = pygame.Surface((self.ScreenWidth, 720), pygame.SRCALPHA)
        wash_alpha = min(135, int(elapsed * 0.08))
        pygame.draw.rect(
            fx_surf,
            (28, 10, 52, wash_alpha),
            (self.BoardStartX - 12, self.BoardStartY - 12, board_w + 24, board_h + 24),
            border_radius=16,
        )
        for ring_idx in range(3):
            ring_prog = (elapsed - ring_idx * 260) * 0.42
            if 0 < ring_prog < 520:
                ring_alpha = max(0, int(190 * (1.0 - ring_prog / 520.0)))
                ring_col = (255, 120, 210, ring_alpha) if ring_idx % 2 == 0 else (120, 230, 255, ring_alpha)
                pygame.draw.circle(fx_surf, ring_col, (cx, cy), int(ring_prog), width=4)
        self.CurrentScreen.blit(fx_surf, (0, 0))

        # Glowing "TIME OVER!" shader banner centered over the board
        banner_w, banner_h = 520, 155
        bx = cx - banner_w // 2
        by = cy - banner_h // 2 + int(math.sin(t * 2.0) * 6)
        self.Shader.DrawGlowPanel(self.CurrentScreen, bx, by, banner_w, banner_h, hovered=True)

        pulse = (math.sin(t * 3.0) + 1.0) * 0.5
        main_col = (255, int(215 + 35 * pulse), int(140 + 60 * pulse))
        glow_col = (210, 35, 115)
        self.Shader.DrawGlowText(
            self.CurrentScreen,
            self.FontTimeOver,
            "TIME OVER!",
            bx,
            by + 26,
            main_color=main_col,
            glow_color=glow_col,
            offset=4,
            max_width=banner_w - 40,
            center_width=banner_w,
        )

    def DrawBoard(self):
        self.DrawBoardBorderShader()
        if self.IsTimeOver:
            self.DrawTimeOverShader()
            self.DrawEffects()
            return
        selected_positions = set(self.FlowersSeletced)
        hint_positions = set(self.HintPair) if self.HintPair else set()
        t = pygame.time.get_ticks() * 0.015
        shake_x = 0.0
        shake_y = 0.0
        if self.ScreenShake > 0.2:
            shake_x = random.uniform(-self.ScreenShake, self.ScreenShake)
            shake_y = random.uniform(-self.ScreenShake, self.ScreenShake)
            self.ScreenShake *= 0.84
        else:
            self.ScreenShake = 0.0

        for r_idx, row in enumerate(self.Board):
            for c_idx, flower in enumerate(row):
                draw_x = flower.X + shake_x
                draw_y = flower.Y + shake_y
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
                    self.CurrentScreen.blit(flower.Surf, (draw_x, draw_y))
                    self.DrawSpecialBadge(flower, draw_x, draw_y)

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
            ("Match 4 (Zap):", "Spawns a zap flower that clears its full row & column!", (255, 235, 140)),
            ("Match 5 (Rainbow):", "Spawns a rainbow-ring flower that clears all flowers of its color (+3s)!", (255, 195, 245)),
            ("Match 6+ (Bomb):", "Spawns a bomb flower that blasts a 5x5 area around it (+3s)!", (160, 255, 210)),
            ("Combos & Levels:", "Chain cascades boost your multiplier (2x, 3x...). Level up for +15s!", (245, 235, 255)),
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
        self.Shader.DrawParallaxBackground(self.CurrentScreen)
        self.Shader.DrawAtmosphere(self.CurrentScreen)

        hud_x, hud_y, hud_w, hud_h = 875, 60, 355, 435
        pad_x = hud_x + 22
        inner_w = hud_w - 44

        # Main HUD panel
        self.Shader.DrawGlowPanel(self.CurrentScreen, hud_x, hud_y, hud_w, hud_h)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, f"Level {self.Level}", pad_x, 70, main_color=(180, 240, 255), offset=2, max_width=inner_w)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, f"Score: {self.UserScore}", pad_x, 112, main_color=(255, 240, 170), offset=2, max_width=inner_w)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontTiny, f"High Score: {max(self.BestScore, self.UserScore)}", pad_x, 154, main_color=(210, 255, 195), offset=1, max_width=inner_w)

        # Level Progress Bar
        prev_target = (self.Level - 1) * 1500 if self.Level > 1 else 0
        span = max(1, self.LevelTarget - prev_target)
        prog = max(0.0, min(1.0, (self.UserScore - prev_target) / span))
        bar_x, bar_y, bar_w, bar_h = pad_x, 196, inner_w, 18
        pygame.draw.rect(self.CurrentScreen, (25, 15, 55), (bar_x, bar_y, bar_w, bar_h), border_radius=9)
        if prog > 0:
            pygame.draw.rect(self.CurrentScreen, (140, 235, 255), (bar_x, bar_y, int(bar_w * prog), bar_h), border_radius=9)
        pygame.draw.rect(self.CurrentScreen, (210, 180, 255), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=9)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontTiny, f"Next Level: {self.LevelTarget}", pad_x, 222, offset=1, max_width=inner_w)

        time_col = (255, 110, 110) if self.CurrentTime <= 10 else (245, 235, 255)
        mins, secs = divmod(max(0, int(self.CurrentTime)), 60)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, f"Time: {mins:02d}:{secs:02d}", pad_x, 258, main_color=time_col, offset=2, max_width=inner_w)
        if self.ComboCount > 1:
            self.Shader.DrawGlowText(self.CurrentScreen, self.FontSmall, f"Combo: {self.ComboCount}x!", pad_x, 300, main_color=(255, 220, 120), offset=2, max_width=inner_w)

        self.Shader.DrawGlowText(self.CurrentScreen, self.FontTiny, "8-Way & Drag Swap Enabled", pad_x, 344, main_color=(210, 210, 255), offset=1, max_width=inner_w)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontTiny, "Match 4: Zap (Clears Row & Col)", pad_x, 378, main_color=(255, 235, 140), offset=1, max_width=inner_w)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontTiny, "Match 5: Rainbow (Clears Color)", pad_x, 410, main_color=(255, 195, 245), offset=1, max_width=inner_w)
        self.Shader.DrawGlowText(self.CurrentScreen, self.FontTiny, "Match 6+: Bomb (5x5 Blast)", pad_x, 442, main_color=(160, 255, 210), offset=1, max_width=inner_w)

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
                self.SaveCurrentScore()
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

            if self.IsTimeOver:
                if pygame.time.get_ticks() - self.TimeOverStart > 1200:
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                        self.ScreenNeedsToChange = True
                        self.ScreenToChangeToo = "EndScreen"
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        self.ScreenNeedsToChange = True
                        self.ScreenToChangeToo = "EndScreen"
                continue

            if event.type == pygame.USEREVENT:
                self.CurrentTime -= 1
                if 0 < self.CurrentTime <= 10 and self.Sound:
                    self.Sound.Play("tick")
                if self.CurrentTime <= 0:
                    self.TriggerTimeOver()
                    continue
            if event.type == pygame.KEYDOWN and self.AnimData is None and not self.IsFalling:
                if event.key == pygame.K_r and self.ShufflesLeft > 0:
                    self.ShufflesLeft -= 1
                    self.ShuffleBoard()
                elif event.key == pygame.K_h:
                    if self.Sound:
                        self.Sound.Play("select")
                    self.ShowHowToPlay = True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.AnimData is None and not self.IsFalling:
                self.HintPair = None
                self.LastActionTime = pygame.time.get_ticks()
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
                self.HintPair = None
                self.LastActionTime = pygame.time.get_ticks()
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

        if self.IsTimeOver:
            if pygame.time.get_ticks() - self.TimeOverStart >= 3200:
                self.ScreenNeedsToChange = True
                self.ScreenToChangeToo = "EndScreen"
            return

        if self.AnimData is not None:
            flower1, flower2, target1_x, target1_y, target2_x, target2_y = self.AnimData
            self.MoveFlowerPairAnim(flower1, flower2, target1_x, target1_y, target2_x, target2_y)
            self.LastActionTime = pygame.time.get_ticks()
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

