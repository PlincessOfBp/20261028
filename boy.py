from pico2d import (
    load_image, SDL_KEYDOWN, SDL_KEYUP,
    SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT, SDLK_a,
)
import math
import random
import time
from transitions import Machine


class AutoRun:
    DURATION = 5
    SPEED_MULTIPLIER = 2
    SPRITE_SIZE = 150

    def __init__(self, boy):
        self.boy = boy
        self.started_at = 0.0

    def enter(self):
        self.started_at = time.monotonic()

    def update(self, now, elapsed):
        half_size = self.SPRITE_SIZE // 2
        left_edge = half_size
        right_edge = self.boy.SCREEN_WIDTH - half_size
        next_x = (
            self.boy.x
            + self.boy.direction * self.boy.RUN_SPEED * self.SPEED_MULTIPLIER * elapsed
        )

        if next_x <= left_edge:
            self.boy.x = left_edge
            self.boy.direction = 1
        elif next_x >= right_edge:
            self.boy.x = right_edge
            self.boy.direction = -1
        else:
            self.boy.x = next_x

        self.boy.frame = (self.boy.frame + 1) % 8
        return now - self.started_at >= self.DURATION


class Boy:
    image = None
    RUN_SPEED = 200
    SCREEN_WIDTH = 800
    SPRITE_WIDTH = 100

    def __init__(self):
        self.x, self.y = random.randint(self.SPRITE_WIDTH // 2, self.SCREEN_WIDTH - self.SPRITE_WIDTH // 2), 90
        self.frame = random.randint(0, 7)
        self.direction = 1
        self.state_entered_at = time.monotonic()
        self.last_update_at = self.state_entered_at
        self.image = load_image('animation_sheet.png')
        self.auto_run = AutoRun(self)
        self.machine = Machine(
            model=self,
            states=['IDLE', 'RUN', 'SLEEP', 'AUTO_RUN'],
            initial='IDLE',
            transitions=[
                {'trigger': 'sleep', 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'wake_up', 'source': 'SLEEP', 'dest': 'IDLE'},
                {'trigger': 'start_run', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
                {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'start_auto_run', 'source': 'IDLE', 'dest': 'AUTO_RUN'},
                {'trigger': 'cancel_auto_run', 'source': 'AUTO_RUN', 'dest': 'RUN'},
                {'trigger': 'finish_auto_run', 'source': 'AUTO_RUN', 'dest': 'IDLE'},
            ],
            after_state_change='reset_state_timer',
            auto_transitions=False,
        )

    def update(self):
        now = time.monotonic()
        elapsed = now - self.last_update_at
        self.last_update_at = now

        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 8
            if now - self.state_entered_at >= 5:
                self.sleep()
        elif self.state == 'RUN':
            self.x = min(
                self.SCREEN_WIDTH - self.SPRITE_WIDTH // 2,
                max(self.SPRITE_WIDTH // 2, self.x + self.direction * self.RUN_SPEED * elapsed),
            )
            self.frame = (self.frame + 1) % 8
        elif self.state == 'AUTO_RUN':
            if self.auto_run.update(now, elapsed):
                self.finish_auto_run()

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and self.state == 'IDLE' and event.key == SDLK_a:
            self.start_auto_run()
        elif event.type == SDL_KEYDOWN and self.state in ('IDLE', 'SLEEP') and event.key in (SDLK_LEFT, SDLK_RIGHT):
            self.direction = -1 if event.key == SDLK_LEFT else 1
            self.start_run()
        elif event.type == SDL_KEYDOWN and self.state == 'AUTO_RUN' and event.key in (SDLK_LEFT, SDLK_RIGHT):
            self.direction = -1 if event.key == SDLK_LEFT else 1
            self.cancel_auto_run()
        elif event.type == SDL_KEYUP and self.state == 'RUN' and event.key in (SDLK_LEFT, SDLK_RIGHT):
            self.stop_run()
        elif self.state == 'SLEEP' and event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            self.wake_up()

    def on_enter_AUTO_RUN(self):
        self.auto_run.enter()

    def reset_state_timer(self):
        self.state_entered_at = time.monotonic()
        self.last_update_at = self.state_entered_at

    def draw(self):
        idle_row = 300 if self.direction == 1 else 200
        if self.state == 'SLEEP':
            self.image.clip_composite_draw(
                self.frame * 100, idle_row, 100, 100,
                math.pi / 2, '', self.x, self.y, 100, 100,
            )
        elif self.state == 'AUTO_RUN':
            self.image.clip_composite_draw(
                self.frame * 100, 100, 100, 100,
                0, 'h' if self.direction == -1 else '',
                self.x, self.y, self.auto_run.SPRITE_SIZE, self.auto_run.SPRITE_SIZE,
            )
        elif self.state == 'RUN' and self.direction == -1:
            self.image.clip_composite_draw(
                self.frame * 100, 100, 100, 100,
                0, 'h', self.x, self.y, 100, 100,
            )
        elif self.state == 'RUN':
            self.image.clip_draw(self.frame * 100, 100, 100, 100, self.x, self.y)
        else:
            self.image.clip_draw(self.frame * 100, idle_row, 100, 100, self.x, self.y)
