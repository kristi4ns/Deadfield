import math

import pygame

from client import score_sender
from game.game import Game

pygame.init()

# Spēle vienmēr izmanto 1280x720 (16:9) ekrānu
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CENTER_X = SCREEN_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2

# SCALED pielāgo attēlu loga izmēram un saglabā 16:9 formu
# RESIZABLE ļauj mainīt loga izmēru vai lietot zaļo pilnekrāna pogu
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE)

# Šis ļauj pygame saņemt rakstīto tekstu (vajadzīgs vārda ievadei)
pygame.key.start_text_input()

game = Game(SCREEN_WIDTH, SCREEN_HEIGHT)
pygame.display.set_caption("Deadfield")
clock = pygame.time.Clock()


def make_font(size):
    # pygame izmanto pirmo fontu no saraksta, kas ir šajā datorā
    return pygame.font.SysFont("helveticaneue,avenir,segoeui,arial", size)


TITLE_FONT = make_font(100)
WAVE_FONT = make_font(72)
MENU_FONT = make_font(36)
VALUE_FONT = make_font(30)
LABEL_FONT = make_font(17)

BUTTON_WIDTH = 220
BUTTON_HEIGHT = 60
BUTTON_X = CENTER_X - BUTTON_WIDTH / 2

# Krāsas
GROUND_COLOR = (48, 68, 54)
PANEL_COLOR = (18, 22, 24)
PANEL_LINE_COLOR = (46, 54, 56)
BRIGHT_TEXT_COLOR = (232, 236, 236)
DIM_TEXT_COLOR = (125, 138, 140)
BAR_EMPTY_COLOR = (38, 45, 47)
HEALTH_GOOD_COLOR = (120, 220, 130)
HEALTH_MEDIUM_COLOR = (240, 190, 60)
HEALTH_LOW_COLOR = (230, 75, 65)
DASH_READY_COLOR = (110, 200, 255)
DASH_CHARGING_COLOR = (60, 105, 135)
ORB_COLOR = (170, 90, 255)
ORB_HALO_COLOR = (95, 55, 140)
ORB_FULL_COLOR = (255, 200, 0)  # visi 10 apļi kļūst zeltaini, kad tur 10 orbus
BULLET_COLOR = (205, 210, 220)
ZOMBIE_COLOR = (205, 60, 60)
PLAYER_COLOR = (70, 140, 240)
PLAYER_DASH_COLOR = (170, 235, 255)
GRENADE_COLOR = (90, 96, 102)
GRENADE_WARNING_COLOR = (230, 75, 65)
EXPLOSION_COLOR = (255, 170, 60)
CROSSHAIR_COLOR = (255, 255, 255)

# Tumšs caurspīdīgs slānis, ko uzliek virs sastingušās spēles (pauzes un game over ekrānos)
DARK_LAYER = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
DARK_LAYER.fill((0, 0, 0, 170))

# Teksts, ko rāda ekrānā katram uzlabojumam
BOOST_TEXTS = {
    "faster_shooting": "FASTER SHOOTING",
    "stronger_bullets": "STRONGER BULLETS",
    "more_health": "MORE HEALTH",
}


