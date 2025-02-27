from random import uniform, choice, randint
from pygame.locals import *
from itertools import chain
import pygame, sys

pygame.init()

num_cells = 40
cell_size = 20

game_mode = 'menu'
screen_size = screen_width, screen_height = (num_cells * cell_size,
                                             (num_cells - 10) * cell_size)
screen = pygame.display.set_mode(screen_size)
clock = pygame.time.Clock()

left_wall = pygame.Rect(-1, 0, 1, screen_height)
right_wall = pygame.Rect(screen_width + 1, 0, 1, screen_height)
top_wall = pygame.Rect(0, -1, screen_width, 1)
bottom_wall = pygame.Rect(0, screen_height, screen_width, 1)

bg_img = pygame.image.load('./assets/img/background.png').convert_alpha()
noise = pygame.image.load('./assets/img/noise.png').convert_alpha()
bg_sound = pygame.mixer.Sound('./assets/sfx/background.wav')
hit_sound = pygame.mixer.Sound('./assets/sfx/hit.wav')
click_sound = pygame.mixer.Sound('./assets/sfx/click.wav')
lost_hp_sound = pygame.mixer.Sound('./assets/sfx/lost_hp.wav')
end_1_sound = pygame.mixer.Sound('./assets/sfx/end_1.wav')
end_2_sound = pygame.mixer.Sound('./assets/sfx/end_2.wav')
end_3_sound = pygame.mixer.Sound('./assets/sfx/end_3.wav')
end_4_sound = pygame.mixer.Sound('./assets/sfx/end_4.wav')

bg_sound.set_volume(0.1)
hit_sound.set_volume(0.5)
lost_hp_sound.set_volume(0.4)
noise_pos = (-randint(0, 10), -randint(0, 10))
end_sounds = [end_1_sound, end_2_sound, end_3_sound, end_4_sound]
for sound in end_sounds:
    sound.set_volume(0.2)

try:
    with open('./best_score.txt', mode='r', encoding='utf-8') as file:
        best_score = int(file.read())
except:
    with open('./best_score.txt', mode='w', encoding='utf-8') as file:
        file.write('0')
    best_score = 0

def change_game_mode():
    if game_mode == 'menu':
        return 'game'
    elif game_mode == 'game':
        return 'pause'
    elif game_mode == 'pause':
        return 'game'
    elif game_mode == 'again':
        return 'game_start'

def find_divisors(n):
    divisors = []
    for i in range(1, n+1):
        if n % i == 0:
            divisors.append(i)
    return divisors

class GameObject:
    def __init__(self, x, y, width, height, color, velocity):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.velocity_x, self.velocity_y = velocity
        
    def randomize_velocity(self):
        self.velocity_x += self.velocity_x * uniform(-0.01, 0.01)
        self.velocity_y += self.velocity_y * uniform(-0.01, 0.01)
        
    def wall_collision(self, rect, enable_bottom_wall=True):
        if rect.colliderect(left_wall):
            self.collide('x')
            self.x = self.width + 1
        if rect.colliderect(right_wall):
            self.collide('x')
            self.x = screen_width - self.width - 1
        if rect.colliderect(top_wall):
            self.collide('y')
            self.y = self.height + 1
        if rect.colliderect(bottom_wall) and enable_bottom_wall:
            self.collide('y')
        
    def get_pos(self):
        return (self.x, self.y)
    
    def get_size(self):
        return (self.width, self.height)
    
    def collide(self, collision_type):
        if collision_type == 'x':
            self.velocity_x *= -1
        elif collision_type == 'y':
            self.velocity_y *= -1

class Ball(GameObject):
    def __init__(self, x, y, radius, color, velocity):
        super().__init__(x, y, radius, radius, color, velocity)
        self.radius = radius
        
    def update(self):
        self.rect = pygame.Rect((self.x - self.width, self.y - self.height),
                                (self.radius*2, self.radius*2))
        self.wall_collision(self.rect, enable_bottom_wall=False)
        self.randomize_velocity()
    
        self.x += self.velocity_x
        self.y += self.velocity_y
    
    def draw(self):
        pygame.draw.circle(screen, self.color, self.get_pos(), self.radius)

class Brick(GameObject):
    def __init__(self, x, y, width, height, hp):
        self.colors = ['whitesmoke', 'grey', 'yellow', 'green', 'darkgreen']
        super().__init__(x, y, width, height, self.colors[hp - 1], [0, 0])
        self.hp = hp
        self.rect = pygame.Rect(x, y, width, height)
            
    def draw(self):
        if self.hp > 0:
            pygame.draw.rect(screen, self.colors[self.hp - 1], self.rect)
        
