from math import pi, atan2, cos, sin, fabs, radians

import arcade
from time import sleep

from arcade import load_sound, play_sound
from arcade.examples.slime_invaders import GAME_OVER
from arcade.resources import sound_hit1, sound_rock_hit2, sound_jump1, sound_jump3, sound_fall1, sound_gameover1, \
    sound_laser1, sound_secret2, sound_lose2

# print(help(arcade))

"""
Игра "пинг-понг".

Надо как можно дольше отбивать шарик ракеткой, не давая ему провалиться "в подвал". 
У игрока за игру есть определённое количество шариков. Как только шарик падает в подвал, раунд заканчивается. 
Как только у игрока не остаётся ни одного шарика, игра заканчивается.
Во время игры ведётся счёт, это количество отражённых ударов.

Управление:
    Подача - клавиша "пробел"
    Движение ракетки - стрелки влево и вправо
    Начало новой игры - клавиша "Enter"    

Особенности:
    * Ракетка имеет закруглённые края в виде полукруга, и эта геометрия учитывается при отбивании шарика краем ракетки.
    * Если при отражении шарика ракетка находится в движении, то это немного влияет на горизонтальную скорость шарика 
        (увеличивает, если направления движения ракетки и шарика совпадают, или уменьшает в противном случае)

"""

# Размеры и титул экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = 'Anastasia Pong'

COLLISION_DEPTH = 2  # Глубина прогиба ракетки при столкновении (выяснилось экспериментальным путём)

INIT_BALL_SPEED_X = 2  # Начальная скорость шара
INIT_BALL_SPEED_Y = 4

BAR_INIT_POS_X = SCREEN_WIDTH / 2   # Начальная позиция центра ракетки
BAR_INIT_POS_Y = SCREEN_HEIGHT / 5

ADDED_BALL_SPEED_X = 0.2  # Добавка к горизонтальной скорости шарика в долях от скорости движения ракетки

BAR_MOVEMENT_SPEED = 5  # Скорость ракетки при движении

INIT_TRIALS_QTY = 3  # Начальное количество шариков

LIVES_CNT_TEXT_X = 10   # Позиция текста счётчика шариков
LIVES_CNT_TEXT_Y = 20

SCORE_X = SCREEN_WIDTH * 0.75    # Позиция текста счёта
SCORE_Y = 20

TEXT_SIZE = 14      # Параметры текста - размер и цвет
TEXT_COLOR = arcade.color.BLACK

MIN_ANGLE = radians(15)  # Минимальный угол отклонения вектора скорости от вертикали или горизонтали - 15 градусов

SCORE_LIMIT = 5    # Количество ударов, после которого скорость движения шара увеличивается
SCORE_ACCELERATION = 0.2    # доля увеличения скорости



class Bar(arcade.Sprite):
    def __init__(self):
        super().__init__('Bar.png', 1)

    def update(self):  # Движение ракетки
        if (self.change_x >= 0 and self.right < SCREEN_WIDTH) or (self.change_x <= 0 and self.left > 0):
            self.center_x += self.change_x  # Двигаемся, если не достигли краёв
        else:
            self.change_x = 0  # Достигли краёв
            play_sound(bar_bump, volume=2, pan=-1, looping=False)


class Ball(arcade.Sprite):
    def __init__(self):
        super().__init__('Ball.png', 1)

    def setup(self):
        pass

    def update(self):  # Движение шара
        if self.right >= SCREEN_WIDTH or self.left <= 0:  # При ударе об край меняется знак скорости по x
            self.change_x = -self.change_x  # Отражаемся от бортов
            play_sound(ball_to_wall, 1, pan=-1, looping=False)
        if self.top >= SCREEN_HEIGHT:
            self.change_y = -self.change_y  # Отражаемся от потолка
            play_sound(ball_to_ceil, 1, pan=-1, looping=False)
        self.center_x += self.change_x  # Двигаемся
        self.center_y += self.change_y


