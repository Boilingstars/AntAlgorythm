# Основной алгоритм выбора маршрута
from random import randint
import numpy as np
from time import time
from DB import X1, X2, R, N, J
from Utilities import filter, car_crushes, write_gen_log, AntLog

'''
Универсальный муравьиный алгоритм, версия 1.

Что появилось:

- Интерфейс ввода данных
- Структура программы, основанная на взаимодействии двух классов AntGen и Ant
- Первичные логи работы программы

Что необходимо исправить:

- Энтропия маршрутов растёт со временем - предположение
- Кол-во мертвых муравьев растет/в среднем постоянно во времени

Для этого необходимо:

- Интерфейс вывода данных (графики) кол-ва мёртвых муравьев и энтропии
- Генетическая модификация алгоритма
- Испытание машинным обучением
'''

start_time = time()

all_logs = []
LogsInclude = True

class AntGen():
    Pheromons = np.full((N, N), 0.1) # Матрица феромонов N*N из чисел 0.1
    ChoiceGradient = np.zeros((N, N)) # Матрица вероятностей перехода

    def __init__(self, flags:list, blocks:list, s:int, angle:int, a:int = 1, b:int = 1, p:float = 0.6, k:float = 42.5): # Инициализация объекта
        self.start = s
        self.start_angle = angle

        self.requried_points = flags
        self.blocks = blocks

        self.ActiveRoads = car_crushes(self.blocks, X1)
        self.ActiveRoadsT = car_crushes(self.blocks, X2)

        self.alfa = a
        self.beta = b
        self.omega = np.power(self.ActiveRoadsT, self.beta)

        self.p = p
        self.kill_border = k

    # В данном алгоритме присутствует 6 открытых параметра a, b, p, k - параметры системы, J - число итераций, impact_value - функция оставляемого феромона
    def _refresh_choice_gradient(self) -> None:
        # Метод обновления глобальной матрицы вероятности
        self.ChoiceGradient = np.power(self.Pheromons, self.alfa) * self.omega # В матричном виде. ActiveRoads.T ** self.beta не меняется, можно вынести за функцию

        row_sums = np.sum(self.ChoiceGradient, axis = 1, keepdims = True)  # Суммируем по строкам
        self.ChoiceGradient = self.ChoiceGradient / row_sums  # Делим каждую строку на её сумму
    
    # Смерть муравья подразумевает введение генетического алгоритма для контроля генерации!
    def _refresh_pheromons(self, matrix:np.matrix, points:int, length:float) -> np.matrix:
        # Обновляем матрицу феромонов. В данном случае значение value = points*0.6/lengths - пятый открытый параметр системы
        impact_value = points + (1 / length) if length > 0 else 0
        matrix[matrix == 1] = impact_value
        
        return matrix

    def _new_ant_iteration(self) -> list:
        # Одна полная итерация карты ферамонов
        self.Pheromons *= self.p # Феромон испаряется

        self._refresh_choice_gradient() # Обновляем матрицу вероятностей
        pheromon_trace = np.zeros((N, N)) # Матрица феромонов одной итерации

        if LogsInclude:
            log = AntLog(dead_count = 0, success_count = 0, max_points = 0, total_length = 0.0)

        # Код записи карты феромонов. С учётом length и points оставляет по маршруту route феромон
        for i in range(N): # Столько же, сколько вершин
            ant = Ant(self) # Запускаем итерацию муравья. Сюда можно передавать работу генетического алгоритма
            matrix, route, points, length, death_reason = ant._ant_route() # Распаковываем муравья

            if matrix.any():
                pheromon_trace += self._refresh_pheromons(matrix, points, length)

            if LogsInclude:
                log.write_ant_log(route, points, length, death_reason, i)

        self.Pheromons += pheromon_trace

        if LogsInclude:
            iteration_data, best_route_info = log.finalize_log(self.Pheromons)

        return iteration_data, filter([best_route_info] if best_route_info else [])

    def main(self) -> list:
        # Запуск алгоритма
        global all_logs
        final_result = []

        for i in range(J):
            iteration_data, best_route = self._new_ant_iteration()

            if best_route is not None:
                final_result.append(best_route)

            if LogsInclude:
                gen_log = write_gen_log(iteration_data, i)
                all_logs.append(gen_log) # Вызов 

        return filter(final_result) if final_result else None

