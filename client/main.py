import math

import pygame
from game.game import Game

pygame.init()

# The game always uses a 1280x720 (16:9) screen
screen_width = 1280
screen_height = 720

# SCALED stretches the picture to fit the window and keeps the 16:9 shape
# RESIZABLE lets you drag the window edges or use the green fullscreen button
display_flags = pygame.SCALED | pygame.RESIZABLE
screen = pygame.display.set_mode((screen_width, screen_height), display_flags)

# This lets pygame receive typed text (needed for typing the name)
pygame.key.start_text_input()

game = Game(screen_width, screen_height)
pygame.display.set_caption("Deadfield")
clock = pygame.time.Clock()


def make_font(size):
    # pygame uses the first font from this list that your computer has
    return pygame.font.SysFont("helveticaneue,avenir,segoeui,arial", size)


title_font = make_font(100)
wave_font = make_font(72)
menu_font = make_font(36)
value_font = make_font(30)
label_font = make_font(17)

button_width = 220
button_height = 60
button_x = game.screen_width / 2 - button_width / 2

# Colors
ground_color = (48, 68, 54)
panel_color = (18, 22, 24)
panel_line_color = (46, 54, 56)
bright_text_color = (232, 236, 236)
dim_text_color = (125, 138, 140)
bar_empty_color = (38, 45, 47)
health_good_color = (120, 220, 130)
health_medium_color = (240, 190, 60)
health_low_color = (230, 75, 65)
dash_ready_color = (110, 200, 255)
dash_charging_color = (60, 105, 135)
orb_color = (170, 90, 255)
orb_halo_color = (95, 55, 140)
orb_full_color = (255, 200, 0)  # all 10 circles turn gold when you hold 10 orbs
bullet_color = (205, 210, 220)
zombie_color = (205, 60, 60)
player_color = (70, 140, 240)
player_dash_color = (170, 235, 255)
grenade_color = (90, 96, 102)
grenade_warning_color = (230, 75, 65)
explosion_color = (255, 170, 60)

# A dark see-through layer that is drawn over the frozen game (pause and game over screens)
dark_layer = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
dark_layer.fill((0, 0, 0, 170))

# The text shown on the screen for each boost
boost_texts = {
    "faster_shooting": "FASTER SHOOTING",
    "stronger_bullets": "STRONGER BULLETS",
    "more_health": "MORE HEALTH",
}