class Game(arcade.Window):

    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.bar = Bar()
        self.ball = Ball()
        self.setup_game()  # Инициализация игры из 3-х раундов
        self.setup_round()  # Инициализация раунда

    def on_draw(self):
        self.clear(color=(255, 255, 255))
        self.bar.draw()  # Рисуем объекты
        self.ball.draw()
        # Пишем остаток жизней и счёт
        arcade.draw_text(f'Шариков: {self.lives_left}' +
                         ('    Шарики улетели! Нажми <ENTER>.' if self.lives_left == 0 else '')
                         , start_x=LIVES_CNT_TEXT_X, start_y=LIVES_CNT_TEXT_Y, color=TEXT_COLOR, font_size=TEXT_SIZE)
        arcade.draw_text(text=f'Счёт: {self.ball_hits}', start_x=SCORE_X, start_y=SCORE_Y,
                         color=TEXT_COLOR, font_size=TEXT_SIZE)

    def setup_game(self):
        """ инициализация 3-раундовой игры """
        self.lives_left = INIT_TRIALS_QTY
        self.ball_hits = 0

    def setup_round(self):
        """ Инициализируем раунд """
        # Позиционируем ракетку
        self.bar.center_x = BAR_INIT_POS_X
        self.bar.center_y = BAR_INIT_POS_Y
        # Задаём скорость движения ракетки
        self.change_x = 0
        # ПОзиционируем шар
        self.ball.center_x = self.bar.center_x + self.bar.width / 10  # Сместим шарик чуть вправо от середины ракетки
        self.ball.bottom = self.bar.top
        #  Задаём скорость движения шара
        self.ball.change_x = 0  # INIT_BALL_SPEED_X
        self.ball.change_y = 0  # INIT_BALL_SPEED_Y

        # Установки:
        self.in_collision = False  # Не в столкновении
        self.in_round_start = True  # На старте раунда - т.е. ещё не подали шарик

    def update(self, delta_time: float):
        if self.ball.top <= 0 and not self.in_round_start:  # Упустили шар в подвал
            self.lives_left -= 1
            if self.lives_left > 0:
                play_sound(ball_lost, volume=1, pan=-1, looping=False)
            else:
                play_sound(snd_game_over, volume=1, pan=-1, looping=False)
            sleep(3)
            if self.lives_left > 0:
                self.setup_round()
            else:
                self.in_round_start = True
        elif arcade.check_for_collision(self.bar, self.ball):
            if not self.in_collision:  # Это начало столкновения (первое касание при столкновении) с ракеткой
                play_sound(ball_to_bar, 2, -1, False)
                self.ball_hits += 1  # Увеличили счёт
                self.in_collision = True  # Находимся в режиме столкновения - чтоб избежать попыток повторного изменения скорости
                """ Вызовем метод расчёта вектора скорости после столкновения.
                 Вектор скорости зависит:
                    - от взаимного положения шарика и ракетки (т.к. края ракетки имеют полукруглую форму с 
                        с радиусом, равным половине высоты ракетки)
                    - от вектора скорости падения шарика
                    - от скорости движения ракетки в момент столкновения (она увеличивает/уменьшает горизонтальную скорость
                        отскока шарика 
                        
                Параметры вообще можно было не передавать - это всё атрибуты объектов, известных внутри игры,
                но поскольку скорость вычисляется нетривиально, то метод отлаживался в отдельном тестовом модуле,
                И гораздо удобнее было все входные данные параметризовать.
                
                Метод возвращает составляющие (х, у) вектора скорости отражения.
                """
                self.ball.change_x, self.ball.change_y = self.change_ball_speed(
                    ball_center=(self.ball.center_x, self.ball.center_y),  # координаты центра шарика
                    bar_center=(self.bar.center_x, self.bar.center_y),  # координаты центра ракетки
                    bar_dim=(self.bar.width, self.bar.height),  # размеры ракетки
                    ball_speed_i=(self.ball.change_x, self.ball.change_y),  # составляющие вектора падения шарика
                    bar_speed=self.bar.change_x  # скорость движения ракетки
                )
        else:  # не в столкновении - сбросим флаг
            self.in_collision = False

        if ((not self.in_round_start) or  # (1)
                ((self.bar.change_x > 0 and self.bar.right < SCREEN_WIDTH) or (  # (2)
                        self.bar.change_x < 0 < self.bar.left))):
            self.ball.update()  # перерисовываем шарик только в 2-х случаях: (1) когда мы не на старте раунда 2) мы на старте
            # раунда, т.е. шарик "приклеен" к ракетке, и ракетка в движении, и ещё не упёрлась в стенки
        self.bar.update()  # ракетку перерисовываем всегда

    def change_ball_speed(self, ball_center, bar_center, bar_dim, ball_speed_i, bar_speed):
        """
        Рассчитывает новый вектор скорости шара при отражении от ракетки в зависимости от:
            - вектора скорости падения
            - относительного положения шара и ракетки
            - скорости движения ракетки
        :return: ball_speed_r = (change_x, change_y) - вектор скорости отражённого шара
        """
        bar_center_left = (
            bar_center[0] - bar_dim[0] / 2. + bar_dim[1] / 2., bar_center[1])  # центр левого полукруга ракетки
        bar_center_right = (
            bar_center[0] + bar_dim[0] / 2 - bar_dim[1] / 2, bar_center[1])  # центр правого полукруга ракетки

        # добавка к скорости при наборе очередной порции ударов в количестве SCORE_LIMIT
        accel_coeff = 1 + (0 if self.ball_hits % SCORE_LIMIT else SCORE_ACCELERATION)
        # print(f'Коэф.ускорения {accel_coeff}')

        # Если шарик падает на ровную пов-ть, то при отскоке просто меняется знак вектора скорости по вертикали:
        if bar_center_left[0] <= ball_center[0] <= bar_center_right[0]:  # Столкновение с ровной поверхностью ракетки
                        # а к скорости по горизонтали добавляется часть скорости движения ракетки.
            return accel_coeff * (ball_speed_i[0] + bar_speed * ADDED_BALL_SPEED_X), -ball_speed_i[1] * accel_coeff

        """ atan всегда возвращает значение угла, лежащего в 1-й или 4-й четвертях. Поскольку угол падения всегда отрицательный,
        а нам нужен противоположный угол, то если вернулся угол отрицательный, нам надо добавить 180 град:  
        """
        angle_i = atan2(ball_speed_i[1], ball_speed_i[0])  # Угол, противоположный углу падения
        if angle_i < 0:
            angle_i += pi  # Угол скорости всегда отрицательный при столкновении, а здесь мы
            # вычисляем противоположный угол, т.е. не "куда летит", а "откуда летит"

        # Вычислим угол нормали (angle_n) в момент столкновения. Он зависит от точки падения шара.
        # Шарик падает на торец, нормаль - это угол вектора от центра закругления ракетки к центру шара в момент столкновения.

        if ball_center[0] > bar_center_right[0]:  # Столкновение с правым торцом ракетки
            angle_n = atan2(ball_center[1] - bar_center_right[1], ball_center[0] - bar_center_right[0])
        else:  # Столкновение с левым торцом ракетки
            angle_n = atan2(ball_center[1] - bar_center_left[1],
                            ball_center[0] - bar_center_left[0])
            angle_n = angle_n + (2 * pi if angle_n < 0 else 0)  # угол нормали здесь должен быть во 2-й или 3-й четверти


        # Теперь вычислим угол отражения (с учётом, что angle_i - угол, _обратный_ углу падения):
        #                               angle_r = angle_n + (angle_n - angle_i) ( это равно 2 * angle_n - angle_i)
        if fabs(angle_i - angle_n) < pi / 2:  # шар упал под острым углом на поверхность отражения - отскакивает
            angle_r = 2 * angle_n - angle_i
            speed_i_modulus = (ball_speed_i[0] ** 2 + ball_speed_i[1] ** 2) ** 0.5  # Вычислим модуль скорости падения
            # А модуль скорости отражения должен быть такой же.

            # Если угол становится вертикальным (т.е. приближается к pi/2), то отклоним его от вертикали.
            # А если он слишком горизонтальный (т.е. приближается к 0 или к pi), то отклоним его от горизонтали
            if (0 <= angle_r <= MIN_ANGLE) or (pi / 2 <= angle_r <= pi / 2 + MIN_ANGLE) or (-pi <= angle_r <= -pi + MIN_ANGLE):
                angle_r += MIN_ANGLE
            elif (-MIN_ANGLE <= angle_r <= 0) or (pi / 2 - MIN_ANGLE <= angle_r <= pi / 2) or (pi - MIN_ANGLE <= angle_r <= pi):
                angle_r -= MIN_ANGLE

            speed_i_modulus *= accel_coeff

            # Добавка "+ bar_speed * ADDED_BALL_SPEED_X - добавляет часть скорости движения ракетки.
            return speed_i_modulus * cos(angle_r) + bar_speed * ADDED_BALL_SPEED_X, speed_i_modulus * sin(angle_r)
        else:  # Шар упал под тупым углом к плоскости отражения - такое может быть
            # только на краях ракетки, когда он летит "вскользь". В этом случае скорость не меняется.
            return ball_speed_i[0], ball_speed_i[1]

    def on_key_press(self, symbol: int, modifiers: int):
        if self.lives_left > 0:  # Игра не закончена
            if symbol == arcade.key.RIGHT and self.bar.right < SCREEN_WIDTH:  # движ каретки в пределах поля
                self.bar.change_x = BAR_MOVEMENT_SPEED
            elif symbol == arcade.key.LEFT and self.bar.left > 0:
                self.bar.change_x = -BAR_MOVEMENT_SPEED
            elif symbol in (arcade.key.LEFT, arcade.key.RIGHT):
                bar_is_moving = False

            # В начале раунда (до подачи) шарик двигается вместе с ракеткой
            if self.in_round_start:
                self.ball.change_x = self.bar.change_x

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.RIGHT, arcade.key.LEFT) and self.lives_left > 0:  # останов ракетки
            self.bar.change_x = 0
            if self.in_round_start:
                self.ball.change_x = 0
        elif symbol == arcade.key.SPACE and self.in_round_start and self.lives_left > 0:  # Подача
            play_sound(ball_serve)
            self.ball.change_x = INIT_BALL_SPEED_X
            self.ball.change_y = INIT_BALL_SPEED_Y
            self.in_round_start = False  # Всё, не в начале раунда
        elif symbol == arcade.key.ENTER and self.lives_left <= 0:  # Начало 3-раундовой игры
            self.setup_game()  # Инициализируем игру,
            self.setup_round()  # Инициализируем раунд


if __name__ == '__main__':
    window = Game(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    bar_bump = load_sound(sound_hit1)
    ball_to_wall = load_sound(sound_rock_hit2)
    ball_to_ceil = load_sound(sound_jump1)
    ball_to_bar = load_sound(sound_jump3)
    ball_lost = load_sound(sound_lose2)
    snd_game_over = load_sound(sound_gameover1)
    ball_serve = load_sound(sound_secret2)
    arcade.run()
