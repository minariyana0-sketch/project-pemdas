import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, BooleanProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.animation import Animation
import random
from functools import partial

NUM_FISH = 10
kivy.require("2.3.1")

FISH_TYPES = [
    {
        "name": "Ikan Biasa",
        "size": 300,
        "weight": 1,
        "image_right": "images/IKAN KECIL 1 KANAN.png",
        "image_left": "images/IKAN KECIL 1 KIRI.png"
    },
    {
        "name": "Ikan Besar",
        "size": 500,
        "weight": 10,
        "image_right": "images/IKAN BESAR 10 KANAN.png",
        "image_left": "images/IKAN BESAR 10 KIRI.png"
    },
    {
        "name": "Ikan Sedang",
        "size": 350,
        "weight": 3,
        "image_right": "images/IKAN SEDANG 3 KANAN.png",
        "image_left": "images/IKAN SEDANG 3 KIRI.png"
    },
]


class Fish(Widget):
    fish_size = NumericProperty(0)
    weight = NumericProperty(0)
    image_source = StringProperty("")
    image_right = StringProperty("")
    image_left = StringProperty("")
    is_caught = BooleanProperty(False)
    is_moving = BooleanProperty(True)
    direction = NumericProperty(1)  # 1 = kanan, -1 = kiri
    caught_image = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (self.fish_size, self.fish_size)
        self.image_source = self.image_right  
        Clock.schedule_once(self.mulai_berenang, random.uniform(0.5, 2.0))

    def mulai_berenang(self, *args):
        if not self.is_moving or self.is_caught:
            return
        if random.random() < 0.15:
            Clock.schedule_once(self.mulai_berenang, random.uniform(1.0, 3.0))
            return
        if random.choice([True, False]):
            self.gerak_ke_kanan()
        else:
            self.gerak_ke_kiri()
        self.animasi_bergerak_acak()

    def gerak_ke_kanan(self, *args):
        if not self.is_moving or self.is_caught:
            return
        Animation.cancel_all(self, 'x')
        self.direction = 1
        self.image_source = self.image_right
        if self.x > Window.width * 0.85:
            self.gerak_ke_kiri()
            return
        target_x = Window.width + self.width
        base_dur = 12.0 if self.weight >= 10 else 10.0
        durasi = random.uniform(base_dur, base_dur + 6.0)
        anim = Animation(x=target_x, duration=durasi, t='in_out_sine')
        anim.bind(on_complete=self.mulai_berenang)
        anim.start(self)

    def gerak_ke_kiri(self, *args):
        if not self.is_moving or self.is_caught:
            return
        Animation.cancel_all(self, 'x')
        self.direction = -1
        self.image_source = self.image_left
        if self.x < Window.width * 0.15:
            self.gerak_ke_kanan()
            return
        target_x = -self.width
        base_dur = 12.0 if self.weight >= 10 else 10.0
        durasi = random.uniform(base_dur, base_dur + 6.0)
        anim = Animation(x=target_x, duration=durasi, t='in_out_sine')
        anim.bind(on_complete=self.mulai_berenang)
        anim.start(self)

    def animasi_bergerak_acak(self, *args):
        if not self.is_moving or self.is_caught:
            return
        Animation.cancel_all(self, 'y')
        water_top = Window.height * 0.6
        min_y = 20
        max_y = max(min_y + 20, water_top - self.height - 20)
        target_y = random.uniform(min_y, max_y)
        durasi = random.uniform(8.0, 14.0)
        anim = Animation(y=target_y, duration=durasi, t='in_out_sine')
        anim.bind(on_complete=self.animasi_bergerak_acak)
        anim.start(self)


class FishingLine(Widget):
    player_id = NumericProperty(0)
    is_casting = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.caught_fish = None 

    def get_hook_rect(self):
        hook_size = 30
        hook_x = self.center_x - hook_size / 2
        hook_y = self.y - 150 + 20 
        return (hook_x, hook_y, hook_size, hook_size)

    def move_left(self):
        if self.parent:
            self.x = max(0, self.x - 25)

    def move_right(self):
        if self.parent:
            self.x = min(self.parent.width - self.width, self.x + 25)

    def cast(self):
        if not self.is_casting and self.parent:
            self.is_casting = True
            water_surface = Window.height * 0.4  
            anim = Animation(y=water_surface, duration=0.4)
            anim.start(self)


