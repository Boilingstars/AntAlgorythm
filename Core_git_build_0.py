# Основной алгоритм выбора маршрута
from random import randint
import numpy as np
from time import time
from DB import ActiveRoads, ActiveRoadsT, N, J

# Анализ ситуации в городе. Удаление заблокированных дорог с ДТП и пробками
def traffic_jams() -> None:
    return

start_time = time()

# Функция отбора лучшего маршрута
def choosing_the_best(routes):
    best_route = None
    max_points = 0      # Начальное значение для максимума
    min_length = 100    # Начальное значение для минимума

    for route in routes:
        # Извлекаем points и lengths
        (points, lengths), values = list(route.items())[0]
        
        # Проверяем, является ли текущий маршрут лучшим
        if (points > max_points) or (points == max_points and lengths < min_length):
            best_route = route
            max_points = points
            min_length = lengths

    return best_route

class AcoCars():
    # __slots__ = ("start", "alfa", "beta", "p", "kill_border") # Коллекция slots для ускорения

    Pheromons = np.full((N, N), 0.1) # Матрица феромонов N*N из чисел 0.1
    ChoiceGradient = np.zeros((N, N)) # Матрица вероятностей перехода

    def __init__(self, flags:list, blocks:list, s:int, a:int = 1, b:int = 1, p:float = 0.6, k:float = 42.5): # Инициализация объекта
        self.start = s
        self.requried_points = flags
        self.alfa = a
        self.beta = b
        self.omega = ActiveRoadsT ** self.beta
        self.p = p
        self.kill_border = k

    # В данном алгоритме присутствует 6 открытых параметра a, b, p, k - параметры системы, J - число итераций, impact_value - функция оставляемого феромона
    def __refresh_choice_gradient(self) -> None:
        # Метод обновления глобальной матрицы вероятности
        self.ChoiceGradient = (self.Pheromons ** self.alfa) * self.omega # В матричном виде. ActiveRoads.T ** self.beta не меняется, можно вынести за функцию

        row_sums = np.sum(self.ChoiceGradient, axis = 1, keepdims = True)  # Суммируем по строкам
        self.ChoiceGradient = self.ChoiceGradient / row_sums  # Делим каждую строку на её сумму

    def __ant_making_choice(self, choice:float, current_point:int, previous_point:int) -> int:
        # Поиск наиболее близкого числа в массиве для выбора следующей точки
        paths:list = list(self.ChoiceGradient[current_point - 1]) # current_point - 1 т.к. итерация начинается с 0
        paths[previous_point - 1] = 0 # Исключаем возвращение обратно

        paths_array = np.array(paths)
        paths_array[paths_array == 0] = 100 # Делаем нулевые точки недостижимыми
        
        idx = (np.abs(paths_array - choice)).argmin() # Получаем индекс первого минимального элемента по модулю
        chosen_point = int(idx) + 1 # idx + 1 т.к. итерация начинается с 0

        return chosen_point # Возвращаем предпочтительную точку перехода
    
    def __is_death_circle(self, route:list) -> bool: # Написать код выхода из кругов смерти
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

    def __is_ant_dead(self, length, current_point) -> bool:
        # Выход из проблемных ситуаций (блуждание, тупик и круг смерти)
        death = True

        # Если попал в тупик или слишком долго блуждал
        if length >= self.kill_border or current_point == 0:
            death = False

        return death

    def __ant_route(self) -> tuple:
        # Дорога одного муравья в итерации
        previous_point = current_point = self.start # Текущая точка
        points = length = 0 # Обновляем параметры успеха

        ant_pheromon_trace = np.zeros((N, N)) # Запоминаем маршрут муравья. Используем словарь, так как он работает схоже с hesh таблицей

        route = []
        memory = []

        AntAlive = True # Муравей оживает

        # Начало движения
        while AntAlive:  
            choice = randint(0, 1)
            chosen_point = self.__ant_making_choice(choice, current_point, previous_point)
            
            previous_point = current_point
            current_point =  chosen_point

            length += float(ActiveRoads[previous_point - 1, current_point - 1]) # Записываем пройденное расстояние
            ant_pheromon_trace[previous_point - 1, current_point - 1] = 1 # Запоминаем след муравья для рассчёта феромона.

            route.append(current_point) # Запоминаем маршрут

            # Учитываем только непройденные ранее точки в подсчете ценности маршрута
            if (current_point in self.requried_points) and not(current_point in memory):
                points += 1 # Сколько точек собрал муравей, на столько больше он отложит феромона
                memory.append(current_point)

            AntAlive = self.__is_ant_dead(length, current_point) # Проверка того, был ли шаг муравья смертельным

            if len(memory) == len(self.requried_points):
                break

        # Если к концу цикла муравей умер, то параметры успеха обнуляются
        if AntAlive == False or self.__is_death_circle(route) == True:
            route = []
            points = 0

        return (ant_pheromon_trace, route, points, length) # Возвращаем коллекцию параметров успеха и маршрута
     
    # Смерть муравья подразумевает введение генетического алгоритма для контроля генерации!
    def __refresh_pheromons(self, matrix:np.matrix, points:int, length:float) -> np.matrix:
        # Обновляем матрицу феромонов. В данном случае значение value = points*0.6/lengths - пятый открытый параметр системы
        impact_value = points + (1 / length)
        matrix[matrix == 1] = impact_value
        
        return matrix

    def __new_ant_iteration(self) -> list:
        # Одна полная итерация карты ферамонов
        self.Pheromons *= self.p # Феромон испаряется

        self.__refresh_choice_gradient() # Обновляем матрицу вероятностей
        pheromon_trace = np.zeros((N, N)) # Матрица феромонов одной итерации
        partial_result = []

        # Код записи карты феромонов. С учётом length и points оставляет по маршруту route феромон
        for i in range(N): # Столько же, сколько вершин
            ant = self.__ant_route() # Запускаем итерацию муравья. Сюда можно передавать работу генетического алгоритма
            matrix, route, points, length = ant # Распаковываем муравья

            if len(route) != 0:
                partial_result.append({(points, length): route})
                pheromon_trace += self.__refresh_pheromons(matrix, points, length) # Записываем вклад от каждого муравья

        self.Pheromons += pheromon_trace # Обновляем глобальную карту

        return choosing_the_best(partial_result)

    def main(self) -> list:
        # Запуск алгоритма
        final_result = []

        for i in range(J):
            final_result.append(self.__new_ant_iteration())
        
        return choosing_the_best(final_result)

# 1 Файл - управление машиной. Второй файл можно разделить на две части.

if __name__ == "__main__":
    pass