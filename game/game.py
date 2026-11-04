import math
import os
import random

# Pa diagonāli kustoties spēlētājs būtu ātrāks nekā taisni,
# tāpēc ātrumu reizinām ar šo skaitli (1 dalīts ar √2)
DIAGONAL_SLOWDOWN = 0.7071

# Galvenā projekta mape (tā, kurā atrodas game un client)
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Faili, kuros spēle atceras datus starp palaišanas reizēm
HIGH_SCORE_FILE = os.path.join(PROJECT_FOLDER, "highscore.txt")
PLAYER_NAME_FILE = os.path.join(PROJECT_FOLDER, "player_name.txt")


def is_close(first_x, first_y, second_x, second_y, touch_distance):
    # Divi objekti pieskaras, ja to centri gan pa x, gan pa y ir pietiekami tuvu
    if abs(first_x - second_x) > touch_distance:
        return False
    if abs(first_y - second_y) > touch_distance:
        return False
    return True


def read_text_file(file_path):
    # Nolasa teksta failu. Ja faila vēl nav, atgriež tukšu tekstu
    try:
        with open(file_path, "r", encoding="utf-8") as text_file:
            return text_file.read().strip()
    except (OSError, ValueError):
        return ""


def write_text_file(file_path, text):
    # Ieraksta tekstu failā. Ja neizdodas, spēle vienkārši turpina darbu
    try:
        with open(file_path, "w", encoding="utf-8") as text_file:
            text_file.write(text)
    except OSError:
        pass


