# Основной алгоритм выбора маршрута
from random import random
import numpy as np
from time import time

from DB import X1, X2, N, J
from Utilities import filter, car_crushes, AntLog
from tests import reform_a_path, form_a_dict

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

В данном алгоритме присутствует 6 открытых параметра a, b, p, k - параметры системы, J - число итераций, impact_value - функция оставляемого феромона
'''

start_time = time()

all_logs:list = []
LogsInclude:bool = True # Включает / выключает логи

class AntGen():
    Pheromons:np.matrix = np.full((N, N), 0.1) # Матрица феромонов N*N из чисел 0.1
    ChoiceGradient:np.matrix = np.zeros((N, N)) # Матрица вероятностей перехода

    def __init__(self, flags:list, blocks:list, s:int, angle:int, a:int = 1, b:int = 1, p:float = 0.6, k:float = 42.5): # Инициализация объекта
        self.start = s
        self.start_angle = angle

        self.requried_points = flags
        self.blocks = blocks

        self.ActiveRoads:np.matrix = car_crushes(self.blocks, X1)
        self.ActiveRoadsT:np.matrix = car_crushes(self.blocks, X2)

        self.alfa = a
        self.beta = b
        self.omega:np.matrix = np.power(self.ActiveRoadsT, self.beta)

        self.p = p
        self.kill_border = k

    def _refresh_choice_gradient(self) -> None:
        # Метод обновления глобальной матрицы вероятности
        self.ChoiceGradient = np.power(self.Pheromons, self.alfa) * self.omega # В матричном виде. ActiveRoads.T ** self.beta не меняется, можно вынести за функцию

        row_sums = np.sum(self.ChoiceGradient, axis = 1, keepdims = True)  # Суммируем по строкам
        self.ChoiceGradient = self.ChoiceGradient / row_sums  # Делим каждую строку на её сумму
    
    def _refresh_pheromons(self, matrix:np.matrix, points:int, length:float) -> np.matrix:
        # Метод обновления матрицы феромонов. 
        impact_value = points / length if length > 0 else 0
        matrix = np.where(matrix == 1, impact_value, matrix)
        
        return matrix

    def _new_ant_iteration(self) -> list:
        # Одна полная итерация карты ферамонов
        self.Pheromons *= self.p # Феромон испаряется

        self._refresh_choice_gradient() # Обновляем матрицу вероятностей
        pheromon_trace = np.zeros((N, N)) # Матрица феромонов одной итерации

        # Создаем лог с фильтром. Если логи отключены, работает только фильтр
        log = AntLog(dead_count = 0, success_count = 0, max_points = 0, total_length = 0.0, IfLogsIncluded = LogsInclude)

        # Код записи карты феромонов. С учётом length и points оставляет по маршруту route феромон
        for i in range(N): # Столько же, сколько вершин
            ant = Ant(self) # Запускаем итерацию муравья. 
            matrix, route, points, length, death_reason = ant._ant_route() # Распаковываем муравья

            if matrix.any():
                pheromon_trace += self._refresh_pheromons(matrix, points, length)
                log.write_ant_log(route, points, length, death_reason, i)

        self.Pheromons += pheromon_trace

        if LogsInclude:
            iteration_data, best_route_info = log.finalize_log(self.Pheromons, self.ChoiceGradient)
            return iteration_data, filter([best_route_info] if best_route_info else [])
        else:
            best_route_info = log.finalize_log(self.Pheromons, self.ChoiceGradient)

        return filter([best_route_info] if best_route_info else [])

    def main(self) -> list:
        # Запуск алгоритма
        global all_logs
        final_result = []

        for i in range(J):
            if LogsInclude:
                iteration_data, best_route = self._new_ant_iteration()
                gen_log = AntLog.write_gen_log(iteration_data, i)
                all_logs.append(gen_log) # Вызов 
            else:
                best_route = self._new_ant_iteration()

            if best_route is not None:
                final_result.append(best_route)

        return filter(final_result) if final_result else None

class Ant(AntGen):
    def __init__(self, gen):
        self.gen = gen

    def _ant_making_choice(self, choice:float, current_point:int, previous_point:int) -> int:
        # Поиск наиболее близкого числа в массиве для выбора следующей точки
        paths:np.array = np.array(self.gen.ChoiceGradient[current_point - 1])
        paths = reform_a_path(paths, previous_point, current_point, self.gen.start_angle, self.gen.start) # Удаляем ненужные точки, определяемые поворотом
        paths_dict = form_a_dict(paths) # Формируем пути в виде словаря точка перехода -> вероятность

        for key in paths_dict:
            if paths_dict[key][0] <= choice <= paths_dict[key][1]:
                chosen_point = key
                return chosen_point
            else:
                continue
        
        if chosen_point == None: # Если выбора нет - возвращаем 0
            return 0

    def _is_ant_dead(self, route:list, length:float, current_point:int) -> bool:
        # Если попал в тупик или слишком долго 
        n = len(route)

        if length >= self.gen.kill_border:
            return (False, 'Превышен лимит длины')
        
        elif current_point == 0:
            return (False, 'Тупик')
    
        # Проверяем последовательности длиной от 3 до n // 2
        seen_sequences = set()
        for length in range(3, n // 2 + 1):
            for start in range(n - length):
                sequence = tuple(route[start:start + length])
                if sequence in seen_sequences:
                    return (False, 'Круг смерти')
                seen_sequences.add(sequence)

        return (True, None)

    def _ant_route(self) -> tuple:
        # Дорога одного муравья в итерации
        previous_point = 0
        current_point = self.gen.start # Текущая точка
        points = length = 0 # Обновляем параметры успеха
        ant_pheromon_trace = np.zeros((N, N)) # Запоминаем маршрут муравья. Используем словарь, так как он работает схоже с hesh таблицей
        route, memory = [], []
        AntAlive = True # Муравей оживает
        death_reason = None

        # Начало движения
        while AntAlive:  
            choice = random()
            chosen_point = self._ant_making_choice(choice, current_point, previous_point)
            previous_point, current_point = current_point, chosen_point

            length += float(self.gen.ActiveRoads[previous_point - 1, current_point - 1]) # Записываем пройденное расстояние
            ant_pheromon_trace[previous_point - 1, current_point - 1] = 1 # Запоминаем след муравья для рассчёта феромона.
            route.append(int(current_point)) # Запоминаем маршрут

            # Учитываем только непройденные ранее точки в подсчете ценности маршрута
            if (current_point in self.gen.requried_points) and not(current_point in memory):
                points += 1 # Сколько точек собрал муравей, на столько больше он отложит феромона
                memory.append(current_point)

            AntAlive, death_reason = self._is_ant_dead(route, length, current_point) # Проверка того, был ли шаг муравья смертельным

            if len(memory) == len(self.gen.requried_points):
                break

        # Если к концу цикла муравей умер, то параметры успеха обнуляются
        if death_reason or not memory:
            return (ant_pheromon_trace, route, 0, 0, death_reason)
        
        return (ant_pheromon_trace, route, points, length, None) # Возвращаем коллекцию параметров успеха и маршрута

    
if __name__ == "__main__":

    # ЗДЕСЬ ТЕСТЫ И ЛОГИ

    Cycle = AntGen([11, 5, 10], [(5, 14)], 6, angle = 180, a = 1, b = 1, p = 0.5, k = 40)
    Route = Cycle.main()

    if LogsInclude:
        with open('logs.txt', 'w', encoding='utf-8') as file:  # Добавлено encoding
            file.write("\n\n".join(all_logs))

    print(time() - start_time)

    print(Route)