class GameScreen(Screen):
    score1 = NumericProperty(0)
    score2 = NumericProperty(0)
    time_left = NumericProperty(60)
    num_players = NumericProperty(1)
    player1_line = ObjectProperty(None)
    player2_line = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fishes = []

    def on_pre_enter(self):
        Clock.unschedule(self.update)
        Clock.unschedule(self.update_time)
        self.initialize_game()
        self.player1_line = self.ids.get('p1_line')
        self.player2_line = self.ids.get('p2_line')
        Clock.schedule_interval(self.update, 1 / 60.0)
        Clock.schedule_interval(self.update_time, 1.0)

    def on_leave(self):
        Clock.unschedule(self.update)
        Clock.unschedule(self.update_time)

    def initialize_game(self):
        self.score1 = 0
        self.score2 = 0
        self.time_left = 60
        self.fishes = []
        if 'fish_layer' in self.ids:
            self.ids.fish_layer.clear_widgets()
        for _ in range(NUM_FISH):
            self.spawn_new_fish()

    def spawn_new_fish(self, *args):
        ft = random.choice(FISH_TYPES)
        f = Fish(
            fish_size=ft["size"],
            weight=ft["weight"],
            image_right=ft["image_right"],
            image_left=ft["image_left"]
        )
        water_top = Window.height * 0.6
        f.x = random.uniform(0, Window.width - f.width)
        f.y = random.uniform(20, max(30, water_top - f.height - 20))
        if 'fish_layer' in self.ids:
            self.ids.fish_layer.add_widget(f)
        self.fishes.append(f)
        f.mulai_berenang()

    def update(self, dt):
        active_lines = []
        if self.player1_line and self.player1_line.is_casting:
            active_lines.append(self.player1_line)
        if self.num_players == 2 and self.player2_line and self.player2_line.is_casting:
            active_lines.append(self.player2_line)

        for fish in self.fishes[:]:
            for line in active_lines:
                hx, hy, hw, hh = line.get_hook_rect()
                if (fish.x < hx + hw and fish.right > hx and
                    fish.y < hy + hh and fish.top > hy):
                    self.catch_fish(line, fish)
                    break

    def update_time(self, dt):
        self.time_left -= 1
        if self.time_left <= 0:
            self.end_game()     

    def catch_fish(self, line_widget, fish_widget):
        if fish_widget.is_caught:
            return
        fish_widget.is_caught = True
        fish_widget.is_moving = False
        Animation.cancel_all(fish_widget)

        score = fish_widget.weight
        if line_widget.player_id == 1:
            self.score1 += score
        else:
            self.score2 += score

        line_widget.caught_fish = fish_widget

        hook_x, hook_y, _, _ = line_widget.get_hook_rect()
        fish_widget.x = hook_x - (fish_widget.width - 30) / 2  
        fish_widget.y = hook_y - fish_widget.height

        target_y = Window.height * 0.75
        duration = 1.5

        anim_line = Animation(y=target_y, duration=duration, t='in_out_quad')
        anim_line.start(line_widget)

        anim_fish = Animation(y=target_y - fish_widget.height - 30, duration=duration, t='in_out_quad')
        anim_fish.bind(on_complete=partial(self.finish_catch, line_widget, fish_widget))
        anim_fish.start(fish_widget)

    def finish_catch(self, line_widget, fish_widget, *args):
        if fish_widget.parent:
            self.ids.fish_layer.remove_widget(fish_widget)
        self.spawn_new_fish()
        line_widget.caught_fish = None
        line_widget.is_casting = False

    def end_game(self):
        Clock.unschedule(self.update)
        Clock.unschedule(self.update_time)
        go = self.manager.get_screen("gameover")
        go.score1_text.text = f"Player 1: {self.score1}"
        go.score2_text.text = f"Player 2: {self.score2}"
        go.score2_text.opacity = 1 if self.num_players == 2 else 0
        self.manager.current = "gameover"


class MenuScreen(Screen):
    def start_game(self):
        self.manager.current = "player_menu"


class PlayerMenuScreen(Screen):
    def start_game_solo(self):
        self.manager.get_screen("game").num_players = 1
        self.manager.current = "game"
    def start_game_vs(self):
        self.manager.get_screen("game").num_players = 2
        self.manager.current = "game"


class GameOverScreen(Screen):
    score1_text = ObjectProperty(None)
    score2_text = ObjectProperty(None)
    def restart_game(self):
        game = self.manager.get_screen("game")
        game.initialize_game()
        self.manager.current = "game"
    def go_menu(self):
        self.manager.current = "menu"
    def exit_game(self):
        App.get_running_app().stop()


class FishingGameApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(PlayerMenuScreen(name="player_menu"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(GameOverScreen(name="gameover"))
        Window.size = (1000, 600)
        Window.bind(on_key_down=self.on_key_down)
        return sm

    def on_key_down(self, win, key, scancode, text, mods):
        if self.root.current != "game":
            return
        g = self.root.get_screen("game")
        # Player 1
        if key in (97, ord("a")) and g.player1_line:
            g.player1_line.move_left()
        elif key in (100, ord("d")) and g.player1_line:
            g.player1_line.move_right()
        elif key in (119, ord("w")) and g.player1_line:
            g.player1_line.cast()
        # Player 2
        if g.num_players == 2:
            if key == 276 and g.player2_line: g.player2_line.move_left()
            elif key == 275 and g.player2_line: g.player2_line.move_right()
            elif key == 273 and g.player2_line: g.player2_line.cast()

if __name__ == "__main__":
    FishingGameApp().run()