class Game:
    def __init__(self, screen_width, screen_height):
        # Visa ekrāna izmērs (to iedod client)
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Joslas augšā un apakšā rāda informāciju (veselība, rezultāts, ...)
        # Pati spēle notiek tikai spēles laukumā starp tām
        self.top_bar_height = 64
        self.bottom_bar_height = 56
        self.play_area_top = self.top_bar_height
        self.play_area_bottom = self.screen_height - self.bottom_bar_height

        # Ekrāni
        self.state = "menu"  # "menu", "enter_name", "playing", "paused", "game_over"
        self.menu_options = ["Start", "Quit"]
        self.name_options = ["Start", "Back"]
        self.pause_options = ["Resume", "Menu"]
        self.game_over_options = ["Play again", "Menu"]
        self.hovered_option = None
        self.running = True

        # Spēlētāja vārds (to jautā pirms katras spēles, un vēlāk to rāda mājaslapā)
        self.max_name_length = 12
        self.player_name = read_text_file(PLAYER_NAME_FILE)[:self.max_name_length]

        # Labākais rezultāts, kāds jebkad sasniegts (tas saglabājas failā)
        saved_score = read_text_file(HIGH_SCORE_FILE)
        if saved_score.isdigit():
            self.high_score = int(saved_score)
        else:
            self.high_score = 0

        # Sākuma vērtības. Uzlabojumi maina pašreizējās vērtības raunda laikā,
        # un katrs jauns raunds sākas no šiem skaitļiem
        self.start_max_health = 100
        self.start_bullet_damage = 10  # 3 sitieni, lai nogalinātu zombiju ar 30 dzīvībām
        self.start_shoot_delay = 13  # kadri starp diviem šāvieniem (60 kadri = 1 sekunde)

        # Spēlētāja iestatījumi
        self.player_size = 30
        self.player_speed = 4

        # Izrāviena (dash) iestatījumi
        self.dash_speed = 15  # pikseļi kadrā izrāviena laikā
        self.dash_time = 10  # kadri, cik ilgi izrāviens ilgst (apmēram 150 pikseļi)
        self.dash_cooldown_delay = 420  # kadri līdz nākamajam izrāvienam (7 sekundes)

        # Šaušanas iestatījumi
        self.bullet_speed = 12
        self.bullet_size = 5  # cik tuvu zombijam jānonāk lodei, lai trāpītu
        self.bullet_length = 14  # cik gara ir "tic-tac" formas lode
        self.bullet_thickness = 5  # cik plata ir lode
        self.shoot_pause_after_click = 15  # kadri bez šaušanas pēc pogas klikšķa

        # Orbu iestatījumi
        self.orb_radius = 10
        self.orbs_needed = 10  # spēlētājs var nēsāt ne vairāk kā 10 orbus
        self.orb_spawn_delay = 180  # kadri starp diviem jauniem orbiem (3 sekundes)
        self.max_orbs_on_map = 5  # kamēr uz kartes ir tik daudz, jauni neparādās
        self.orb_edge_margin = 40  # orbi neparādās tuvāk laukuma malai par šo

        # Uzlabojumu iestatījumi (uzlabojums ilgst līdz raunda beigām)
        self.boost_names = ["faster_shooting", "stronger_bullets", "more_health"]
        self.boost_damage_amount = 5  # stiprākas lodes: 10 kaitējums kļūst 15, tad 20, ...
        self.boost_shoot_delay_amount = 3  # ātrāka šaušana: aizkave samazinās par 3 kadriem
        self.minimum_shoot_delay = 4  # aizkave nekad nekļūst mazāka par šo
        self.boost_health_amount = 20  # vairāk veselības: maksimums un pašreizējā veselība aug par šo
        self.boost_message_delay = 120  # kadri, cik ilgi uzlabojuma ziņa ir redzama (2 sekundes)

        # Granātas iestatījumi
        self.grenade_speed = 18  # pikseļi kadrā, kamēr tā lido uz kursoru
        self.grenade_fuse_time = 30  # kadri no nolaišanās līdz sprādzienam (pussekunde)
        self.grenade_radius = 130  # zombiji šajā aplī iet bojā
        self.grenade_size = 8
        self.explosion_time = 20  # kadri, cik ilgi sprādziena attēls ir redzams

        # Zombiju iestatījumi (šīs ir 1. viļņa vērtības)
        self.zombie_size = 30
        self.zombie_health = 30  # 3 sitieni ar 10 kaitējumu
        self.zombie_speed = 1.7
        self.zombie_damage = 10  # cik veselības zaudē spēlētājs, kad zombijs pieskaras

        # Kā zombiji kļūst stiprāki ar katru vilni
        self.extra_zombie_health = 10  # pieskaita ik pēc 3 viļņiem
        self.zombie_speed_increase = 0.1  # pieskaita katrā vilnī
        self.zombie_max_speed = 3.2  # 3.2 * 1.2 = 3.84, vēl joprojām lēnāk par spēlētāju

        # Kā zombiji izklīst, nevis veido vienu lielu bariņu
        self.zombie_slowest_factor = 0.8  # lēnākie iet ar 80% no viļņa ātruma
        self.zombie_fastest_factor = 1.2  # ātrākie iet ar 120% no viļņa ātruma
        self.zombie_flank_distance = 150  # tālie zombiji mērķē uz savu vietu šādā attālumā no spēlētāja
        self.zombie_flank_spread = 0.6  # cik tālu vieta var būt no zombija puses (0.6 ≈ 35 grādi)
        self.zombie_spacing = 40  # cik tuvu viens otram drīkst nonākt zombiji

        # Viļņu iestatījumi
        self.zombies_in_first_wave = 11
        self.extra_zombies_per_wave = 4
        self.wave_spawn_time = 1000  # kadri, cik ilgi visi viļņa zombiji parādās (ap 17 sekundēm)
        self.wave_break_delay = 180  # kadri pauzei starp viļņiem (3 sekundes)

        # Punktu iestatījumi
        self.points_per_zombie = 10
        self.points_per_orb = 5
        self.points_per_wave = 100

        # Cik ilgi spēlētājs ir drošībā pēc trāpījuma (60 kadri = 1 sekunde)
        self.hit_pause = 45

        # Viss, kas mainās raunda laikā, saņem sākuma vērtību šeit
        self.reset_round()

    # ---------- Jauna raunda sākšana ----------
    def reset_round(self):
        # Uzlabojumi (katrs raunds sākas bez uzlabojumiem)
        self.player_max_health = self.start_max_health
        self.bullet_damage = self.start_bullet_damage
        self.shoot_delay = self.start_shoot_delay
        self.last_boost = None  # pēdējā saņemtā uzlabojuma nosaukums
        self.boost_message_timer = 0  # virs 0, kamēr uzlabojuma ziņa ir redzama

        # Spēlētājs (player_x un player_y ir kvadrāta CENTRS)
        self.player_x = self.screen_width / 2
        self.player_y = (self.play_area_top + self.play_area_bottom) / 2
        self.player_health = self.player_max_health
        self.hit_timer = 0  # skaita līdz 0, kamēr tas ir virs 0, spēlētājs ir drošībā

        # Izrāviens
        self.dash_timer = 0  # virs 0, kamēr spēlētājs izdara izrāvienu
        self.dash_cooldown_timer = 0  # virs 0, kamēr izrāviens atjaunojas
        self.dash_direction_x = 0
        self.dash_direction_y = 0
        self.last_direction_x = 1  # izrāviens iet šajā virzienā, ja spēlētājs vēl nav kustējies
        self.last_direction_y = 0

        # Šaušana
        self.bullets = []  # visas lodes, kas pašlaik lido
        self.shoot_timer = 0  # skaita līdz 0, tad atkal var šaut

        # Granātas
        self.grenades = []  # visas granātas, kas lido vai gaida sprādzienu
        self.explosions = []  # visi sprādzieni, kas vēl ir uz ekrāna

        # Orbi
        self.orbs = []  # visi orbi, kas pašlaik guļ uz kartes
        self.orbs_collected = 0  # cik orbus spēlētājs tur (no 0 līdz 10)
        self.orb_spawn_timer = 0

        # Zombiji
        self.zombies = []  # visi zombiji uz kartes
        self.zombie_spawn_timer = 0
        self.current_zombie_health = self.zombie_health
        self.current_zombie_speed = self.zombie_speed

        # Viļņi (raunds sākas ar īsu pauzi, tad sākas 1. vilnis)
        self.wave_number = 1
        self.wave_break_timer = self.wave_break_delay  # kamēr tas ir virs 0, ir pauze
        self.zombies_left_to_spawn = 0
        self.wave_spawn_delay = 60  # kadri starp diviem viena viļņa zombijiem

        # Rezultāts (atceramies veco rekordu, lai beigās zinātu, vai tas pārspēts)
        self.score = 0
        self.record_at_round_start = self.high_score

    def start_new_round(self):
        self.reset_round()
        self.hovered_option = None
        self.shoot_timer = self.shoot_pause_after_click
        self.state = "playing"

    # ---------- Esc taustiņš ----------
    def press_escape(self):
        # Spēles laikā Esc pauzē spēli, un vēlreiz nospiests turpina to
        # Vārda ekrānā Esc atgriež uz izvēlni
        # (izvēlnē un game over ekrānā tas neko nedara)
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

    # ---------- Izvēlne, vārda, pauzes un game over ekrāni ----------
    def hover_option(self, option_number):
        self.hovered_option = option_number

    def click_option(self, option_number):
        if self.state == "menu":
            if self.menu_options[option_number] == "Start":
                # Pirms spēles sākuma spēlētājs ievada vārdu
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

    # ---------- Spēlētāja vārds ----------
    def add_name_text(self, typed_text):
        # typed_text ir tas, ko spēlētājs tikko uzrakstīja (parasti viens burts)
        for character in typed_text:
            # Vārdam ir maksimālais garums
            if len(self.player_name) >= self.max_name_length:
                break

            # Atļauti tikai burti, cipari, atstarpe un dažas vienkāršas zīmes
            if not (character.isalnum() or character in " _-."):
                continue

            # Vārds nedrīkst sākties ar atstarpi
            if character == " " and len(self.player_name) == 0:
                continue

            self.player_name = self.player_name + character

    def delete_name_character(self):
        # Izdzēš pēdējo burtu (Backspace taustiņš)
        self.player_name = self.player_name[:-1]

    def confirm_name(self):
        # Atstarpes vārda beigās nav vārda daļa
        self.player_name = self.player_name.strip()

        # Tukšs vārds nav atļauts
        if self.player_name == "":
            return

        write_text_file(PLAYER_NAME_FILE, self.player_name)
        self.start_new_round()

    # ---------- Labākais rezultāts ----------
    def update_high_score(self):
        # Kad rezultāts pārsniedz rekordu, tas kļūst par jauno rekordu
        # Saglabājam uzreiz, lai rekords nepazustu, ja spēli aizver pēkšņi
        if self.score > self.high_score:
            self.high_score = self.score
            write_text_file(HIGH_SCORE_FILE, str(self.high_score))

    def is_new_best(self):
        # Patiess, ja šajā raundā pārspēts rekords, kāds bija pirms raunda
        return self.score > self.record_at_round_start

    # ---------- Atjaunināšana (darbojas katru kadru, kamēr notiek spēle) ----------
    def update_game(self):
        # Visi atpakaļskaitīšanas taimeri katrā kadrā samazinās par 1, bet ne zem 0
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

        # Spēlētājs tikko gāja bojā, tāpēc vairs nav ko atjaunināt
        # (pēdējā brīža punkti rekordam joprojām skaitās)
        if self.state == "game_over":
            self.update_high_score()
            return

        self.spawn_orbs_over_time()
        self.collect_orbs()
        self.update_grenades()
        self.update_explosions()
        self.update_wave()
        self.update_high_score()

    # ---------- Spēlētājs ----------
    def move_player(self, direction_x, direction_y):
        # direction_x un direction_y ir -1, 0 vai 1
        # Piemērs: direction_x = -1 nozīmē "iet pa kreisi"

        # Atceramies, kurp spēlētājs gāja pēdējo reizi, jo izrāviens iet turp
        if direction_x != 0 or direction_y != 0:
            self.last_direction_x = direction_x
            self.last_direction_y = direction_y

        # Izrāviena laikā spēlētājs lido izrāviena virzienā, un taustiņi neko nedara
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

        # Augšējā un apakšējā siena ir joslu malas
        if self.player_y < self.play_area_top + half_size:
            self.player_y = self.play_area_top + half_size
        if self.player_y > self.play_area_bottom - half_size:
            self.player_y = self.play_area_bottom - half_size

    def start_dash(self):
        # Nevar izrauties, ja jau notiek izrāviens vai tas vēl atjaunojas
        if self.dash_timer > 0 or self.dash_cooldown_timer > 0:
            return

        # Virziena garumu pārvēršam par tieši 1 (tāpat kā šaujot),
        # lai izrāviens visos virzienos būtu vienāds
        direction_length = math.hypot(self.last_direction_x, self.last_direction_y)
        self.dash_direction_x = self.last_direction_x / direction_length
        self.dash_direction_y = self.last_direction_y / direction_length

        self.dash_timer = self.dash_time
        self.dash_cooldown_timer = self.dash_cooldown_delay

    # ---------- Lodes ----------
    def shoot(self, target_x, target_y):
        # Vēl jāgaida, līdz aizkave beidzas
        if self.shoot_timer > 0:
            return

        # Cik tālu mērķis ir no spēlētāja?
        distance_x = target_x - self.player_x
        distance_y = target_y - self.player_y
        total_distance = math.hypot(distance_x, distance_y)

        # Pele ir tieši uz spēlētāja, tāpēc nav virziena
        if total_distance == 0:
            return

        # Dalot ar kopējo attālumu, virziena garums kļūst tieši 1,
        # tāpēc lodes visos virzienos lido ar vienādu ātrumu
        # Lodes x un y ir tās PRIEKŠGALS, bet garā aste tiek zīmēta aiz tā
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

            # Paturam tikai lodes, kas vēl ir spēles laukumā
            if self.is_inside_play_area(bullet["x"], bullet["y"]):
                bullets_still_flying.append(bullet)

        self.bullets = bullets_still_flying

    def is_inside_play_area(self, x, y):
        if x < 0 or x > self.screen_width:
            return False
        if y < self.play_area_top or y > self.play_area_bottom:
            return False
        return True

    # ---------- Orbi ----------
    def spawn_orbs_over_time(self):
        # Uz kartes jau guļ pietiekami daudz orbu, tāpēc gaidām
        if len(self.orbs) >= self.max_orbs_on_map:
            return

        self.orb_spawn_timer = self.orb_spawn_timer - 1

        if self.orb_spawn_timer <= 0:
            self.spawn_orb()
            self.orb_spawn_timer = self.orb_spawn_delay

    def spawn_orb(self):
        # Nejauša vieta spēles laukumā, bet ne pārāk tuvu malai
        orb_x = random.randint(self.orb_edge_margin, self.screen_width - self.orb_edge_margin)
        orb_y = random.randint(
            self.play_area_top + self.orb_edge_margin,
            self.play_area_bottom - self.orb_edge_margin,
        )

        orb = {"x": orb_x, "y": orb_y}
        self.orbs.append(orb)

    def collect_orbs(self):
        touch_distance = self.player_size / 2 + self.orb_radius
        orbs_still_lying_around = []

        for orb in self.orbs:
            # Spēlētājs var nēsāt tikai 10 orbus, tāpēc lieki orbi paliek uz kartes
            player_has_room = self.orbs_collected < self.orbs_needed
            player_touches_orb = is_close(
                orb["x"], orb["y"], self.player_x, self.player_y, touch_distance
            )

            if player_has_room and player_touches_orb:
                self.orbs_collected = self.orbs_collected + 1
                self.score = self.score + self.points_per_orb
            else:
                orbs_still_lying_around.append(orb)

        self.orbs = orbs_still_lying_around

    # ---------- Uzlabojumi (E taustiņš) ----------
    def use_boost(self):
        # Darbojas tikai tad, kad savākti visi 10 orbi
        if self.orbs_collected < self.orbs_needed:
            return

        # Sastādām sarakstu ar uzlabojumiem, kas vēl var palīdzēt
        # Kad šaušana jau ir pēc iespējas ātra, šo uzlabojumu izlaižam
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
            # Vairāk veselības: maksimums aug, un spēlētājs tiek dziedināts par tikpat
            self.player_max_health = self.player_max_health + self.boost_health_amount
            self.player_health = self.player_health + self.boost_health_amount

        # Orbi ir iztērēti, un client parāda ziņu par uzlabojumu
        self.orbs_collected = 0
        self.last_boost = boost_name
        self.boost_message_timer = self.boost_message_delay

    # ---------- Granātas (F taustiņš) ----------
    def throw_grenade(self, target_x, target_y):
        # Darbojas tikai tad, kad savākti visi 10 orbi
        if self.orbs_collected < self.orbs_needed:
            return

        # Granāta var nokrist tikai spēles laukumā, nevis uz joslām
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

        # Pietiekami tuvu mērķim, tāpēc granāta nolaižas tur
        if total_distance <= self.grenade_speed:
            grenade["x"] = grenade["target_x"]
            grenade["y"] = grenade["target_y"]
            grenade["landed"] = True
            return

        grenade["x"] = grenade["x"] + distance_x / total_distance * self.grenade_speed
        grenade["y"] = grenade["y"] + distance_y / total_distance * self.grenade_speed

    def explode_grenade(self, grenade):
        # Katrs zombijs aplī iet bojā, un par katru saņemam punktus
        zombies_still_alive = []

        for zombie in self.zombies:
            distance_to_grenade = math.hypot(zombie["x"] - grenade["x"], zombie["y"] - grenade["y"])

            if distance_to_grenade <= self.grenade_radius:
                self.score = self.score + self.points_per_zombie
            else:
                zombies_still_alive.append(zombie)

        self.zombies = zombies_still_alive

        # Šeit client uzzīmē īsu sprādziena attēlu
        explosion = {"x": grenade["x"], "y": grenade["y"], "timer": self.explosion_time}
        self.explosions.append(explosion)

    def update_explosions(self):
        explosions_still_visible = []

        for explosion in self.explosions:
            explosion["timer"] = explosion["timer"] - 1
            if explosion["timer"] > 0:
                explosions_still_visible.append(explosion)

        self.explosions = explosions_still_visible

    # ---------- Viļņi ----------
    def update_wave(self):
        # Pauzes laikā tikai skaitām atpakaļ, un tad sākas nākamais vilnis
        if self.wave_break_timer > 0:
            self.wave_break_timer = self.wave_break_timer - 1
            if self.wave_break_timer == 0:
                self.start_wave()
            return

        self.spawn_zombies_over_time()

        # Vilnis ir beidzies, kad nav ko vairs izlaist un visi zombiji ir miruši
        if self.zombies_left_to_spawn == 0 and len(self.zombies) == 0:
            self.finish_wave()

    def start_wave(self):
        # Katrā vilnī ir vairāk zombiju
        zombie_count = self.zombies_in_first_wave + (self.wave_number - 1) * self.extra_zombies_per_wave
        self.zombies_left_to_spawn = zombie_count

        # Izkliedējam zombijus pa visu parādīšanās laiku (bet ne ātrāk kā vienu ik pēc 10 kadriem)
        self.wave_spawn_delay = max(10, self.wave_spawn_time // zombie_count)
        self.zombie_spawn_timer = 0  # pirmais zombijs parādās uzreiz

        # Izturīgāki zombiji: +dzīvības ik pēc 3 viļņiem (// atmet daļskaitli)
        waves_with_extra_health = (self.wave_number - 1) // 3
        self.current_zombie_health = self.zombie_health + self.extra_zombie_health * waves_with_extra_health

        # Ātrāki zombiji: +ātrums katrā vilnī, līdz maksimumam
        faster_speed = self.zombie_speed + self.zombie_speed_increase * (self.wave_number - 1)
        self.current_zombie_speed = min(faster_speed, self.zombie_max_speed)

    def finish_wave(self):
        self.score = self.score + self.points_per_wave
        self.wave_number = self.wave_number + 1
        self.wave_break_timer = self.wave_break_delay

    # ---------- Zombiji ----------
    def spawn_zombies_over_time(self):
        if self.zombies_left_to_spawn <= 0:
            return

        self.zombie_spawn_timer = self.zombie_spawn_timer - 1

        if self.zombie_spawn_timer <= 0:
            self.spawn_zombie()
            self.zombies_left_to_spawn = self.zombies_left_to_spawn - 1
            self.zombie_spawn_timer = self.wave_spawn_delay

    def spawn_zombie(self):
        # Zombiji parādās tieši aiz spēles laukuma malas, nejaušā pusē
        # (augšā un apakšā tas ir aiz joslām, tāpēc parādīšanos neredz)
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

        # Katrs zombijs saņem savu ātrumu, lai tie nepienāktu visi reizē
        speed_factor = random.uniform(self.zombie_slowest_factor, self.zombie_fastest_factor)

        # Katrs zombijs saņem arī savu vietu ap spēlētāju. Vieta ir tajā pašā pusē,
        # no kuras zombijs nāk, ar nelielu nejaušu novirzi, tāpēc zombiji iet
        # aptuveni taisni uz spēlētāju un nevazājas apkārt
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

            # Tālu: iet uz šī zombija savu vietu blakus spēlētājam
            # Tuvu: iet taisni uz spēlētāju
            if distance_to_player > self.zombie_flank_distance:
                target_x = self.player_x + zombie["flank_x"]
                target_y = self.player_y + zombie["flank_y"]
            else:
                target_x = self.player_x
                target_y = self.player_y

            # Tā pati ideja kā šaujot: atrodam virzienu uz mērķi
            distance_x = target_x - zombie["x"]
            distance_y = target_y - zombie["y"]
            total_distance = math.hypot(distance_x, distance_y)

            # Zombijs ir tieši uz sava mērķa, tāpēc nav kur iet
            if total_distance == 0:
                continue

            zombie["x"] = zombie["x"] + distance_x / total_distance * zombie["speed"]
            zombie["y"] = zombie["y"] + distance_y / total_distance * zombie["speed"]

    def push_zombies_apart(self):
        # Katrs zombiju pāris, kas ir par tuvu, atgrūž viens otru,
        # lai zombiji neuzkrātos viens uz otra
        minimum_distance = self.zombie_spacing

        for first_number in range(len(self.zombies)):
            for second_number in range(first_number + 1, len(self.zombies)):
                first_zombie = self.zombies[first_number]
                second_zombie = self.zombies[second_number]

                distance_x = second_zombie["x"] - first_zombie["x"]
                distance_y = second_zombie["y"] - first_zombie["y"]
                total_distance = math.hypot(distance_x, distance_y)

                # Šie divi ir pietiekami tālu viens no otra
                if total_distance >= minimum_distance:
                    continue

                # Tie ir tieši vienā vietā, tāpēc atgrūžam tos nejaušā virzienā
                if total_distance == 0:
                    angle = random.uniform(0, 2 * math.pi)
                    distance_x = math.cos(angle)
                    distance_y = math.sin(angle)
                    total_distance = 1

                # Katrs zombijs atkāpjas par pusi no pārklāšanās
                overlap = minimum_distance - total_distance
                push_x = distance_x / total_distance * overlap / 2
                push_y = distance_y / total_distance * overlap / 2

                first_zombie["x"] = first_zombie["x"] - push_x
                first_zombie["y"] = first_zombie["y"] - push_y
                second_zombie["x"] = second_zombie["x"] + push_x
                second_zombie["y"] = second_zombie["y"] + push_y

    # ---------- Lodes trāpa zombijiem ----------
    def check_bullet_hits(self):
        # Zombijs ir kvadrāts, tāpēc lode tam pieskaras, kad ir pietiekami tuvu
        touch_distance = self.zombie_size / 2 + self.bullet_size

        # 1. solis: katra lode, kas pieskaras zombijam, to ievaino un pazūd
        bullets_that_missed = []

        for bullet in self.bullets:
            bullet_hit_a_zombie = False

            for zombie in self.zombies:
                if is_close(bullet["x"], bullet["y"], zombie["x"], zombie["y"], touch_distance):
                    zombie["health"] = zombie["health"] - self.bullet_damage
                    bullet_hit_a_zombie = True
                    break  # viena lode var trāpīt tikai vienam zombijam

            if not bullet_hit_a_zombie:
                bullets_that_missed.append(bullet)

        self.bullets = bullets_that_missed

        # 2. solis: zombiji bez dzīvībām iet bojā, un par katru saņemam punktus
        zombies_still_alive = []

        for zombie in self.zombies:
            if zombie["health"] > 0:
                zombies_still_alive.append(zombie)
            else:
                self.score = self.score + self.points_per_zombie

        self.zombies = zombies_still_alive

    # ---------- Zombiji trāpa spēlētājam ----------
    def check_zombie_hits_player(self):
        # Spēlētājs ir drošībā, kamēr turpinās pauze pēc pēdējā trāpījuma
        if self.hit_timer > 0:
            return

        # Spēlētājs ir drošībā arī izrāviena laikā
        if self.dash_timer > 0:
            return

        # Abi ir kvadrāti, tāpēc tie pieskaras, kad ir pietiekami tuvu
        touch_distance = (self.player_size + self.zombie_size) / 2

        for zombie in self.zombies:
            if is_close(zombie["x"], zombie["y"], self.player_x, self.player_y, touch_distance):
                self.player_health = self.player_health - self.zombie_damage
                self.hit_timer = self.hit_pause
                break  # vienlaikus tikai viens trāpījums, pat ja pieskaras vairāki zombiji

        if self.player_health <= 0:
            self.player_health = 0
            self.hit_timer = 0
            self.state = "game_over"