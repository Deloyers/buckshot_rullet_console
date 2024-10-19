import random
import time
import os
import sqlite3
from typing import List, Optional, Tuple, Union

class Player:
    """
    Класс, представляющий игрока в игре.
    
    Attributes:
        name (str): Имя игрока.
        lives (int): Количество жизней игрока.
        items (List[str]): Список предметов игрока.
    """

    def __init__(self, name: str):
        self.name: str = name
        self.lives: int = 2
        self.items: List[str] = []

class RussianRoulette:
    """
    Основной класс игры "Русская рулетка".
    
    Attributes:
        player (Player): Объект игрока.
        dealer (Player): Объект дилера.
        shotgun (List[str]): Список патронов в дробовике.
        stage (int): Текущий этап игры.
        round (int): Текущий раунд игры.
        infinite_mode (bool): Флаг бесконечного режима.
        winnings (int): Сумма выигрыша.
        stages_completed (int): Количество завершенных этапов.
        db_connection (sqlite3.Connection): Соединение с базой данных.
    """

    def __init__(self):
        self.player: Player = Player("Игрок")
        self.dealer: Player = Player("Дилер")
        self.shotgun: List[str] = []
        self.stage: int = 1
        self.round: int = 1
        self.infinite_mode: bool = False
        self.winnings: int = 0
        self.stages_completed: int = 0
        self.db_connection: sqlite3.Connection = sqlite3.connect('game_progress.db')
        self.create_table()

    def create_table(self) -> None:
        """Создает таблицу в базе данных для сохранения прогресса игры."""
        cursor = self.db_connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_progress
        (id INTEGER PRIMARY KEY,
         player_lives INTEGER,
         dealer_lives INTEGER,
         player_items TEXT,
         dealer_items TEXT,
         stage INTEGER,
         round INTEGER,
         infinite_mode INTEGER,
         winnings INTEGER,
         stages_completed INTEGER)
        ''')
        self.db_connection.commit()

    def save_progress(self) -> None:
        """Сохраняет текущий прогресс игры в базу данных."""
        cursor = self.db_connection.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO game_progress
        (id, player_lives, dealer_lives, player_items, dealer_items, stage, round, infinite_mode, winnings, stages_completed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (1, self.player.lives, self.dealer.lives, ','.join(self.player.items), ','.join(self.dealer.items),
              self.stage, self.round, int(self.infinite_mode), self.winnings, self.stages_completed))
        self.db_connection.commit()

    def load_progress(self) -> bool:
        """
        Загружает сохраненный прогресс игры из базы данных.
        
        Returns:
            bool: True, если прогресс успешно загружен, иначе False.
        """
        cursor = self.db_connection.cursor()
        cursor.execute('SELECT * FROM game_progress WHERE id = 1')
        row = cursor.fetchone()
        if row:
            self.player.lives, self.dealer.lives, player_items, dealer_items, self.stage, self.round, infinite_mode, self.winnings, self.stages_completed = row[1:]
            self.player.items = player_items.split(',') if player_items else []
            self.dealer.items = dealer_items.split(',') if dealer_items else []
            self.infinite_mode = bool(infinite_mode)
            return True
        return False

    def load_shotgun(self) -> None:
        """Заряжает дробовик случайными патронами."""
        self.shotgun = [random.choice(["пустой", "боевой"]) for _ in range(6)]
        if self.dealer.name == "Дилер":
            self.dealer_last_bullet = self.shotgun[-1]
        self.print_shotgun_info()

    def print_shotgun_info(self) -> None:
        """Выводит информацию о текущем состоянии дробовика."""
        total_bullets = len(self.shotgun)
        empty_bullets = self.shotgun.count("пустой")
        live_bullets = self.shotgun.count("боевой")
        print(f"В дробовике {total_bullets} патронов: {empty_bullets} холостых, {live_bullets} боевых.")

    def shoot(self, target: Player) -> Union[bool, str]:
        """
        Производит выстрел по цели.
        
        Args:
            target (Player): Цель выстрела.
        
        Returns:
            Union[bool, str]: Результат выстрела или "new_round", если начинается новый раунд.
        """
        if not self.shotgun:
            self.clear_console()
            print("Дробовик пуст. Начинается новый раунд...")
            time.sleep(1)
            self.start_new_round()
            return "new_round"
    
        bullet = self.shotgun.pop(0)
        self.clear_console()
        print(f"{target.name} получает выстрел. Заряд: {bullet}")
        self.print_shotgun_info()
        time.sleep(1)
    
        if bullet == "боевой":
            target.lives -= 1
            print(f"{target.name} теряет жизнь. Осталось жизней: {target.lives}")
            time.sleep(1)
            return False
        else:
            print(f"{target.name} везет. Можно сделать еще один выстрел.")
            time.sleep(1)
            return True

    def use_item(self, player: Player, item: str) -> Optional[str]:
        """
        Использует предмет из инвентаря игрока.
        
        Args:
            player (Player): Игрок, использующий предмет.
            item (str): Название предмета.
        
        Returns:
            Optional[str]: Результат использования предмета или None.
        """
        self.clear_console()
        if item == "Телефон":
            if self.shotgun:
                random_index = random.randint(0, len(self.shotgun) - 1)
                print(f"Таинственный голос сообщает: {random_index + 1}-й патрон - {self.shotgun[random_index]}")
            else:
                print("Дробовик пуст. Нельзя использовать Телефон.")
        elif item == "Банка пива":
            if self.shotgun:
                removed_bullet = self.shotgun.pop(0)
                print(f"{player.name} использует Банку пива. Удален заряд: {removed_bullet}")
                if not self.shotgun:
                    print("Это был последний заряд. Раунд завершен.")
                    return "end_round"
            else:
                print("Дробовик пуст. Нельзя использовать Банку пива.")
        elif item == "Лупа":
            if self.shotgun:
                print(f"{player.name} использует Лупу. Следующий заряд: {self.shotgun[0]}")
            else:
                print("Дробовик пуст. Нельзя использовать Лупу.")
        elif item == "Наручники":
            print(f"{player.name} использует Наручники. Оппонент пропускает ход.")
            return "skip_turn"
        elif item == "Пачка сигарет":
            player.lives += 1
            print(f"{player.name} использует Пачку сигарет. Получена дополнительная жизнь. Жизней: {player.lives}")
        elif item == "Складная ножовка":
            print(f"{player.name} использует Складную ножовку. Урон дробовика удвоен на этот ход.")
            return "double_damage"
        elif item == "Отказ от претензий, подписанный Богом":
            print(f"{player.name} кладет 'Отказ от претензий, подписанный Богом' обратно в черный ящик.")
        elif item == "Адреналин":
            if player.name == "Игрок" and self.dealer.items:
                stolen_item = random.choice(self.dealer.items)
                self.dealer.items.remove(stolen_item)
                print(f"{player.name} использует Адреналин и крадет у Дилера предмет: {stolen_item}")
                return self.use_item(player, stolen_item)
            elif player.name == "Дилер" and self.player.items:
                stolen_item = random.choice(self.player.items)
                self.player.items.remove(stolen_item)
                print(f"{player.name} использует Адреналин и крадет у Игрока предмет: {stolen_item}")
                return self.use_item(player, stolen_item)
            else:
                print(f"{player.name} не может использовать Адреналин, так как у оппонента нет предметов.")
        elif item == "Инвертор":
            if self.shotgun:
                self.shotgun[0] = "боевой" if self.shotgun[0] == "пустой" else "пустой"
                print(f"{player.name} использует Инвертор. Следующий заряд изменен.")
            else:
                print("Дробовик пуст. Нельзя использовать Инвертор.")
        elif item == "Одноразовый телефон":
            if self.shotgun:
                random_index = random.randint(0, len(self.shotgun) - 1)
                print(f"{player.name} использует Одноразовый телефон. {random_index + 1}-й заряд: {self.shotgun[random_index]}")
            else:
                print("Дробовик пуст. Нельзя использовать Одноразовый телефон.")
        elif item == "Просроченное лекарство":
            effect = random.choice(["positive", "negative"])
            if effect == "positive":
                player.lives += 2
                print(f"{player.name} использует Просроченное лекарство. Получено 2 дополнительные жизни. Жизней: {player.lives}")
            else:
                player.lives -= 1
                print(f"{player.name} использует Просроченное лекарство. Потеряна 1 жизнь. Жизней: {player.lives}")

        time.sleep(2)
        return None

    def dealer_turn(self) -> Union[bool, str]:
        """
        Выполняет ход дилера.
        
        Returns:
            Union[bool, str]: Результат хода дилера.
        """
        if self.dealer.items:
            item = random.choice(self.dealer.items)
            self.dealer.items.remove(item)
            result = self.use_item(self.dealer, item)
            if result in ["skip_turn", "double_damage", "end_round"]:
                return result

        knows_next_bullet = self.dealer_knows_bullet()

        while True:
            if not self.shotgun:
                self.clear_console()
                print("Дробовик пуст. Начинается новый раунд...")
                time.sleep(1)
                self.start_new_round()
                return "new_round"

            if knows_next_bullet:
                if self.shotgun[0] == "пустой":
                    result = self.shoot(self.dealer)
                else:
                    result = self.shoot(self.player)
            else:
                if random.choice([True, False]):
                    result = self.shoot(self.player)
                else:
                    result = self.shoot(self.dealer)
        
            if result == "new_round":
                continue
            return result

    def dealer_knows_bullet(self) -> bool:
        """
        Проверяет, знает ли дилер следующий патрон.
        
        Returns:
            bool: True, если дилер знает следующий патрон, иначе False.
        """
        return self.shotgun and (self.shotgun[0] == self.dealer_last_bullet or "Лупа" in self.dealer.items)

    def player_turn(self) -> Union[bool, str]:
        """
        Выполняет ход игрока.
        
        Returns:
            Union[bool, str]: Результат хода игрока.
        """
        if not self.shotgun:
            self.clear_console()
            print("Дробовик пуст. Начинается новый раунд...")
            time.sleep(1)
            self.start_new_round()
            return "new_round"

        while True:
            self.clear_console()
            print(f"Ваши жизни: {self.player.lives}")
            print(f"Ваши предметы: {', '.join(self.player.items)}")
            self.print_shotgun_info()
            action = input("Выберите действие (стрелять/использовать предмет): ").lower()
            if action == "стрелять":
                target = input("Выберите цель (себя/дилера): ").lower()
                if target == "себя":
                    result = self.shoot(self.player)
                    if result == "new_round":
                        continue
                    return result
                elif target == "дилера":
                    result = self.shoot(self.dealer)
                    if result == "new_round":
                        continue
                    return result
                else:
                    print("Неверная цель. Попробуйте снова.")
                    time.sleep(1)
            elif action == "использовать предмет":
                if self.player.items:
                    print("Доступные предметы:", ", ".join(self.player.items))
                    item = input("Выберите предмет для использования: ")
                    if item in self.player.items:
                        self.player.items.remove(item)
                        result = self.use_item(self.player, item)
                        if result in ["skip_turn", "double_damage", "end_round"]:
                            return result
                    else:
                        print("У вас нет такого предмета. Попробуйте снова.")
                        time.sleep(1)
                else:
                    print("У вас нет предметов для использования.")
                    time.sleep(1)
            else:
                print("Неверное действие. Попробуйте снова.")
                time.sleep(1)

    def offer_new_items(self) -> None:
        """Предлагает игроку новые предметы в начале этапа."""
        max_items = 2 if self.stage == 2 else 4
        available_items = ["Банка пива", "Лупа", "Наручники", "Пачка сигарет", "Складная ножовка", "Отказ от претензий, подписанный Богом", "Телефон"]
        new_items = random.sample(available_items, max_items)
    
        print("Вам дали специальную коробочку!")
        for item in new_items:
            while True:
                choice = input(f"Достать предмет '{item}'? (q - да, a - завершить): ").lower()
                if choice == 'q':
                    if len(self.player.items) < 8:
                        self.player.items.append(item)
                        print(f"Вы получили предмет: {item}")
                        print(f"Ваши предметы: {', '.join(self.player.items)}")
                        break
                    else:
                        print("Все слоты заполнены!")
                        break
                elif choice == 'a':
                    print("Получение предметов завершено.")
                    return
                else:
                    print("Неверный ввод. Попробуйте снова.")
    
        print("Все предметы из коробочки разобраны.")

    def start_new_round(self) -> None:
        """Начинает новый раунд игры."""
        self.round += 1
        self.clear_console()
        print(f"\nНачинается раунд {self.round}")
        self.load_shotgun()
        print("Информация о патронах:")
        self.print_shotgun_info()
        if self.stage in [2, 3]:
            self.offer_new_items()
        time.sleep(2)

    def play_stage(self) -> Optional[bool]:
        """
        Играет один этап игры.
        
        Returns:
            Optional[bool]: True, если игрок выиграл, False, если проиграл, None в случае ничьей.
        """
        self.clear_console()
        print(f"\nНачинается этап {self.stage}")
        time.sleep(1)
        if self.stage == 1:
            self.player.lives = self.dealer.lives = 2
            self.player.items = []
            self.dealer.items = []
        elif self.stage == 2:
            self.player.lives = self.dealer.lives = 4
        elif self.stage == 3:
            self.player.lives = self.dealer.lives = 6
        
        self.round = 0
        self.start_new_round()
        
        skip_next_turn = None
        
        while self.player.lives > 0 and self.dealer.lives > 0:
            self.clear_console()
            print(f"\nЭтап {self.stage}, Раунд {self.round}")
            print(f"Жизни игрока: {self.player.lives}, Жизни дилера: {self.dealer.lives}")
            print(f"Предметы игрока: {', '.join(self.player.items)}")
            print(f"Предметы дилера: {', '.join(self.dealer.items)}")
            self.print_shotgun_info()
            time.sleep(1)
            
            if skip_next_turn != "player":
                player_result = self.player_turn()
                if player_result == "new_round":
                    self.start_new_round()
                    continue
                if player_result == "skip_turn":
                    skip_next_turn = "dealer"
                    continue
                if self.dealer.lives <= 0:
                    break
            else:
                skip_next_turn = None
            
            if skip_next_turn != "dealer" and self.dealer.lives > 0:
                dealer_result = self.dealer_turn()
                if dealer_result == "new_round":
                    self.start_new_round()
                    continue
                if dealer_result == "skip_turn":
                    skip_next_turn = "player"
                    continue
            else:
                skip_next_turn = None
            
            if self.stage == 3 and (self.player.lives <= 2 or self.dealer.lives <= 2):
                self.clear_console()
                print("Внимание! Система жизнеобеспечения отключена. Режим 'пан или пропал'.")
                time.sleep(2)

        self.clear_console()
        if self.player.lives <= 0:
            print("Игрок проиграл.")
            time.sleep(2)
            return False
        elif self.dealer.lives <= 0:
            print("Дилер проиграл.")
            time.sleep(2)
            return True
        else:
            print("Этап завершен. Ничья.")
            time.sleep(2)
            return None
    
    def play_infinite_mode(self) -> None:
        """Играет в бесконечном режиме."""
        while True:
            result = self.play_stage()
            if result:
                self.stages_completed += 1
                if self.stages_completed % 3 == 0:
                    self.clear_console()
                    double_down = input(f"Вы выиграли {self.winnings}$. Хотите удвоить выигрыш? (да/нет): ").lower()
                    if double_down == "да":
                        self.winnings *= 2
                        print(f"Отлично! Теперь ваш выигрыш составляет {self.winnings}$.")
                    else:
                        print(f"Поздравляем! Вы уходите с выигрышем в {self.winnings}$.")
                        time.sleep(2)
                        return
                self.stage = (self.stage % 3) + 1
            else:
                self.clear_console()
                print("Вы проиграли в бесконечном режиме и остались ни с чем.")
                time.sleep(2)
                return
            self.save_progress()

    def play(self) -> None:
        """Основной метод для запуска игры."""
        self.clear_console()
        choice = input("Выберите действие (новая игра/загрузить): ").lower()
        if choice == "загрузить" and self.load_progress():
            print("Прогресс успешно загружен.")
            time.sleep(1)
        else:
            print("Начинаем новую игру.")
            time.sleep(1)

        while True:
            if not self.infinite_mode:
                for stage in range(self.stage, 4):
                    self.stage = stage
                    result = self.play_stage()
                    self.save_progress()
                    if not result:
                        self.clear_console()
                        print("Игра окончена. Вы проиграли.")
                        time.sleep(2)
                        return
                    elif result is True and stage == 3:
                        self.clear_console()
                        print("Поздравляем! Вы выиграли чемодан денег и дробовик на память!")
                        time.sleep(2)
                        break
                
                self.clear_console()
                play_infinite = input("Хотите сыграть в бесконечный режим? (да/нет): ").lower()
                if play_infinite == "да":
                    self.clear_console()
                    print("Вы приняли таблетки и вошли в бесконечный режим.")
                    time.sleep(2)
                    self.infinite_mode = True
                    self.winnings = 1000
                    self.save_progress()
                else:
                    break
            else:
                self.play_infinite_mode()

    @staticmethod
    def clear_console() -> None:
        """Очищает консоль."""
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    game = RussianRoulette()
    game.play()