class Wall:
    def __init__(self, num_rows):
        self.num_rows = num_rows
        (self.num_cols, self.brick_width,
         self.border_offset) = self.get_brick_params()
        self.brick_height  = (self.brick_width * 0.4) // 1
        self.size = [(self.brick_width * 0.9) // 1, (self.brick_width * 0.3) // 1]
        self.bricks = self.get_bricks()
    
    def draw(self):
        for row in self.bricks:
            for brick in row:
                brick.draw()
              
    def get_bricks(self):
        bricks = []
        for i in range(self.num_rows):
            bricks.append([])
            for j in range(self.num_cols):                
                brick = Brick(
                    j * self.brick_width + ((self.border_offset * 0.75) // 1),
                i * 30 + self.brick_height - 20, *self.size, 3)
                bricks[-1].append(brick)
        return bricks
        
    def get_brick_params(self, target_brick_number=9):
        border_offset = 20
        shorten_screen_width = num_cells * cell_size - border_offset
        screen_width_divisors = find_divisors(shorten_screen_width)
        diff = [abs(target_brick_number - divisor) 
                for divisor in screen_width_divisors]
        brick_width = 0
        brick_squeeze = 0
        while brick_width < 10:
            num_bricks = screen_width_divisors[
                diff.index(min(diff))] - brick_squeeze
            brick_width = shorten_screen_width / num_bricks
            brick_squeeze += 1
            border_offset -= 1
        if border_offset < 8:
            border_offset = 8
        return num_bricks, brick_width, border_offset

class Platform(GameObject):
    def __init__(self, x, y, width, height, color):
        super().__init__(x, y, width, height, color, [0, 0])
        self.rect = pygame.Rect(x, y, width, height)
        self.velocity_x = choice([-1, 1]) * 5
        
    def update(self):
        self.rect.x += self.velocity_x
        if self.rect.left <= 0:
            self.velocity_x *= -1
            self.rect.left = 1
        if self.rect.right >= screen_width:
            self.velocity_x *= -1
            self.rect.right = screen_width - 1
    
    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)

class Menu:
    def __init__(self, hp):
        self.hp = hp
        self.mainfont = pygame.font.Font('./assets/RasterForgeRegular_Designed_by_GGBotNet.ttf',
                                         screen_size[0] // 10)
        self.button_font = pygame.font.Font('./assets/RasterForgeRegular_Designed_by_GGBotNet.ttf',
                                            screen_size[0] // 30)
        
        self.main_text = self.get_text('BREAKOUT', 'White', text_type='main_menu')
        
        button_width = 200
        button_height = 80
        
        self.start_button = self.get_button('START', screen_width // 2 - button_width // 2,
                                             screen_height // 2 + button_height)
        self.resume_button = self.get_button('RESUME', screen_width // 2 - button_width // 2,
                                             screen_height // 2 - button_height)
        self.main_menu_button = self.get_button('MAIN_MENU', screen_width // 2 - button_width // 2,
                                             screen_height // 2 + 10)
        self.exit_button = self.get_button('EXIT', screen_width // 2 - button_width // 2,
                                             screen_height // 2 + button_height + 20)
        self.again_button = self.get_button('AGAIN', screen_width // 2 - button_width // 2,
                                             screen_height // 2 + button_height)
        
    def get_text(self, text, color='black', text_type='button'):
        if text_type == 'button':
            return self.button_font.render(text, True, color)
        elif text_type == 'main_menu':
            return self.mainfont.render(text, True, color)
        
    def get_button(self, text, x, y, width=200, height=80,text_color='black'):        
        button_rect = pygame.Rect(x, y, width, height)
        button_text = self.get_text(text, text_color)
        return (button_rect, button_text)
        
    def draw_button(self, button_rect, button_text, button_color='white'):
        pygame.draw.rect(screen, button_color, button_rect)
        screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2,
                                  button_rect.centery - button_text.get_height() // 2))
        
    
    def draw(self):
        screen.blit(self.main_text, (screen_width // 2 - self.main_text.get_width() // 2, 50))
        if game_mode == 'menu':
            self.draw_button(*self.start_button)
        elif game_mode == 'pause':
            self.draw_button(*self.resume_button)
            self.draw_button(*self.main_menu_button)
            self.draw_button(*self.exit_button)
        elif game_mode == 'again':
            self.draw_button(*self.again_button)
        
    def click(self, pos):
        if game_mode == 'menu':
            if self.start_button[0].collidepoint(pos):
                return 'game_start'
        elif game_mode == 'pause':
            if self.resume_button[0].collidepoint(pos):
                return 'game'
            elif self.main_menu_button[0].collidepoint(pos):
                return 'menu'
            elif self.exit_button[0].collidepoint(pos):
                return 'exit'
        elif game_mode == 'again':
            if self.again_button[0].collidepoint(pos):
                return 'game_start'
        return game_mode

class Game:
    def __init__(self):
        self.score = 0
        self.platform = Platform((num_cells * cell_size) // 2,
                                 (num_cells - 12) * cell_size, 150, 15,'black')
        self.ball = Ball(self.platform.rect.centerx, self.platform.rect.centery - 20, 10,
                         'green', [uniform(4.8, 5.2) * choice([-1, 1]), uniform(4.8, 5.2)])
        self.wall = Wall(num_rows=4)
        self.menu = Menu(hp=10)
        self.hp_text = self.menu.get_text(str(self.menu.hp), 'white')
        self.score_text = self.menu.get_text(str(self.score), 'white')
        self.best_score_text = self.menu.get_text(f'Record: {best_score}', 'white')
        
    def update(self):
        global game_mode
        if game_mode == 'game':
            self.ball.update()
            self.platform.update()            
            self.collision_handler()     
            if self.menu.hp <= 0:
                choice(end_sounds).play()
                game_mode = 'again'   
    
    def update_hp(self):
        self.menu.hp -= 1
        lost_hp_sound.play()
        color = 'white'
        
        if self.menu.hp <= 3:
            color = 'red'
        elif self.menu.hp <= 5:
            color = 'crimson'
        elif self.menu.hp <= 7:
            color = 'yellow'

        
        self.hp_text = self.menu.get_text(str(self.menu.hp), color)
    
    def update_score(self):
        global best_score
        self.score += 1
        if self.score > 10:
            color = 'yellow'
        elif self.score > 50:
            color = 'green'
        elif self.score > 100:
            color = 'red'
        else:
            color = 'white'
        self.score_text = self.menu.get_text(str(self.score), color)
        if best_score < self.score:
            best_score = self.score
            self.best_score_text = self.menu.get_text(f'Record: {best_score}', 'white')
    
    def collision_handler(self):
        self.ball.rect.topleft = (self.ball.x - self.ball.radius,
                                  self.ball.y - self.ball.radius)
        collided_bricks = [brick for brick in chain(*self.wall.bricks) 
                           if brick.hp > 0 and self.ball.rect.colliderect(brick.rect)]

        for brick in collided_bricks:
            hit_sound.play()
            brick.hp -= 1
            self.update_score()

            if (self.ball.rect.centerx < brick.rect.left) or (
                self.ball.rect.centerx > brick.rect.right):
                self.ball.collide('x')
            else:
                self.ball.collide('y')

            if self.ball.rect.centerx < brick.rect.left:
                self.ball.x = brick.rect.left - self.ball.radius
            elif self.ball.rect.centerx > brick.rect.right:
                self.ball.x = brick.rect.right + self.ball.radius
            elif self.ball.rect.centery < brick.rect.top:
                self.ball.y = brick.rect.top - self.ball.radius  
            elif self.ball.rect.centery > brick.rect.bottom:
                self.ball.y = brick.rect.bottom + self.ball.radius

        self.ball.rect.topleft = (self.ball.x - self.ball.radius,
                                  self.ball.y - self.ball.radius)
        
        if self.ball.rect.colliderect(self.platform.rect):
            self.ball.collide('y')
        
        if self.ball.y > screen_height + abs(self.ball.velocity_y * 10):
            self.ball = Ball(self.platform.rect.centerx, self.platform.rect.centery - 20, 10, 'green',
                             [uniform(4.8, 5.2) * choice([-1, 1]), uniform(4.8, 5.2)])
            self.update_hp()
        
    def draw(self):
        global game_mode
        if game_mode == 'game':
            self.ball.draw()
            self.platform.draw()
            self.wall.draw()
        elif game_mode in ['menu', 'pause', 'again']:
            self.menu.draw()
        if game_mode in ['game', 'pause']:
            screen.blit(self.hp_text, (screen_width - 50, screen_height - 50))
            screen.blit(self.score_text, (50, screen_height - 50))
        if game_mode in ['pause', 'again']:
            screen.blit(self.best_score_text, (screen_width // 2 - self.best_score_text.get_width() // 2, 150))

game = Game()

bg_sound.play(-1)

while True:
    for event in pygame.event.get():
        if event.type == QUIT or game_mode == 'exit':
            pygame.mixer.fadeout(100)
            pygame.display.quit()
            pygame.quit()
            if game.score > best_score:
                with open('./best_score.txt', mode='w', encoding='utf-8') as file:
                    file.write(str(game.score))
                    print(game.score)
            sys.exit()
        elif event.type == KEYDOWN:
            if game_mode == 'game':
                if event.key == K_RIGHT:
                    game.platform.velocity_x = abs(game.platform.velocity_x)
                elif event.key == K_LEFT:
                    game.platform.velocity_x = -abs(game.platform.velocity_x)
            if event.key in (K_RETURN, K_SPACE):
                game_mode = change_game_mode()
                click_sound.play()
        elif event.type == MOUSEBUTTONUP:
            click_sound.play()
            pos = pygame.mouse.get_pos()
            game_mode = game.menu.click(pos)
        if game_mode == 'game_start':
            game_mode = 'game'
            game = Game()    
    game.update()
    
    screen.blit(bg_img, bg_img.get_rect(center=screen.get_rect().center))
    
    game.draw()
    screen.blit(noise, noise_pos, special_flags=BLEND_RGB_MULT)
    
    pygame.display.update()
    clock.tick(60)
    