def make_bullet_picture():
    # Vispirms uzzīmējam lodi 6 reizes lielāku un tad gludi samazinām,
    # lai malas būtu tīras un nav robainas
    scale = 6
    big_length = game.bullet_length * scale
    big_thickness = game.bullet_thickness * scale

    big_picture = pygame.Surface((big_length, big_thickness), pygame.SRCALPHA)
    big_rectangle = pygame.Rect(0, 0, big_length, big_thickness)
    pygame.draw.rect(big_picture, BULLET_COLOR, big_rectangle, border_radius=big_thickness // 2)

    return pygame.transform.smoothscale(big_picture, (game.bullet_length, game.bullet_thickness))


# "Tic-tac" attēls tiek izveidots vienreiz, un tas ir vērsts pa labi
# Katra lode pēc tam saņem tā pagrieztu kopiju
BULLET_PICTURE = make_bullet_picture()


def make_buttons(option_count, first_button_y):
    # Katrai izvēlei viens taisnstūris (poga), vienu zem otras
    buttons = []
    for option_number in range(option_count):
        button_y = first_button_y + option_number * 80
        button_rectangle = pygame.Rect(BUTTON_X, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        buttons.append(button_rectangle)
    return buttons


MENU_BUTTONS = make_buttons(len(game.menu_options), CENTER_Y - 70)
NAME_BUTTONS = make_buttons(len(game.name_options), CENTER_Y + 60)
PAUSE_BUTTONS = make_buttons(len(game.pause_options), CENTER_Y - 70)
GAME_OVER_BUTTONS = make_buttons(len(game.game_over_options), CENTER_Y)


# ---------- Zīmēšanas palīgfunkcijas ----------
def draw_text(surface, text, font, color, x, y, align="center"):
    # Uzzīmē tekstu tā, ka (x, y) ir tā kreisā, centra vai labā puse
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
    # Tieva noapaļota josla: tumša kaste ar krāsainu daļu virsū, kas kļūst īsāka
    # fraction ir skaitlis no 0 (tukša) līdz 1 (pilna)
    bar_box = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, BAR_EMPTY_COLOR, bar_box, border_radius=height // 2)

    fill_width = int(width * fraction)
    if fill_width > 0:
        fill_box = pygame.Rect(x, y, fill_width, height)
        pygame.draw.rect(surface, fill_color, fill_box, border_radius=height // 2)


def draw_buttons(surface, options, buttons, hover_color=BRIGHT_TEXT_COLOR, hover_text_color=PANEL_COLOR):
    for option_number in range(len(options)):
        if option_number == game.hovered_option:
            button_color = hover_color
            text_color = hover_text_color
        else:
            button_color = BAR_EMPTY_COLOR
            text_color = BRIGHT_TEXT_COLOR

        button_rectangle = buttons[option_number]
        pygame.draw.rect(surface, button_color, button_rectangle, border_radius=10)
        draw_text(surface, options[option_number], MENU_FONT, text_color,
                  button_rectangle.centerx, button_rectangle.centery)


def draw_crosshair(surface, center_x, center_y):
    # Aplis ar mazu punktu vidū
    pygame.draw.circle(surface, CROSSHAIR_COLOR, (center_x, center_y), 12, 2)
    pygame.draw.circle(surface, CROSSHAIR_COLOR, (center_x, center_y), 2)

    # Četras īsas līnijas, kas vērstas uz centru
    pygame.draw.line(surface, CROSSHAIR_COLOR, (center_x - 20, center_y), (center_x - 8, center_y), 2)
    pygame.draw.line(surface, CROSSHAIR_COLOR, (center_x + 8, center_y), (center_x + 20, center_y), 2)
    pygame.draw.line(surface, CROSSHAIR_COLOR, (center_x, center_y - 20), (center_x, center_y - 8), 2)
    pygame.draw.line(surface, CROSSHAIR_COLOR, (center_x, center_y + 8), (center_x, center_y + 20), 2)


# ---------- Spēles pasaules zīmēšana ----------
def draw_bullets(surface):
    for bullet in game.bullets:
        # Attēls ir vērsts pa labi, tāpēc pagriežam to lodes lidojuma virzienā
        # (pygame griež pretēji pulksteņrādītājam, bet ekrāna y iet uz leju, tāpēc leņķi apgriežam)
        angle = -math.degrees(math.atan2(bullet["direction_y"], bullet["direction_x"]))
        turned_picture = pygame.transform.rotozoom(BULLET_PICTURE, angle, 1)

        # Lodes x un y ir tās priekšgals, tāpēc attēla vidus ir pusgarumu aiz tā
        middle_x = bullet["x"] - bullet["direction_x"] * game.bullet_length / 2
        middle_y = bullet["y"] - bullet["direction_y"] * game.bullet_length / 2

        picture_rectangle = turned_picture.get_rect(center=(middle_x, middle_y))
        surface.blit(turned_picture, picture_rectangle)


def draw_grenades(surface):
    for grenade in game.grenades:
        grenade_position = (int(grenade["x"]), int(grenade["y"]))

        # Kad granāta ir nolaidusies, gredzens parāda, cik tālu sniegsies sprādziens
        if grenade["landed"]:
            pygame.draw.circle(surface, GRENADE_WARNING_COLOR, grenade_position, game.grenade_radius, 2)

        # Pēc nolaišanās granāta mirgo sarkana līdz sprādzienam
        is_blinking_red = grenade["landed"] and (grenade["fuse_timer"] // 4) % 2 == 0
        if is_blinking_red:
            current_color = GRENADE_WARNING_COLOR
        else:
            current_color = GRENADE_COLOR

        pygame.draw.circle(surface, current_color, grenade_position, game.grenade_size)
        pygame.draw.circle(surface, BRIGHT_TEXT_COLOR, grenade_position, game.grenade_size, 2)


def draw_explosions(surface):
    for explosion in game.explosions:
        # Sprādziens izzūd: fraction iet no 1 (jauns) līdz 0 (pazudis)
        fraction = explosion["timer"] / game.explosion_time
        alpha = int(190 * fraction)

        # Caurspīdīgam aplim vajag savu mazo attēlu
        picture_size = game.grenade_radius * 2
        explosion_picture = pygame.Surface((picture_size, picture_size), pygame.SRCALPHA)
        circle_center = (game.grenade_radius, game.grenade_radius)
        pygame.draw.circle(explosion_picture, (*EXPLOSION_COLOR, alpha), circle_center, game.grenade_radius)

        picture_x = int(explosion["x"]) - game.grenade_radius
        picture_y = int(explosion["y"]) - game.grenade_radius
        surface.blit(explosion_picture, (picture_x, picture_y))


def draw_game_world(surface):
    # Orbi (zīmē pirmos, lai viss pārējais ir virs tiem)
    for orb in game.orbs:
        orb_position = (int(orb["x"]), int(orb["y"]))
        pygame.draw.circle(surface, ORB_HALO_COLOR, orb_position, game.orb_radius + 5)
        pygame.draw.circle(surface, ORB_COLOR, orb_position, game.orb_radius)
        pygame.draw.circle(surface, (240, 225, 255), orb_position, 3)

    draw_grenades(surface)
    draw_bullets(surface)

    # Zombiji
    for zombie in game.zombies:
        zombie_rectangle = pygame.Rect(0, 0, game.zombie_size, game.zombie_size)
        zombie_rectangle.center = (zombie["x"], zombie["y"])
        pygame.draw.rect(surface, ZOMBIE_COLOR, zombie_rectangle)

    # Sprādzieni (virs zombijiem)
    draw_explosions(surface)

    # Spēlētājs (mirgo, kamēr turpinās pauze pēc trāpījuma)
    player_is_hidden = (game.hit_timer // 5) % 2 == 1
    if not player_is_hidden:
        # Izrāviena laikā spēlētājs kļūst gaiši zils
        if game.dash_timer > 0:
            current_color = PLAYER_DASH_COLOR
        else:
            current_color = PLAYER_COLOR

        player_rectangle = pygame.Rect(0, 0, game.player_size, game.player_size)
        player_rectangle.center = (game.player_x, game.player_y)
        pygame.draw.rect(surface, current_color, player_rectangle)


# ---------- Joslu zīmēšana ----------
def draw_orb_circles(surface, first_circle_x, circle_y):
    # 10 mazi apļi rindā: par katru orbu iedegas viens
    circle_radius = 7
    circle_spacing = 20

    # Kad tur visus 10 orbus, visi apļi kļūst zeltaini
    if game.orbs_collected >= game.orbs_needed:
        lit_color = ORB_FULL_COLOR
    else:
        lit_color = ORB_COLOR

    for circle_number in range(game.orbs_needed):
        circle_position = (first_circle_x + circle_number * circle_spacing, circle_y)

        if circle_number < game.orbs_collected:
            pygame.draw.circle(surface, lit_color, circle_position, circle_radius)
        else:
            pygame.draw.circle(surface, BAR_EMPTY_COLOR, circle_position, circle_radius)
            pygame.draw.circle(surface, PANEL_LINE_COLOR, circle_position, circle_radius, 1)


def draw_top_bar(surface):
    # Josla augšā: veselība pa kreisi, vilnis vidū, labākais un rezultāts pa labi
    bar_height = game.play_area_top
    pygame.draw.rect(surface, PANEL_COLOR, (0, 0, SCREEN_WIDTH, bar_height))
    pygame.draw.line(surface, PANEL_LINE_COLOR, (0, bar_height - 1), (SCREEN_WIDTH, bar_height - 1), 1)

    label_y = 18
    value_y = 41

    # Veselība (pa kreisi). Josla maina krāsu, kad veselības kļūst maz
    health_fraction = game.player_health / game.player_max_health

    if health_fraction > 0.5:
        health_color = HEALTH_GOOD_COLOR
    elif health_fraction > 0.25:
        health_color = HEALTH_MEDIUM_COLOR
    else:
        health_color = HEALTH_LOW_COLOR

    draw_text(surface, "HEALTH", LABEL_FONT, DIM_TEXT_COLOR, 30, label_y, "left")
    draw_bar(surface, 30, 34, 220, 10, health_fraction, health_color)

    # Vilnis (vidū)
    draw_text(surface, "WAVE", LABEL_FONT, DIM_TEXT_COLOR, CENTER_X, label_y)
    draw_text(surface, str(game.wave_number), VALUE_FONT, BRIGHT_TEXT_COLOR, CENTER_X, value_y)

    # Labākais rezultāts (pa labi, pa kreisi no rezultāta). Tas aug kopā ar rezultātu, kad pārspēj rekordu
    best_x = SCREEN_WIDTH - 180
    draw_text(surface, "BEST", LABEL_FONT, DIM_TEXT_COLOR, best_x, label_y, "right")
    draw_text(surface, str(game.high_score).zfill(6), VALUE_FONT, DIM_TEXT_COLOR, best_x, value_y, "right")

    # Rezultāts (pa labi, vienmēr seši cipari, piemēram 001240)
    score_x = SCREEN_WIDTH - 30
    draw_text(surface, "SCORE", LABEL_FONT, DIM_TEXT_COLOR, score_x, label_y, "right")
    draw_text(surface, str(game.score).zfill(6), VALUE_FONT, BRIGHT_TEXT_COLOR, score_x, value_y, "right")


def draw_bottom_bar(surface):
    # Josla apakšā: orbi pa kreisi, izrāviens pa labi
    bar_top = game.play_area_bottom
    bar_height = SCREEN_HEIGHT - bar_top
    center_y = bar_top + bar_height // 2

    pygame.draw.rect(surface, PANEL_COLOR, (0, bar_top, SCREEN_WIDTH, bar_height))
    pygame.draw.line(surface, PANEL_LINE_COLOR, (0, bar_top), (SCREEN_WIDTH, bar_top), 1)

    # Orbi: 10 apļi
    draw_text(surface, "ORBS", LABEL_FONT, DIM_TEXT_COLOR, 30, center_y, "left")
    draw_orb_circles(surface, 92, center_y)

    # Kad savākti visi 10 orbi, parādām, ko dara taustiņi
    if game.orbs_collected >= game.orbs_needed:
        draw_text(surface, "E  BOOST      F  GRENADE", LABEL_FONT, BRIGHT_TEXT_COLOR, 310, center_y, "left")

    # Izrāviens: josla piepildās, kamēr tas atjaunojas, un kļūst spilgta, kad ir gatavs
    dash_fraction = 1 - game.dash_cooldown_timer / game.dash_cooldown_delay

    if game.dash_cooldown_timer == 0:
        dash_color = DASH_READY_COLOR
    else:
        dash_color = DASH_CHARGING_COLOR

    draw_text(surface, "DASH", LABEL_FONT, DIM_TEXT_COLOR, 1020, center_y, "left")
    draw_bar(surface, 1070, center_y - 4, 180, 8, dash_fraction, dash_color)


def draw_game_view(surface):
    # Zeme starp abām joslām
    ground_height = game.play_area_bottom - game.play_area_top
    pygame.draw.rect(surface, GROUND_COLOR, (0, game.play_area_top, SCREEN_WIDTH, ground_height))

    draw_game_world(surface)

    # Joslas zīmē pēc pasaules, tāpēc zombiji, kas nāk no aiz tām, paliek paslēpti
    draw_top_bar(surface)
    draw_bottom_bar(surface)


# ---------- Ekrānu zīmēšana ----------
def draw_menu_screen(surface):
    draw_text(surface, "DEADFIELD", TITLE_FONT, BRIGHT_TEXT_COLOR, CENTER_X, CENTER_Y - 160)
    draw_buttons(surface, game.menu_options, MENU_BUTTONS)


def draw_name_screen(surface):
    draw_text(surface, "ENTER YOUR NAME", WAVE_FONT, BRIGHT_TEXT_COLOR, CENTER_X, CENTER_Y - 170)

    # Lodziņš, kurā raksta vārdu
    box_rectangle = pygame.Rect(0, 0, 440, 64)
    box_rectangle.center = (CENTER_X, CENTER_Y - 70)
    pygame.draw.rect(surface, BAR_EMPTY_COLOR, box_rectangle, border_radius=12)
    pygame.draw.rect(surface, PANEL_LINE_COLOR, box_rectangle, 2, border_radius=12)

    text_left = box_rectangle.left + 24
    text_center_y = box_rectangle.centery

    # Uzrakstītais vārds vai pelēks mājiens, kamēr lodziņš ir tukšs
    if game.player_name == "":
        draw_text(surface, "Your name", MENU_FONT, DIM_TEXT_COLOR, text_left, text_center_y, "left")
        cursor_x = text_left
    else:
        draw_text(surface, game.player_name, MENU_FONT, BRIGHT_TEXT_COLOR, text_left, text_center_y, "left")
        cursor_x = text_left + MENU_FONT.size(game.player_name)[0] + 3

    # Kursors mirgo: pusi sekundes redzams, pusi sekundes paslēpts
    if (pygame.time.get_ticks() // 500) % 2 == 0:
        cursor_top = (cursor_x, text_center_y - 18)
        cursor_bottom = (cursor_x, text_center_y + 18)
        pygame.draw.line(surface, BRIGHT_TEXT_COLOR, cursor_top, cursor_bottom, 2)

    hint_text = "Letters and numbers, up to " + str(game.max_name_length) + " characters"
    draw_text(surface, hint_text, LABEL_FONT, DIM_TEXT_COLOR, CENTER_X, box_rectangle.bottom + 26)

    draw_buttons(surface, game.name_options, NAME_BUTTONS)


def draw_wave_message(surface):
    # Liela ziņa spēles laukuma vidū pauzes laikā starp viļņiem
    message_y = (game.play_area_top + game.play_area_bottom) / 2 - 120
    wave_text = "WAVE " + str(game.wave_number)
    draw_text(surface, wave_text, WAVE_FONT, BRIGHT_TEXT_COLOR, CENTER_X, message_y)


def draw_boost_message(surface):
    # Parāda, kādu uzlabojumu tikko saņēmi (apmēram 2 sekundes)
    message_y = (game.play_area_top + game.play_area_bottom) / 2 - 50
    draw_text(surface, BOOST_TEXTS[game.last_boost], MENU_FONT, ORB_COLOR, CENTER_X, message_y)


def draw_playing_screen(surface, mouse_position):
    draw_game_view(surface)

    # Liels uzraksts "WAVE 2" pauzes laikā starp viļņiem
    if game.wave_break_timer > 0:
        draw_wave_message(surface)

    # Ziņa par uzlabojumu, ko tikko saņēmi
    if game.boost_message_timer > 0:
        draw_boost_message(surface)

    # Mērķis (zīmē pēdējo, lai tas ir virs visa)
    draw_crosshair(surface, mouse_position[0], mouse_position[1])


def draw_pause_screen(surface):
    # Sastingusī spēle paliek redzama zem tumša caurspīdīga slāņa
    draw_game_view(surface)
    surface.blit(DARK_LAYER, (0, 0))

    draw_text(surface, "PAUSED", TITLE_FONT, BRIGHT_TEXT_COLOR, CENTER_X, CENTER_Y - 160)
    draw_buttons(surface, game.pause_options, PAUSE_BUTTONS)


def draw_send_status(surface):
    # Maza rindiņa apakšā, kas pasaka, vai rezultāts sasniedza mājaslapu
    if score_sender.send_status == "sending":
        status_text = "Saving your score..."
        status_color = DIM_TEXT_COLOR
    elif score_sender.send_status == "saved":
        status_text = "Score saved to the website"
        status_color = HEALTH_GOOD_COLOR
    else:
        status_text = "Could not reach the server, score not saved"
        status_color = HEALTH_LOW_COLOR

    draw_text(surface, status_text, LABEL_FONT, status_color, CENTER_X, CENTER_Y + 190)


def draw_game_over_screen(surface):
    # Sastingusī spēle paliek redzama zem tumša caurspīdīga slāņa
    draw_game_view(surface)
    surface.blit(DARK_LAYER, (0, 0))

    draw_text(surface, "GAME OVER", TITLE_FONT, HEALTH_LOW_COLOR, CENTER_X, CENTER_Y - 190)
    draw_text(surface, game.player_name, MENU_FONT, DIM_TEXT_COLOR, CENTER_X, CENTER_Y - 132)
    draw_text(surface, "Score " + str(game.score), MENU_FONT, BRIGHT_TEXT_COLOR, CENTER_X, CENTER_Y - 98)
    draw_text(surface, "Wave " + str(game.wave_number), MENU_FONT, DIM_TEXT_COLOR, CENTER_X, CENTER_Y - 64)

    # Zeltains uzraksts, ja rekords pārspēts, citādi parādām rekordu
    if game.is_new_best():
        draw_text(surface, "NEW BEST!", MENU_FONT, ORB_FULL_COLOR, CENTER_X, CENTER_Y - 30)
    else:
        draw_text(surface, "Best " + str(game.high_score), MENU_FONT, DIM_TEXT_COLOR, CENTER_X, CENTER_Y - 30)

    # Game over pogas iedegas sarkanas, nevis baltas
    draw_buttons(surface, game.game_over_options, GAME_OVER_BUTTONS, HEALTH_LOW_COLOR, BRIGHT_TEXT_COLOR)

    # Parāda, vai rezultāts nonāca mājaslapā
    draw_send_status(surface)


def draw_current_screen(surface, mouse_position):
    surface.fill(PANEL_COLOR)

    if game.state == "menu":
        draw_menu_screen(surface)
    elif game.state == "enter_name":
        draw_name_screen(surface)
    elif game.state == "playing":
        draw_playing_screen(surface, mouse_position)
    elif game.state == "paused":
        draw_pause_screen(surface)
    elif game.state == "game_over":
        draw_game_over_screen(surface)


# ---------- Ievade ----------
def find_hovered_button(mouse_position):
    # Kuras pogas pašlaik ir uz ekrāna?
    if game.state == "menu":
        active_buttons = MENU_BUTTONS
    elif game.state == "enter_name":
        active_buttons = NAME_BUTTONS
    elif game.state == "paused":
        active_buttons = PAUSE_BUTTONS
    elif game.state == "game_over":
        active_buttons = GAME_OVER_BUTTONS
    else:
        active_buttons = []

    # Atrodam, virs kuras pogas ir pele (None nozīmē, ka virs nevienas)
    hovered_button = None
    for option_number in range(len(active_buttons)):
        if active_buttons[option_number].collidepoint(mouse_position):
            hovered_button = option_number

    return hovered_button


def handle_key_press(key, mouse_position):
    # Esc darbojas vienmēr: pauzē spēli vai atgriež atpakaļ
    if key == pygame.K_ESCAPE:
        game.press_escape()

    # Vārda ekrānā: Backspace dzēš burtu, Enter apstiprina vārdu
    elif game.state == "enter_name":
        if key == pygame.K_BACKSPACE:
            game.delete_name_character()
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            game.confirm_name()

    # Spēles laikā: atstarpe — izrāviens, E — uzlabojums, F — granāta
    elif game.state == "playing":
        if key == pygame.K_SPACE:
            game.start_dash()
        elif key == pygame.K_e:
            game.use_boost()
        elif key == pygame.K_f:
            game.throw_grenade(mouse_position[0], mouse_position[1])


def handle_event(event, mouse_position, hovered_button):
    if event.type == pygame.QUIT:
        game.running = False

    # Rakstītie burti nonāk vārdā (tikai vārda ekrānā)
    elif event.type == pygame.TEXTINPUT:
        if game.state == "enter_name":
            game.add_name_text(event.text)

    elif event.type == pygame.KEYDOWN:
        handle_key_press(event.key, mouse_position)

    # Kreisais peles klikšķis uz pogas (spēles laikā pogu nav)
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if game.state != "playing" and hovered_button is not None:
            game.click_option(hovered_button)


def handle_playing_input(mouse_position):
    # Kustība: WASD taustiņi dod virzienu -1, 0 vai 1 pa x un y
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

    # Turot kreiso peles pogu, spēle turpina šaut (aizkavi pievieno pati spēle)
    pressed_mouse_buttons = pygame.mouse.get_pressed()
    if pressed_mouse_buttons[0]:
        game.shoot(mouse_position[0], mouse_position[1])


# ---------- Galvenais cikls ----------
while game.running:
    mouse_position = pygame.mouse.get_pos()
    hovered_button = find_hovered_button(mouse_position)

    # Izvēlnēs rāda parasto peles bultiņu, spēles laikā — mērķi
    pygame.mouse.set_visible(game.state != "playing")

    # 1. Ievade
    for event in pygame.event.get():
        handle_event(event, mouse_position, hovered_button)

    # 2. Atjaunināšana
    if game.state == "playing":
        handle_playing_input(mouse_position)
        game.update_game()

        # Spēlētājs tikko gāja bojā, tāpēc rezultātu nosūta serverim (mājaslapa to parāda)
        if game.state == "game_over":
            score_sender.send_score(game.player_name, game.score)
    else:
        game.hover_option(hovered_button)

    # 3. Zīmēšana
    draw_current_screen(screen, mouse_position)
    pygame.display.flip()

    # 4. Pauze (spēle darbojas ar 60 kadriem sekundē)
    clock.tick(60)

pygame.quit()