def make_bullet_picture():
    # Draw the tic-tac 6 times bigger first, then shrink it smoothly,
    # so the edges are clean and not jagged
    scale = 6
    big_length = game.bullet_length * scale
    big_thickness = game.bullet_thickness * scale

    big_picture = pygame.Surface((big_length, big_thickness), pygame.SRCALPHA)
    big_rectangle = pygame.Rect(0, 0, big_length, big_thickness)
    pygame.draw.rect(big_picture, bullet_color, big_rectangle, border_radius=big_thickness // 2)

    return pygame.transform.smoothscale(big_picture, (game.bullet_length, game.bullet_thickness))


# The tic-tac picture is made once here and pointing to the right
# Every bullet then gets a turned copy of it
bullet_picture = make_bullet_picture()


def make_buttons(option_count, first_button_y):
    # One rectangle (button) for each option, one below the other
    buttons = []
    for option_number in range(option_count):
        button_y = first_button_y + option_number * 80
        button_rectangle = pygame.Rect(button_x, button_y, button_width, button_height)
        buttons.append(button_rectangle)
    return buttons


menu_buttons = make_buttons(len(game.menu_options), game.screen_height / 2 - 70)
name_buttons = make_buttons(len(game.name_options), game.screen_height / 2 + 60)
pause_buttons = make_buttons(len(game.pause_options), game.screen_height / 2 - 70)
game_over_buttons = make_buttons(len(game.game_over_options), game.screen_height / 2)


def draw_text(surface, text, font, color, x, y, align="center"):
    # Draws text so that (x, y) is its left, center or right side
    text_image = font.render(text, True, color)
    text_rectangle = text_image.get_rect()

    if align == "left":
        text_rectangle.midleft = (x, y)
    elif align == "right":
        text_rectangle.midright = (x, y)
    else:
        text_rectangle.center = (x, y)

    surface.blit(text_image, text_rectangle)


def draw_bar(surface, x, y, width, height, fraction, fill_color):
    # A slim rounded bar: a dark box with a colored part on top that gets shorter
    # fraction is a number from 0 (empty) to 1 (full)
    bar_box = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, bar_empty_color, bar_box, border_radius=height // 2)

    fill_width = int(width * fraction)
    if fill_width > 0:
        fill_box = pygame.Rect(x, y, fill_width, height)
        pygame.draw.rect(surface, fill_color, fill_box, border_radius=height // 2)


def draw_buttons(surface, options, buttons, hover_color=bright_text_color, hover_text_color=panel_color):
    for option_number in range(len(options)):
        if option_number == game.hovered_option:
            button_color = hover_color
            text_color = hover_text_color
        else:
            button_color = bar_empty_color
            text_color = bright_text_color

        button_rectangle = buttons[option_number]
        pygame.draw.rect(surface, button_color, button_rectangle, border_radius=10)
        draw_text(surface, options[option_number], menu_font, text_color,
                  button_rectangle.centerx, button_rectangle.centery)


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


def draw_bullets(surface):
    for bullet in game.bullets:
        # The picture points to the right, so turn it the way the bullet flies
        # (pygame turns counter-clockwise, but the screen's y goes down, so the angle is flipped)
        angle = -math.degrees(math.atan2(bullet["direction_y"], bullet["direction_x"]))
        turned_picture = pygame.transform.rotozoom(bullet_picture, angle, 1)

        # The bullet's x and y are its front, so the middle of the tic-tac is half a length behind it
        middle_x = bullet["x"] - bullet["direction_x"] * game.bullet_length / 2
        middle_y = bullet["y"] - bullet["direction_y"] * game.bullet_length / 2

        picture_rectangle = turned_picture.get_rect(center=(middle_x, middle_y))
        surface.blit(turned_picture, picture_rectangle)


def draw_grenades(surface):
    for grenade in game.grenades:
        grenade_position = (int(grenade["x"]), int(grenade["y"]))

        # Once it has landed, a ring shows how far the explosion will reach
        if grenade["landed"]:
            pygame.draw.circle(surface, grenade_warning_color, grenade_position, game.grenade_radius, 2)

        # After landing the grenade blinks red until it explodes
        grenade_is_red = grenade["landed"] and (grenade["fuse_timer"] // 4) % 2 == 0
        if grenade_is_red:
            current_grenade_color = grenade_warning_color
        else:
            current_grenade_color = grenade_color

        pygame.draw.circle(surface, current_grenade_color, grenade_position, game.grenade_size)
        pygame.draw.circle(surface, bright_text_color, grenade_position, game.grenade_size, 2)


def draw_explosions(surface):
    for explosion in game.explosions:
        # The explosion fades out: fraction goes from 1 (new) to 0 (gone)
        fraction = explosion["timer"] / game.explosion_time
        alpha = int(190 * fraction)

        # A see-through circle needs its own small picture
        picture_size = game.grenade_radius * 2
        explosion_picture = pygame.Surface((picture_size, picture_size), pygame.SRCALPHA)
        circle_center = (game.grenade_radius, game.grenade_radius)
        pygame.draw.circle(explosion_picture, (*explosion_color, alpha), circle_center, game.grenade_radius)

        picture_x = int(explosion["x"]) - game.grenade_radius
        picture_y = int(explosion["y"]) - game.grenade_radius
        surface.blit(explosion_picture, (picture_x, picture_y))


def draw_game_world(surface):
    # Orbs (drawn first, so everything else is on top of them)
    for orb in game.orbs:
        orb_position = (int(orb["x"]), int(orb["y"]))
        pygame.draw.circle(surface, orb_halo_color, orb_position, game.orb_radius + 5)
        pygame.draw.circle(surface, orb_color, orb_position, game.orb_radius)
        pygame.draw.circle(surface, (240, 225, 255), orb_position, 3)

    # Grenades
    draw_grenades(surface)

    # Bullets
    draw_bullets(surface)

    # Zombies
    for zombie in game.zombies:
        zombie_rectangle = pygame.Rect(0, 0, game.zombie_size, game.zombie_size)
        zombie_rectangle.center = (zombie["x"], zombie["y"])
        pygame.draw.rect(surface, zombie_color, zombie_rectangle)

    # Explosions (on top of the zombies)
    draw_explosions(surface)

    # Player (it blinks while the pause after a hit is running)
    player_is_hidden = (game.hit_timer // 5) % 2 == 1
    if not player_is_hidden:
        # The player turns light blue while dashing
        if game.dash_timer > 0:
            current_player_color = player_dash_color
        else:
            current_player_color = player_color

        player_rectangle = pygame.Rect(0, 0, game.player_size, game.player_size)
        player_rectangle.center = (game.player_x, game.player_y)
        pygame.draw.rect(surface, current_player_color, player_rectangle)


def draw_orb_circles(surface, first_circle_x, circle_y):
    # 10 small circles in a row: one lights up for every orb you hold
    circle_radius = 7
    circle_spacing = 20

    # When you hold all 10 orbs, every circle turns gold
    if game.orbs_collected >= game.orbs_needed:
        lit_color = orb_full_color
    else:
        lit_color = orb_color

    for circle_number in range(game.orbs_needed):
        circle_position = (first_circle_x + circle_number * circle_spacing, circle_y)

        if circle_number < game.orbs_collected:
            pygame.draw.circle(surface, lit_color, circle_position, circle_radius)
        else:
            pygame.draw.circle(surface, bar_empty_color, circle_position, circle_radius)
            pygame.draw.circle(surface, panel_line_color, circle_position, circle_radius, 1)


def draw_top_bar(surface):
    # The bar at the top: health on the left, wave in the middle, best and score on the right
    bar_height = game.play_area_top
    pygame.draw.rect(surface, panel_color, (0, 0, screen_width, bar_height))
    pygame.draw.line(surface, panel_line_color, (0, bar_height - 1), (screen_width, bar_height - 1), 1)

    label_y = 18
    value_y = 41

    # Health (left). The bar changes color when your health gets low
    health_fraction = game.player_health / game.player_max_health

    if health_fraction > 0.5:
        health_color = health_good_color
    elif health_fraction > 0.25:
        health_color = health_medium_color
    else:
        health_color = health_low_color

    draw_text(surface, "HEALTH", label_font, dim_text_color, 30, label_y, "left")
    draw_bar(surface, 30, 34, 220, 10, health_fraction, health_color)

    # Wave (middle)
    draw_text(surface, "WAVE", label_font, dim_text_color, screen_width / 2, label_y)
    draw_text(surface, str(game.wave_number), value_font, bright_text_color, screen_width / 2, value_y)

    # Best score (right, left of the score). It grows along with the score when you beat the record
    draw_text(surface, "BEST", label_font, dim_text_color, screen_width - 180, label_y, "right")
    draw_text(surface, str(game.high_score).zfill(6), value_font, dim_text_color, screen_width - 180, value_y, "right")

    # Score (right, always six digits, like 001240)
    draw_text(surface, "SCORE", label_font, dim_text_color, screen_width - 30, label_y, "right")
    draw_text(surface, str(game.score).zfill(6), value_font, bright_text_color, screen_width - 30, value_y, "right")


def draw_bottom_bar(surface):
    # The bar at the bottom: orbs on the left, dash on the right
    bar_top = game.play_area_bottom
    bar_height = screen_height - bar_top
    center_y = bar_top + bar_height // 2

    pygame.draw.rect(surface, panel_color, (0, bar_top, screen_width, bar_height))
    pygame.draw.line(surface, panel_line_color, (0, bar_top), (screen_width, bar_top), 1)

    # Orbs: the 10 circles
    draw_text(surface, "ORBS", label_font, dim_text_color, 30, center_y, "left")
    draw_orb_circles(surface, 92, center_y)

    # When all 10 orbs are collected, show what the keys do
    if game.orbs_collected >= game.orbs_needed:
        draw_text(surface, "E  BOOST      F  GRENADE", label_font, bright_text_color, 310, center_y, "left")

    # Dash: the bar fills up while the dash recharges, and turns bright when it is ready
    dash_fraction = 1 - game.dash_cooldown_timer / game.dash_cooldown_delay

    if game.dash_cooldown_timer == 0:
        dash_color = dash_ready_color
    else:
        dash_color = dash_charging_color

    draw_text(surface, "DASH", label_font, dim_text_color, 1020, center_y, "left")
    draw_bar(surface, 1070, center_y - 4, 180, 8, dash_fraction, dash_color)


def draw_playing_screen(surface):
    # The ground between the two bars
    ground_height = game.play_area_bottom - game.play_area_top
    pygame.draw.rect(surface, ground_color, (0, game.play_area_top, screen_width, ground_height))

    draw_game_world(surface)

    # The bars are drawn after the world, so zombies walking in from behind them stay hidden
    draw_top_bar(surface)
    draw_bottom_bar(surface)


def draw_name_screen(surface):
    draw_text(surface, "ENTER YOUR NAME", wave_font, bright_text_color, screen_width / 2, screen_height / 2 - 170)

    # The box where the name is typed
    box_rectangle = pygame.Rect(0, 0, 440, 64)
    box_rectangle.center = (screen_width / 2, screen_height / 2 - 70)
    pygame.draw.rect(surface, bar_empty_color, box_rectangle, border_radius=12)
    pygame.draw.rect(surface, panel_line_color, box_rectangle, 2, border_radius=12)

    text_left = box_rectangle.left + 24
    text_center_y = box_rectangle.centery

    # The typed name, or a grey hint while the box is empty
    if game.player_name == "":
        draw_text(surface, "Your name", menu_font, dim_text_color, text_left, text_center_y, "left")
        cursor_x = text_left
    else:
        draw_text(surface, game.player_name, menu_font, bright_text_color, text_left, text_center_y, "left")
        cursor_x = text_left + menu_font.size(game.player_name)[0] + 3

    # The cursor blinks: visible for half a second, then hidden for half a second
    if (pygame.time.get_ticks() // 500) % 2 == 0:
        pygame.draw.line(surface, bright_text_color, (cursor_x, text_center_y - 18), (cursor_x, text_center_y + 18), 2)

    hint_text = "Letters and numbers, up to " + str(game.max_name_length) + " characters"
    draw_text(surface, hint_text, label_font, dim_text_color, screen_width / 2, box_rectangle.bottom + 26)

    draw_buttons(surface, game.name_options, name_buttons)


def draw_wave_message(surface):
    # A big message in the middle of the play area during the break between waves
    message_y = (game.play_area_top + game.play_area_bottom) / 2 - 120
    wave_text = "WAVE " + str(game.wave_number)
    draw_text(surface, wave_text, wave_font, bright_text_color, screen_width / 2, message_y)


def draw_boost_message(surface):
    # Shows which boost you just got, for about 2 seconds
    message_y = (game.play_area_top + game.play_area_bottom) / 2 - 50
    draw_text(surface, boost_texts[game.last_boost], menu_font, orb_color, screen_width / 2, message_y)


while game.running:
    # Which buttons are on the screen right now?
    if game.state == "menu":
        active_buttons = menu_buttons
    elif game.state == "enter_name":
        active_buttons = name_buttons
    elif game.state == "paused":
        active_buttons = pause_buttons
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
        elif event.type == pygame.TEXTINPUT:
            # Typed letters go into the name (only on the name screen)
            if game.state == "enter_name":
                game.add_name_text(event.text)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            if game.state == "enter_name":
                game.delete_name_character()
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if game.state == "enter_name":
                game.confirm_name()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Esc pauses the game (and continues it), or goes back from the name screen
            game.press_escape()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if game.state == "playing":
                game.start_dash()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if game.state == "playing":
                game.use_boost()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            if game.state == "playing":
                game.throw_grenade(mouse_position[0], mouse_position[1])
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
    screen.fill(panel_color)

    if game.state == "menu":
        draw_text(screen, "DEADFIELD", title_font, bright_text_color, screen_width / 2, screen_height / 2 - 160)
        draw_buttons(screen, game.menu_options, menu_buttons)

    elif game.state == "enter_name":
        draw_name_screen(screen)

    elif game.state == "playing":
        draw_playing_screen(screen)

        # Big "WAVE 2" message while the break between waves is running
        if game.wave_break_timer > 0:
            draw_wave_message(screen)

        # Message about the boost you just got
        if game.boost_message_timer > 0:
            draw_boost_message(screen)

        # Crosshair (drawn last so it is on top of everything)
        draw_crosshair(screen, mouse_position[0], mouse_position[1])

    elif game.state == "paused":
        # The frozen game stays visible behind a dark see-through layer
        draw_playing_screen(screen)
        screen.blit(dark_layer, (0, 0))

        draw_text(screen, "PAUSED", title_font, bright_text_color, screen_width / 2, screen_height / 2 - 160)
        draw_buttons(screen, game.pause_options, pause_buttons)

    elif game.state == "game_over":
        # The frozen game stays visible behind a dark see-through layer
        draw_playing_screen(screen)
        screen.blit(dark_layer, (0, 0))

        draw_text(screen, "GAME OVER", title_font, health_low_color, screen_width / 2, screen_height / 2 - 190)
        draw_text(screen, game.player_name, menu_font, dim_text_color, screen_width / 2, screen_height / 2 - 132)
        draw_text(screen, "Score " + str(game.score), menu_font, bright_text_color, screen_width / 2, screen_height / 2 - 98)
        draw_text(screen, "Wave " + str(game.wave_number), menu_font, dim_text_color, screen_width / 2, screen_height / 2 - 64)

        # Gold message if the record was beaten, otherwise show the record
        if game.is_new_best():
            draw_text(screen, "NEW BEST!", menu_font, orb_full_color, screen_width / 2, screen_height / 2 - 30)
        else:
            draw_text(screen, "Best " + str(game.high_score), menu_font, dim_text_color, screen_width / 2, screen_height / 2 - 30)

        # The game over buttons light up red instead of white
        draw_buttons(screen, game.game_over_options, game_over_buttons, health_low_color, bright_text_color)

    pygame.display.flip()

    # 4. Pause (keeps the game at 60 frames per second)
    clock.tick(60)

pygame.quit()