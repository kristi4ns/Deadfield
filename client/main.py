import pygame
from game.game import Game

pygame.init()

# The game always uses a 1280x720 (16:9) play area
screen_width = 1280
screen_height = 720

# SCALED stretches the picture to fit the window and keeps the 16:9 shape
# RESIZABLE lets you drag the window edges or use the green fullscreen button
display_flags = pygame.SCALED | pygame.RESIZABLE
screen = pygame.display.set_mode((screen_width, screen_height), display_flags)

game = Game(screen_width, screen_height)
pygame.display.set_caption("Deadfield")
clock = pygame.time.Clock()
title_font = pygame.font.SysFont(None, 120)
wave_font = pygame.font.SysFont(None, 90)
menu_font = pygame.font.SysFont(None, 48)
hud_font = pygame.font.SysFont(None, 36)

button_width = 220
button_height = 60
button_x = game.screen_width / 2 - button_width / 2


def make_buttons(option_count, first_button_y):
    # One rectangle (button) for each option, one below the other
    buttons = []
    for option_number in range(option_count):
        button_y = first_button_y + option_number * 80
        button_rectangle = pygame.Rect(button_x, button_y, button_width, button_height)
        buttons.append(button_rectangle)
    return buttons


menu_buttons = make_buttons(len(game.menu_options), game.screen_height / 2 - 70)
game_over_buttons = make_buttons(len(game.game_over_options), game.screen_height / 2)


def draw_buttons(surface, options, buttons):
    for option_number in range(len(options)):
        if option_number == game.hovered_option:
            button_color = (255, 200, 0)
            text_color = (30, 30, 30)
        else:
            button_color = (70, 70, 70)
            text_color = (230, 230, 230)

        button_rectangle = buttons[option_number]
        pygame.draw.rect(surface, button_color, button_rectangle, border_radius=8)

        option_text = menu_font.render(options[option_number], True, text_color)
        text_position = option_text.get_rect(center=button_rectangle.center)
        surface.blit(option_text, text_position)


def draw_crosshair(surface, center_x, center_y):
    crosshair_color = (255, 255, 255)

    # A circle with a small dot in the middle
    pygame.draw.circle(surface, crosshair_color, (center_x, center_y), 12, 2)
    pygame.draw.circle(surface, crosshair_color, (center_x, center_y), 2)

    # Four short lines pointing at the center
    pygame.draw.line(surface, crosshair_color, (center_x - 20, center_y), (center_x - 8, center_y), 2)
    pygame.draw.line(surface, crosshair_color, (center_x + 8, center_y), (center_x + 20, center_y), 2)
    pygame.draw.line(surface, crosshair_color, (center_x, center_y - 20), (center_x, center_y - 8), 2)
    pygame.draw.line(surface, crosshair_color, (center_x, center_y + 8), (center_x, center_y + 20), 2)