class Ant(AntGen):
    def __init__(self, gen):
        self.gen = gen

    # -- ТУТ НУЖНА ОПТИМИЗАЦИЯ ОТСЮДА --

    def _rotation_check(self, paths_array:np.array, current_point, idx, choice) -> int:
        global R
        check_value = R[current_point - 1][idx]

        if (self.gen.start_angle - 90) in check_value or (self.gen.start_angle + 90) in check_value:
            return idx
        
        paths_array = list(paths_array)
        paths_array[idx - 1] = 100 # Точка, в которую нельзя повернуть становится недостижимой
        paths_array = np.array(paths_array)

        return np.abs(paths_array - choice).argmin()

    def _ant_making_choice(self, choice:float, current_point:int, previous_point:int) -> int:
        # Поиск наиболее близкого числа в массиве для выбора следующей точки
        paths:list = list(self.gen.ChoiceGradient[current_point - 1]) # current_point - 1 т.к. итерация начинается с 0
        paths[previous_point - 1] = 0 # Исключаем возвращение обратно
        
        paths_array = np.array(paths)
        paths_array[paths_array == 0] = 100 # Делаем нулевые точки недостижимыми
        
        idx = (np.abs(paths_array - choice)).argmin() # Получаем индекс первого минимального элемента по модулю
        
        if current_point == self.gen.start: # Проверяем, можем ли туда развернуться
            idx = self._rotation_check(paths_array, current_point, idx, choice)

        chosen_point = int(idx) + 1 # idx + 1 т.к. итерация начинается с 0

        return chosen_point # Возвращаем предпочтительную точку перехода
    
    # -- ТУТ НУЖНА ОПТИМИЗАЦИЯ ДОСЮДА --

    def _is_death_circle(self, route:list) -> bool: # Написать код выхода из кругов смерти
        n = len(route)
    
        # Проверяем последовательности длиной от 3 до n // 2
        for length in range(3, n // 2 + 1):
            for start in range(n - length):
                # Извлекаем текущую последовательность
                sequence = route[start:start + length]
                # Проверяем, есть ли такая же последовательность дальше в массиве
                for next_start in range(start + length, n - length + 1):
                    if route[next_start:next_start + length] == sequence:
                        return True

        return False

    def _is_ant_dead(self, length:float, current_point:int) -> bool:
        # Выход из проблемных ситуаций (блуждание, тупик и круг смерти)
        death = True

        # Если попал в тупик или слишком долго блуждал
        if length >= self.gen.kill_border or current_point == 0:
            death = False

        return death

    def _ant_route(self) -> tuple:
        # Дорога одного муравья в итерации
        previous_point = current_point = self.gen.start # Текущая точка
        points = length = 0 # Обновляем параметры успеха

        ant_pheromon_trace = np.zeros((N, N)) # Запоминаем маршрут муравья. Используем словарь, так как он работает схоже с hesh таблицей

        route = []
        memory = []

        AntAlive = True # Муравей оживает
        death_reason = None

        # Начало движения
        while AntAlive:  
            choice = randint(0, 1)
            chosen_point = self._ant_making_choice(choice, current_point, previous_point)
            
            previous_point = current_point
            current_point =  chosen_point

            length += float(self.gen.ActiveRoads[previous_point - 1, current_point - 1]) # Записываем пройденное расстояние
            ant_pheromon_trace[previous_point - 1, current_point - 1] = 1 # Запоминаем след муравья для рассчёта феромона.

            route.append(current_point) # Запоминаем маршрут

            # Учитываем только непройденные ранее точки в подсчете ценности маршрута
            if (current_point in self.gen.requried_points) and not(current_point in memory):
                points += 1 # Сколько точек собрал муравей, на столько больше он отложит феромона
                memory.append(current_point)

            AntAlive = self._is_ant_dead(length, current_point) # Проверка того, был ли шаг муравья смертельным

            if len(memory) == len(self.gen.requried_points):
                break

        # Если к концу цикла муравей умер, то параметры успеха обнуляются
        if not AntAlive or self._is_death_circle(route) == True:
            death_reason = "Превышен лимит длины" if length >= self.gen.kill_border else "Тупик"
        
        elif self._is_death_circle(route):
            death_reason = "Круг смерти"

        if death_reason or not memory:
            return (ant_pheromon_trace, [], 0, 0, death_reason)
        
        return (ant_pheromon_trace, route, points, length, None) # Возвращаем коллекцию параметров успеха и маршрута

if __name__ == "__main__":
    Cycle = AntGen([4, 14, 10], [(4, 5)], 1, 0, a = 1, b = 1, p = 0.64, k = 38.0)
    Route = Cycle.main()

    with open('logs.txt', 'w', encoding='utf-8') as file:  # Добавлено encoding
        file.write("\n\n".join(all_logs))

    print(time() - start_time)

    print(Route)