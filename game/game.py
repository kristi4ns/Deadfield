import math
import random

# Moving diagonally would be faster than moving straight,
# so we multiply by this number to make it equal
DIAGONAL_SLOWDOWN = 0.7071


class Game:
    def __init__(self, screen_width, screen_height):
        # Size of the play area (given by the client)
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Screens
        self.state = "menu"  # "menu", "playing", "game_over"
        self.menu_options = ["Start", "Quit"]
        self.game_over_options = ["Play again", "Menu"]
        self.hovered_option = None
        self.running = True

        # Player settings
        self.player_size = 30
        self.player_speed = 4
        self.player_max_health = 100

        # Shooting settings
        self.bullet_speed = 12
        self.bullet_size = 5
        self.bullet_damage = 10  # the strength boost will raise this later
        self.shoot_delay = 13  # frames between two shots (60 frames = 1 second)

        # Zombie settings (these are the values for wave 1)
        self.zombie_size = 30
        self.zombie_health = 30  # 3 hits with 10 damage
        self.zombie_speed = 1.7
        self.zombie_damage = 10  # health the player loses when a zombie touches them

        # How zombies get stronger with every wave
        self.extra_zombie_health = 10  # added every 3 waves
        self.zombie_speed_increase = 0.1  # added every wave
        self.zombie_max_speed = 3.2  # keep this lower than player_speed

        # Wave settings
        self.zombies_in_first_wave = 11
        self.extra_zombies_per_wave = 4
        self.wave_spawn_time = 1000  # frames it takes to spawn a whole wave (about 17 seconds)
        self.wave_break_delay = 180  # frames of pause between waves (3 seconds)

        # Score settings
        self.points_per_zombie = 10
        self.points_per_wave = 100

        # How long the player is safe after being hit (60 frames = 1 second)
        self.hit_pause = 45

        # Everything that changes during a round gets its starting value here
        self.reset_round()

    # ---------- Starting a new round ----------
    def reset_round(self):
        # Player (player_x and player_y are the CENTER of the square)
        self.player_x = self.screen_width / 2
        self.player_y = self.screen_height / 2
        self.player_health = self.player_max_health
        self.hit_timer = 0  # counts down to 0, the player is safe while it is above 0

        # Shooting
        self.bullets = []  # every bullet that is flying right now
        self.shoot_timer = 0  # counts down to 0, then we can shoot again

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

        # Score
        self.score = 0

    def start_new_round(self):
        self.reset_round()
        self.hovered_option = None
        self.state = "playing"

    # ---------- Menu and game over screen ----------
    def hover_option(self, option_number):
        self.hovered_option = option_number

    def click_option(self, option_number):
        if self.state == "menu":
            if self.menu_options[option_number] == "Start":
                self.start_new_round()
            else:
                self.running = False

        elif self.state == "game_over":
            if self.game_over_options[option_number] == "Play again":
                self.start_new_round()
            else:
                self.state = "menu"

    # ---------- Update (runs once every frame while playing) ----------
    def update_game(self):
        if self.shoot_timer > 0:
            self.shoot_timer = self.shoot_timer - 1
        if self.hit_timer > 0:
            self.hit_timer = self.hit_timer - 1

        self.move_bullets()
        self.move_zombies()
        self.check_bullet_hits()
        self.check_zombie_hits_player()

        # The player just died, so there is nothing more to update
        if self.state == "game_over":
            return

        self.update_wave()

    # ---------- Player ----------
    def move_player(self, direction_x, direction_y):
        # direction_x and direction_y are -1, 0 or 1
        # Example: direction_x = -1 means "go left"

        if direction_x != 0 and direction_y != 0:
            direction_x = direction_x * DIAGONAL_SLOWDOWN
            direction_y = direction_y * DIAGONAL_SLOWDOWN

        self.player_x = self.player_x + direction_x * self.player_speed
        self.player_y = self.player_y + direction_y * self.player_speed

        self.keep_player_inside_screen()

    def keep_player_inside_screen(self):
        half_size = self.player_size / 2

        if self.player_x < half_size:
            self.player_x = half_size
        if self.player_x > self.screen_width - half_size:
            self.player_x = self.screen_width - half_size

        if self.player_y < half_size:
            self.player_y = half_size
        if self.player_y > self.screen_height - half_size:
            self.player_y = self.screen_height - half_size

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

            # Only keep the bullets that are still on the screen
            if self.is_inside_screen(bullet["x"], bullet["y"]):
                bullets_still_flying.append(bullet)

        self.bullets = bullets_still_flying

    def is_inside_screen(self, x, y):
        if x < 0 or x > self.screen_width:
            return False
        if y < 0 or y > self.screen_height:
            return False
        return True

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
        # Zombies appear just outside the screen, on a random side
        margin = 40
        side = random.choice(["top", "bottom", "left", "right"])

        if side == "top":
            spawn_x = random.randint(0, self.screen_width)
            spawn_y = -margin
        elif side == "bottom":
            spawn_x = random.randint(0, self.screen_width)
            spawn_y = self.screen_height + margin
        elif side == "left":
            spawn_x = -margin
            spawn_y = random.randint(0, self.screen_height)
        else:
            spawn_x = self.screen_width + margin
            spawn_y = random.randint(0, self.screen_height)

        zombie = {"x": spawn_x, "y": spawn_y, "health": self.current_zombie_health}
        self.zombies.append(zombie)

    def move_zombies(self):
        for zombie in self.zombies:
            # Same idea as shooting: find the direction to the player
            distance_x = self.player_x - zombie["x"]
            distance_y = self.player_y - zombie["y"]
            total_distance = math.hypot(distance_x, distance_y)

            # The zombie is exactly on the player, so there is nowhere to walk
            if total_distance == 0:
                continue

            zombie["x"] = zombie["x"] + distance_x / total_distance * self.current_zombie_speed
            zombie["y"] = zombie["y"] + distance_y / total_distance * self.current_zombie_speed

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

        for zombie in self.zombies:
            if self.zombie_touches_player(zombie):
                self.player_health = self.player_health - self.zombie_damage
                self.hit_timer = self.hit_pause
                break  # only one hit at a time, even if several zombies touch

        if self.player_health <= 0:
            self.player_health = 0
            self.hit_timer = 0
            self.state = "game_over"