import math
import os
import random

# Moving diagonally would be faster than moving straight,
# so we multiply by this number to make it equal
DIAGONAL_SLOWDOWN = 0.7071

# The main project folder (the one that holds game and client)
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Small files where the game remembers things between runs
HIGH_SCORE_FILE = os.path.join(PROJECT_FOLDER, "highscore.txt")
PLAYER_NAME_FILE = os.path.join(PROJECT_FOLDER, "player_name.txt")


class Game:
    def __init__(self, screen_width, screen_height):
        # Size of the whole screen (given by the client)
        self.screen_width = screen_width
        self.screen_height = screen_height

        # The bars at the top and bottom hold the information (health, score, ...)
        # The game itself only happens in the play area between them
        self.top_bar_height = 64
        self.bottom_bar_height = 56
        self.play_area_top = self.top_bar_height
        self.play_area_bottom = self.screen_height - self.bottom_bar_height

        # Screens
        self.state = "menu"  # "menu", "enter_name", "playing", "paused", "game_over"
        self.menu_options = ["Start", "Quit"]
        self.name_options = ["Start", "Back"]
        self.pause_options = ["Resume", "Menu"]
        self.game_over_options = ["Play again", "Menu"]
        self.hovered_option = None
        self.running = True

        # The player's name (it is asked for before every game and shown on the website later)
        self.max_name_length = 12
        self.player_name = self.load_player_name()

        # The best score ever reached (it stays between rounds and is saved in a file)
        self.high_score = self.load_high_score()

        # Starting values. Boosts change the current values during a round,
        # and every new round starts again from these numbers
        self.start_max_health = 100
        self.start_bullet_damage = 10  # 3 hits to kill a zombie with 30 health
        self.start_shoot_delay = 13  # frames between two shots (60 frames = 1 second)

        # Player settings
        self.player_size = 30
        self.player_speed = 4

        # Dash settings
        self.dash_speed = 15  # pixels per frame while dashing
        self.dash_time = 10  # frames the dash lasts (10 frames = about 150 pixels)
        self.dash_cooldown_delay = 420  # frames until the dash is ready again (7 seconds)

        # Shooting settings
        self.bullet_speed = 12
        self.bullet_size = 5  # how close a bullet must get to a zombie to hit it
        self.bullet_length = 14  # how long the tic-tac shape is
        self.bullet_thickness = 5  # how wide the tic-tac shape is
        self.shoot_pause_after_click = 15  # frames without shooting after clicking a button, so the click does not fire a bullet

        # Orb settings
        self.orb_radius = 10
        self.orbs_needed = 10  # the player can hold 10 orbs at most
        self.orb_spawn_delay = 180  # frames between two new orbs (3 seconds)
        self.max_orbs_on_map = 5  # no new orbs appear while this many are lying around
        self.orb_edge_margin = 40  # orbs do not appear closer than this to the edge of the play area

        # Boost settings (a boost lasts until the round ends)
        self.boost_names = ["faster_shooting", "stronger_bullets", "more_health"]
        self.boost_damage_amount = 5  # stronger bullets: 10 damage becomes 15, then 20, ...
        self.boost_shoot_delay_amount = 3  # faster shooting: the delay gets 3 frames shorter (13, 10, 7, 4)
        self.minimum_shoot_delay = 4  # the delay never gets shorter than this
        self.boost_health_amount = 20  # more health: max health and current health go up by this
        self.boost_message_delay = 120  # frames the boost message stays on the screen (2 seconds)

        # Grenade settings
        self.grenade_speed = 18  # pixels per frame while it flies to the cursor
        self.grenade_fuse_time = 30  # frames between landing and exploding (half a second)
        self.grenade_radius = 130  # zombies inside this circle die
        self.grenade_size = 8
        self.explosion_time = 20  # frames the explosion picture stays on the screen

        # Zombie settings (these are the values for wave 1)
        self.zombie_size = 30
        self.zombie_health = 30  # 3 hits with 10 damage
        self.zombie_speed = 1.7
        self.zombie_damage = 10  # health the player loses when a zombie touches them

        # How zombies get stronger with every wave
        self.extra_zombie_health = 10  # added every 3 waves
        self.zombie_speed_increase = 0.1  # added every wave
        self.zombie_max_speed = 3.2  # 3.2 * 1.2 = 3.84, still lower than player_speed

        # How zombies spread out instead of forming one big group
        self.zombie_slowest_factor = 0.8  # the slowest zombies walk at 80% of the wave speed
        self.zombie_fastest_factor = 1.2  # the fastest zombies walk at 120% of the wave speed
        self.zombie_flank_distance = 150  # far zombies aim for their own spot this far from the player
        self.zombie_flank_spread = 0.6  # how far the spot can be from the zombie's own side (0.6 = about 35 degrees)
        self.zombie_spacing = 40  # how close two zombies are allowed to get to each other

        # Wave settings
        self.zombies_in_first_wave = 11
        self.extra_zombies_per_wave = 4
        self.wave_spawn_time = 1000  # frames it takes to spawn a whole wave (about 17 seconds)
        self.wave_break_delay = 180  # frames of pause between waves (3 seconds)

        # Score settings
        self.points_per_zombie = 10
        self.points_per_orb = 5
        self.points_per_wave = 100

        # How long the player is safe after being hit (60 frames = 1 second)
        self.hit_pause = 45

        # Everything that changes during a round gets its starting value here
        self.reset_round()

    # ---------- Starting a new round ----------
    def reset_round(self):
        # Boosts (every round starts without boosts)
        self.player_max_health = self.start_max_health
        self.bullet_damage = self.start_bullet_damage
        self.shoot_delay = self.start_shoot_delay
        self.last_boost = None  # the name of the boost the player got last
        self.boost_message_timer = 0  # above 0 while the boost message is on the screen

        # Player (player_x and player_y are the CENTER of the square)
        self.player_x = self.screen_width / 2
        self.player_y = (self.play_area_top + self.play_area_bottom) / 2
        self.player_health = self.player_max_health
        self.hit_timer = 0  # counts down to 0, the player is safe while it is above 0

        # Dash
        self.dash_timer = 0  # above 0 while the player is dashing
        self.dash_cooldown_timer = 0  # above 0 while the dash is recharging
        self.dash_direction_x = 0
        self.dash_direction_y = 0
        self.last_direction_x = 1  # the dash goes this way if the player has not moved yet
        self.last_direction_y = 0

        # Shooting
        self.bullets = []  # every bullet that is flying right now
        self.shoot_timer = 0  # counts down to 0, then we can shoot again

        # Grenades
        self.grenades = []  # every grenade that is flying or waiting to explode
        self.explosions = []  # every explosion that is still on the screen

        # Orbs
        self.orbs = []  # every orb lying on the map right now
        self.orbs_collected = 0  # how many orbs the player holds (0 to 10)
        self.orb_spawn_timer = 0

        # Zombies
        self.zombies = []  # every zombie on the map right now
        self.zombie_spawn_timer = 0
        self.current_zombie_health = self.zombie_health
        self.current_zombie_speed = self.zombie_speed

        # Waves (the round starts with a short break, then wave 1 begins)
        self.wave_number = 1
        self.wave_break_timer = self.wave_break_delay  # while this is above 0, we are in a break
        self.zombies_left_to_spawn = 0
        self.wave_spawn_delay = 60  # frames between two zombies of the same wave

        # Score (we remember the old record, so we can tell at the end if it was beaten)
        self.score = 0
        self.record_at_round_start = self.high_score

    def start_new_round(self):
        self.reset_round()
        self.hovered_option = None
        self.shoot_timer = self.shoot_pause_after_click
        self.state = "playing"

    # ---------- Esc key ----------
    def press_escape(self):
        # While playing, Esc pauses the game, and pressing it again continues
        # On the name screen, Esc goes back to the menu
        # (it does nothing in the menu or on the game over screen)
        if self.state == "playing":
            self.state = "paused"
            self.hovered_option = None
        elif self.state == "paused":
            self.resume_game()
        elif self.state == "enter_name":
            self.state = "menu"
            self.hovered_option = None

    def resume_game(self):
        self.state = "playing"
        self.hovered_option = None
        self.shoot_timer = self.shoot_pause_after_click

    # ---------- Menu, name, pause and game over screens ----------
    def hover_option(self, option_number):
        self.hovered_option = option_number

    def click_option(self, option_number):
        if self.state == "menu":
            if self.menu_options[option_number] == "Start":
                # Before the game starts, the player types a name
                self.state = "enter_name"
                self.hovered_option = None
            else:
                self.running = False

        elif self.state == "enter_name":
            if self.name_options[option_number] == "Start":
                self.confirm_name()
            else:
                self.state = "menu"
                self.hovered_option = None

        elif self.state == "paused":
            if self.pause_options[option_number] == "Resume":
                self.resume_game()
            else:
                self.state = "menu"
                self.hovered_option = None

        elif self.state == "game_over":
            if self.game_over_options[option_number] == "Play again":
                self.start_new_round()
            else:
                self.state = "menu"

    # ---------- Player name ----------
    def add_name_text(self, typed_text):
        # typed_text is what the player just typed (usually one character)
        for character in typed_text:
            # The name has a maximum length
            if len(self.player_name) >= self.max_name_length:
                break

            # Only letters, numbers, spaces and a few simple signs are allowed
            if not (character.isalnum() or character in " _-."):
                continue

            # A name can not start with a space
            if character == " " and len(self.player_name) == 0:
                continue

            self.player_name = self.player_name + character

    def delete_name_character(self):
        # Removes the last character (the Backspace key)
        self.player_name = self.player_name[:-1]

    def confirm_name(self):
        # Spaces at the end do not count as part of the name
        self.player_name = self.player_name.strip()

        # An empty name is not allowed
        if self.player_name == "":
            return

        self.save_player_name()
        self.start_new_round()

    def load_player_name(self):
        # Reads the name the player used last time, so they do not have to type it again
        # If the file does not exist yet, the name is empty
        try:
            with open(PLAYER_NAME_FILE, "r", encoding="utf-8") as name_file:
                return name_file.read().strip()[:self.max_name_length]
        except (OSError, ValueError):
            return ""

    def save_player_name(self):
        # Writes the name to the file
        # If saving does not work, the game just keeps going
        try:
            with open(PLAYER_NAME_FILE, "w", encoding="utf-8") as name_file:
                name_file.write(self.player_name)
        except OSError:
            pass

    # ---------- High score ----------
    def load_high_score(self):
        # Reads the saved best score from the file
        # If the file does not exist yet (or is broken), the best score is 0
        try:
            with open(HIGH_SCORE_FILE, "r") as score_file:
                return int(score_file.read().strip())
        except (OSError, ValueError):
            return 0

    def save_high_score(self):
        # Writes the best score to the file
        # If saving does not work, the game just keeps going
        try:
            with open(HIGH_SCORE_FILE, "w") as score_file:
                score_file.write(str(self.high_score))
        except OSError:
            pass

    def update_high_score(self):
        # Whenever the score gets higher than the record, it becomes the new record
        # We save right away, so the record is safe even if the game is closed
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def is_new_best(self):
        # True if this round beat the record from before the round started
        return self.score > self.record_at_round_start

    # ---------- Update (runs once every frame while playing) ----------
    def update_game(self):
        if self.shoot_timer > 0:
            self.shoot_timer = self.shoot_timer - 1
        if self.hit_timer > 0:
            self.hit_timer = self.hit_timer - 1
        if self.dash_timer > 0:
            self.dash_timer = self.dash_timer - 1
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer = self.dash_cooldown_timer - 1
        if self.boost_message_timer > 0:
            self.boost_message_timer = self.boost_message_timer - 1

        self.move_bullets()
        self.move_zombies()
        self.push_zombies_apart()
        self.check_bullet_hits()
        self.check_zombie_hits_player()

        # The player just died, so there is nothing more to update
        # (the points from the last moment still count for the record)
        if self.state == "game_over":
            self.update_high_score()
            return

        self.spawn_orbs_over_time()
        self.collect_orbs()
        self.update_grenades()
        self.update_explosions()
        self.update_wave()
        self.update_high_score()

    # ---------- Player ----------
    def move_player(self, direction_x, direction_y):
        # direction_x and direction_y are -1, 0 or 1
        # Example: direction_x = -1 means "go left"

        # Remember where the player last walked, because the dash goes that way
        if direction_x != 0 or direction_y != 0:
            self.last_direction_x = direction_x
            self.last_direction_y = direction_y

        # While dashing, the player flies in the dash direction and the keys do nothing
        if self.dash_timer > 0:
            self.player_x = self.player_x + self.dash_direction_x * self.dash_speed
            self.player_y = self.player_y + self.dash_direction_y * self.dash_speed
            self.keep_player_inside_play_area()
            return

        if direction_x != 0 and direction_y != 0:
            direction_x = direction_x * DIAGONAL_SLOWDOWN
            direction_y = direction_y * DIAGONAL_SLOWDOWN

        self.player_x = self.player_x + direction_x * self.player_speed
        self.player_y = self.player_y + direction_y * self.player_speed

        self.keep_player_inside_play_area()

    def keep_player_inside_play_area(self):
        half_size = self.player_size / 2

        if self.player_x < half_size:
            self.player_x = half_size
        if self.player_x > self.screen_width - half_size:
            self.player_x = self.screen_width - half_size

        # The top and bottom walls are the edges of the bars
        if self.player_y < self.play_area_top + half_size:
            self.player_y = self.play_area_top + half_size
        if self.player_y > self.play_area_bottom - half_size:
            self.player_y = self.play_area_bottom - half_size

    def start_dash(self):
        # Can't dash while already dashing or while the dash is recharging
        if self.dash_timer > 0 or self.dash_cooldown_timer > 0:
            return

        # Make the direction exactly 1 long (same trick as shooting),
        # so the dash is equally long in every direction
        direction_length = math.hypot(self.last_direction_x, self.last_direction_y)
        self.dash_direction_x = self.last_direction_x / direction_length
        self.dash_direction_y = self.last_direction_y / direction_length

        self.dash_timer = self.dash_time
        self.dash_cooldown_timer = self.dash_cooldown_delay

    # ---------- Bullets ----------
    def shoot(self, target_x, target_y):
        # Still waiting for the delay to finish
        if self.shoot_timer > 0:
            return

        # How far is the target from the player?
        distance_x = target_x - self.player_x
        distance_y = target_y - self.player_y
        total_distance = math.hypot(distance_x, distance_y)

        # The mouse is exactly on the player, so there is no direction
        if total_distance == 0:
            return

        # Dividing by the total distance makes the direction exactly 1 long,
        # so bullets fly at the same speed in every direction
        # A bullet's x and y are its FRONT. The long tail is drawn behind it
        bullet = {
            "x": self.player_x,
            "y": self.player_y,
            "direction_x": distance_x / total_distance,
            "direction_y": distance_y / total_distance,
        }
        self.bullets.append(bullet)
        self.shoot_timer = self.shoot_delay

    def move_bullets(self):
        bullets_still_flying = []

        for bullet in self.bullets:
            bullet["x"] = bullet["x"] + bullet["direction_x"] * self.bullet_speed
            bullet["y"] = bullet["y"] + bullet["direction_y"] * self.bullet_speed

            # Only keep the bullets that are still in the play area
            if self.is_inside_play_area(bullet["x"], bullet["y"]):
                bullets_still_flying.append(bullet)

        self.bullets = bullets_still_flying

    def is_inside_play_area(self, x, y):
        if x < 0 or x > self.screen_width:
            return False
        if y < self.play_area_top or y > self.play_area_bottom:
            return False
        return True

    # ---------- Orbs ----------
    def spawn_orbs_over_time(self):
        # Enough orbs are lying around already, so wait
        if len(self.orbs) >= self.max_orbs_on_map:
            return

        self.orb_spawn_timer = self.orb_spawn_timer - 1

        if self.orb_spawn_timer <= 0:
            self.spawn_orb()
            self.orb_spawn_timer = self.orb_spawn_delay

    def spawn_orb(self):
        # A random spot in the play area, but not too close to the edge
        orb_x = random.randint(self.orb_edge_margin, self.screen_width - self.orb_edge_margin)
        orb_y = random.randint(
            self.play_area_top + self.orb_edge_margin,
            self.play_area_bottom - self.orb_edge_margin,
        )

        orb = {"x": orb_x, "y": orb_y}
        self.orbs.append(orb)

    def orb_touches_player(self, orb):
        touch_distance = self.player_size / 2 + self.orb_radius

        if abs(orb["x"] - self.player_x) > touch_distance:
            return False
        if abs(orb["y"] - self.player_y) > touch_distance:
            return False
        return True

    def collect_orbs(self):
        orbs_still_lying_around = []

        for orb in self.orbs:
            # The player can only hold 10 orbs, so extra orbs stay on the map
            player_has_room = self.orbs_collected < self.orbs_needed

            if player_has_room and self.orb_touches_player(orb):
                self.orbs_collected = self.orbs_collected + 1
                self.score = self.score + self.points_per_orb
            else:
                orbs_still_lying_around.append(orb)

        self.orbs = orbs_still_lying_around

    # ---------- Boosts (E key) ----------
    def use_boost(self):
        # Only works when all 10 orbs are collected
        if self.orbs_collected < self.orbs_needed:
            return

        # Make a list of the boosts that can still help
        # Once shooting is as fast as it can get, that boost is left out
        shooting_is_maxed = self.shoot_delay <= self.minimum_shoot_delay

        available_boosts = []
        for possible_boost in self.boost_names:
            if possible_boost == "faster_shooting" and shooting_is_maxed:
                continue
            available_boosts.append(possible_boost)

        boost_name = random.choice(available_boosts)

        if boost_name == "faster_shooting":
            self.shoot_delay = self.shoot_delay - self.boost_shoot_delay_amount
            if self.shoot_delay < self.minimum_shoot_delay:
                self.shoot_delay = self.minimum_shoot_delay

        elif boost_name == "stronger_bullets":
            self.bullet_damage = self.bullet_damage + self.boost_damage_amount

        else:
            # More health: the maximum goes up and the player is healed by the same amount
            self.player_max_health = self.player_max_health + self.boost_health_amount
            self.player_health = self.player_health + self.boost_health_amount

        # The orbs are used up, and the client shows a message about the boost
        self.orbs_collected = 0
        self.last_boost = boost_name
        self.boost_message_timer = self.boost_message_delay

    # ---------- Grenades (F key) ----------
    def throw_grenade(self, target_x, target_y):
        # Only works when all 10 orbs are collected
        if self.orbs_collected < self.orbs_needed:
            return

        # The grenade can only land in the play area, not on the bars
        if target_y < self.play_area_top:
            target_y = self.play_area_top
        if target_y > self.play_area_bottom:
            target_y = self.play_area_bottom

        grenade = {
            "x": self.player_x,
            "y": self.player_y,
            "target_x": target_x,
            "target_y": target_y,
            "landed": False,
            "fuse_timer": self.grenade_fuse_time,
        }
        self.grenades.append(grenade)
        self.orbs_collected = 0

    def update_grenades(self):
        grenades_still_waiting = []

        for grenade in self.grenades:
            if grenade["landed"]:
                grenade["fuse_timer"] = grenade["fuse_timer"] - 1
            else:
                self.move_grenade(grenade)

            if grenade["landed"] and grenade["fuse_timer"] <= 0:
                self.explode_grenade(grenade)
            else:
                grenades_still_waiting.append(grenade)

        self.grenades = grenades_still_waiting

    def move_grenade(self, grenade):
        distance_x = grenade["target_x"] - grenade["x"]
        distance_y = grenade["target_y"] - grenade["y"]
        total_distance = math.hypot(distance_x, distance_y)

        # Close enough to the target, so the grenade lands there
        if total_distance <= self.grenade_speed:
            grenade["x"] = grenade["target_x"]
            grenade["y"] = grenade["target_y"]
            grenade["landed"] = True
            return

        grenade["x"] = grenade["x"] + distance_x / total_distance * self.grenade_speed
        grenade["y"] = grenade["y"] + distance_y / total_distance * self.grenade_speed

    def explode_grenade(self, grenade):
        # Every zombie inside the circle dies, and we get points for each one
        zombies_still_alive = []

        for zombie in self.zombies:
            distance_to_grenade = math.hypot(zombie["x"] - grenade["x"], zombie["y"] - grenade["y"])

            if distance_to_grenade <= self.grenade_radius:
                self.score = self.score + self.points_per_zombie
            else:
                zombies_still_alive.append(zombie)

        self.zombies = zombies_still_alive

        # The client draws a short explosion picture here
        explosion = {"x": grenade["x"], "y": grenade["y"], "timer": self.explosion_time}
        self.explosions.append(explosion)

    def update_explosions(self):
        explosions_still_visible = []

        for explosion in self.explosions:
            explosion["timer"] = explosion["timer"] - 1
            if explosion["timer"] > 0:
                explosions_still_visible.append(explosion)

        self.explosions = explosions_still_visible

    # ---------- Waves ----------
    def update_wave(self):
        # During the break we only count down, and then the next wave starts
        if self.wave_break_timer > 0:
            self.wave_break_timer = self.wave_break_timer - 1
            if self.wave_break_timer == 0:
                self.start_wave()
            return

        self.spawn_zombies_over_time()

        # The wave is over when nothing is left to spawn and every zombie is dead
        if self.zombies_left_to_spawn == 0 and len(self.zombies) == 0:
            self.finish_wave()

    def start_wave(self):
        # More zombies in every wave
        zombie_count = self.zombies_in_first_wave + (self.wave_number - 1) * self.extra_zombies_per_wave
        self.zombies_left_to_spawn = zombie_count

        # Spread the zombies over the spawn time (but never faster than one every 10 frames)
        self.wave_spawn_delay = max(10, self.wave_spawn_time // zombie_count)
        self.zombie_spawn_timer = 0  # the first zombie comes right away

        # Tougher zombies: +health every 3 waves (// throws away the decimals)
        waves_with_extra_health = (self.wave_number - 1) // 3
        self.current_zombie_health = self.zombie_health + self.extra_zombie_health * waves_with_extra_health

        # Faster zombies: +speed every wave, up to the maximum
        faster_speed = self.zombie_speed + self.zombie_speed_increase * (self.wave_number - 1)
        self.current_zombie_speed = min(faster_speed, self.zombie_max_speed)

    def finish_wave(self):
        self.score = self.score + self.points_per_wave
        self.wave_number = self.wave_number + 1
        self.wave_break_timer = self.wave_break_delay

    # ---------- Zombies ----------
    def spawn_zombies_over_time(self):
        if self.zombies_left_to_spawn <= 0:
            return

        self.zombie_spawn_timer = self.zombie_spawn_timer - 1

        if self.zombie_spawn_timer <= 0:
            self.spawn_zombie()
            self.zombies_left_to_spawn = self.zombies_left_to_spawn - 1
            self.zombie_spawn_timer = self.wave_spawn_delay

    def spawn_zombie(self):
        # Zombies appear just outside the play area, on a random side
        # (at the top and bottom that is behind the bars, so you can not see them appear)
        margin = 40
        side = random.choice(["top", "bottom", "left", "right"])

        if side == "top":
            spawn_x = random.randint(0, self.screen_width)
            spawn_y = self.play_area_top - margin
        elif side == "bottom":
            spawn_x = random.randint(0, self.screen_width)
            spawn_y = self.play_area_bottom + margin
        elif side == "left":
            spawn_x = -margin
            spawn_y = random.randint(self.play_area_top, self.play_area_bottom)
        else:
            spawn_x = self.screen_width + margin
            spawn_y = random.randint(self.play_area_top, self.play_area_bottom)

        # Every zombie gets its own speed, so they do not all arrive together
        speed_factor = random.uniform(self.zombie_slowest_factor, self.zombie_fastest_factor)

        # Every zombie also gets its own spot around the player.
        # The spot is on the same side the zombie comes from, with a small random spread,
        # so the zombies walk roughly straight at the player and do not wander around
        angle_to_zombie = math.atan2(spawn_y - self.player_y, spawn_x - self.player_x)
        flank_angle = angle_to_zombie + random.uniform(-self.zombie_flank_spread, self.zombie_flank_spread)

        zombie = {
            "x": spawn_x,
            "y": spawn_y,
            "health": self.current_zombie_health,
            "speed": self.current_zombie_speed * speed_factor,
            "flank_x": math.cos(flank_angle) * self.zombie_flank_distance,
            "flank_y": math.sin(flank_angle) * self.zombie_flank_distance,
        }
        self.zombies.append(zombie)

    def move_zombies(self):
        for zombie in self.zombies:
            distance_to_player = math.hypot(self.player_x - zombie["x"], self.player_y - zombie["y"])

            # Far away: walk to this zombie's own spot next to the player
            # Close by: walk straight at the player
            if distance_to_player > self.zombie_flank_distance:
                target_x = self.player_x + zombie["flank_x"]
                target_y = self.player_y + zombie["flank_y"]
            else:
                target_x = self.player_x
                target_y = self.player_y

            # Same idea as shooting: find the direction to the target
            distance_x = target_x - zombie["x"]
            distance_y = target_y - zombie["y"]
            total_distance = math.hypot(distance_x, distance_y)

            # The zombie is exactly on its target, so there is nowhere to walk
            if total_distance == 0:
                continue

            zombie["x"] = zombie["x"] + distance_x / total_distance * zombie["speed"]
            zombie["y"] = zombie["y"] + distance_y / total_distance * zombie["speed"]

    def push_zombies_apart(self):
        # Every pair of zombies that is too close pushes each other away,
        # so they do not stack on top of each other
        minimum_distance = self.zombie_spacing

        for first_number in range(len(self.zombies)):
            for second_number in range(first_number + 1, len(self.zombies)):
                first_zombie = self.zombies[first_number]
                second_zombie = self.zombies[second_number]

                distance_x = second_zombie["x"] - first_zombie["x"]
                distance_y = second_zombie["y"] - first_zombie["y"]
                total_distance = math.hypot(distance_x, distance_y)

                # These two are far enough apart
                if total_distance >= minimum_distance:
                    continue

                # They are on exactly the same spot, so push them in a random direction
                if total_distance == 0:
                    angle = random.uniform(0, 2 * math.pi)
                    distance_x = math.cos(angle)
                    distance_y = math.sin(angle)
                    total_distance = 1

                # Each zombie moves away by half of the overlap
                overlap = minimum_distance - total_distance
                push_x = distance_x / total_distance * overlap / 2
                push_y = distance_y / total_distance * overlap / 2

                first_zombie["x"] = first_zombie["x"] - push_x
                first_zombie["y"] = first_zombie["y"] - push_y
                second_zombie["x"] = second_zombie["x"] + push_x
                second_zombie["y"] = second_zombie["y"] + push_y

    # ---------- Bullets hitting zombies ----------
    def bullet_touches_zombie(self, bullet, zombie):
        # The zombie is a square, so the bullet touches it when it is close enough
        # on both the x side and the y side
        touch_distance = self.zombie_size / 2 + self.bullet_size

        if abs(bullet["x"] - zombie["x"]) > touch_distance:
            return False
        if abs(bullet["y"] - zombie["y"]) > touch_distance:
            return False
        return True

    def check_bullet_hits(self):
        # Step 1: every bullet that touches a zombie damages it and disappears
        bullets_that_missed = []

        for bullet in self.bullets:
            bullet_hit_a_zombie = False

            for zombie in self.zombies:
                if self.bullet_touches_zombie(bullet, zombie):
                    zombie["health"] = zombie["health"] - self.bullet_damage
                    bullet_hit_a_zombie = True
                    break  # one bullet can only hit one zombie

            if not bullet_hit_a_zombie:
                bullets_that_missed.append(bullet)

        self.bullets = bullets_that_missed

        # Step 2: zombies with no health left die, and we get points for each
        zombies_still_alive = []

        for zombie in self.zombies:
            if zombie["health"] > 0:
                zombies_still_alive.append(zombie)
            else:
                self.score = self.score + self.points_per_zombie

        self.zombies = zombies_still_alive

    # ---------- Zombies hitting the player ----------
    def zombie_touches_player(self, zombie):
        # Both are squares, so they touch when they are close enough
        # on both the x side and the y side
        touch_distance = (self.player_size + self.zombie_size) / 2

        if abs(zombie["x"] - self.player_x) > touch_distance:
            return False
        if abs(zombie["y"] - self.player_y) > touch_distance:
            return False
        return True

    def check_zombie_hits_player(self):
        # The player is safe while the pause after the last hit is still running
        if self.hit_timer > 0:
            return

        # The player is also safe while dashing
        if self.dash_timer > 0:
            return

        for zombie in self.zombies:
            if self.zombie_touches_player(zombie):
                self.player_health = self.player_health - self.zombie_damage
                self.hit_timer = self.hit_pause
                break  # only one hit at a time, even if several zombies touch

        if self.player_health <= 0:
            self.player_health = 0
            self.hit_timer = 0
            self.state = "game_over"