def draw_game_world(surface):
    # Bullets
    for bullet in game.bullets:
        bullet_position = (int(bullet["x"]), int(bullet["y"]))
        pygame.draw.circle(surface, (255, 220, 0), bullet_position, game.bullet_size)

    # Zombies
    for zombie in game.zombies:
        zombie_rectangle = pygame.Rect(0, 0, game.zombie_size, game.zombie_size)
        zombie_rectangle.center = (zombie["x"], zombie["y"])
        pygame.draw.rect(surface, (200, 50, 50), zombie_rectangle)

    # Player (it blinks while the pause after a hit is running)
    player_is_hidden = (game.hit_timer // 5) % 2 == 1
    if not player_is_hidden:
        player_rectangle = pygame.Rect(0, 0, game.player_size, game.player_size)
        player_rectangle.center = (game.player_x, game.player_y)
        pygame.draw.rect(surface, (0, 200, 0), player_rectangle)


def draw_hud(surface):
    # HUD = the information shown on top of the game (score, health, and so on)
    score_text = hud_font.render("Score: " + str(game.score), True, (255, 255, 255))
    surface.blit(score_text, (20, 20))

    # Wave number at the top in the middle
    wave_text = hud_font.render("Wave " + str(game.wave_number), True, (255, 255, 255))
    surface.blit(wave_text, wave_text.get_rect(center=(screen_width / 2, 35)))

    # Health bar: a dark red box with a green part on top that gets shorter
    bar_x = 20
    bar_y = 55
    bar_width = 200
    bar_height = 20
    health_fraction = game.player_health / game.player_max_health

    bar_background = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    bar_fill = pygame.Rect(bar_x, bar_y, int(bar_width * health_fraction), bar_height)

    pygame.draw.rect(surface, (90, 20, 20), bar_background)
    pygame.draw.rect(surface, (0, 200, 0), bar_fill)
    pygame.draw.rect(surface, (255, 255, 255), bar_background, 2)


def draw_wave_message(surface):
    # A big message in the middle of the screen during the break between waves
    message_text = wave_font.render("Wave " + str(game.wave_number), True, (255, 255, 255))
    surface.blit(message_text, message_text.get_rect(center=(screen_width / 2, screen_height / 2 - 150)))


while game.running:
    # Which buttons are on the screen right now?
    if game.state == "menu":
        active_buttons = menu_buttons
    elif game.state == "game_over":
        active_buttons = game_over_buttons
    else:
        active_buttons = []

    # Find which button the mouse is over (None means no button)
    mouse_position = pygame.mouse.get_pos()
    hovered_button = None
    for option_number in range(len(active_buttons)):
        if active_buttons[option_number].collidepoint(mouse_position):
            hovered_button = option_number

    # Show the normal mouse arrow in the menus, the crosshair while playing
    pygame.mouse.set_visible(game.state != "playing")

    # 1. Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # For now Esc closes the game (later it will be the pause button)
            game.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game.state != "playing" and hovered_button is not None:
                game.click_option(hovered_button)

    if game.state == "playing":
        pressed_keys = pygame.key.get_pressed()
        direction_x = 0
        direction_y = 0
        if pressed_keys[pygame.K_a]:
            direction_x = direction_x - 1
        if pressed_keys[pygame.K_d]:
            direction_x = direction_x + 1
        if pressed_keys[pygame.K_w]:
            direction_y = direction_y - 1
        if pressed_keys[pygame.K_s]:
            direction_y = direction_y + 1
        game.move_player(direction_x, direction_y)

        # Holding the left mouse button keeps shooting (the game adds the delay)
        pressed_mouse_buttons = pygame.mouse.get_pressed()
        if pressed_mouse_buttons[0]:
            game.shoot(mouse_position[0], mouse_position[1])

    # 2. Events
    if game.state == "playing":
        game.update_game()
    else:
        game.hover_option(hovered_button)

    # 3. Drawing
    screen.fill((30, 30, 30))

    if game.state == "menu":
        draw_buttons(screen, game.menu_options, menu_buttons)

    elif game.state == "playing":
        draw_game_world(screen)
        draw_hud(screen)

        # Big "Wave 2" message while the break between waves is running
        if game.wave_break_timer > 0:
            draw_wave_message(screen)

        # Crosshair (drawn last so it is on top of everything)
        draw_crosshair(screen, mouse_position[0], mouse_position[1])

    elif game.state == "game_over":
        # The frozen game stays visible behind a dark see-through layer
        draw_game_world(screen)
        dark_layer = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        dark_layer.fill((0, 0, 0, 160))
        screen.blit(dark_layer, (0, 0))

        title_text = title_font.render("GAME OVER", True, (200, 50, 50))
        screen.blit(title_text, title_text.get_rect(center=(screen_width / 2, screen_height / 2 - 140)))

        final_score_text = menu_font.render("Score: " + str(game.score), True, (255, 255, 255))
        screen.blit(final_score_text, final_score_text.get_rect(center=(screen_width / 2, screen_height / 2 - 70)))

        wave_reached_text = menu_font.render("Wave reached: " + str(game.wave_number), True, (255, 255, 255))
        screen.blit(wave_reached_text, wave_reached_text.get_rect(center=(screen_width / 2, screen_height / 2 - 30)))

        draw_buttons(screen, game.game_over_options, game_over_buttons)

    pygame.display.flip()

    # 4. Pause (keeps the game at 60 frames per second)
    clock.tick(60)

pygame.quit()