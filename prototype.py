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
    if not routes or not routes[0]:  # Проверка на пустой список или пустой словарь
        return None
    best_route = None
    max_points = 0
    min_length = float('inf')
    for route_info in routes:
        if not route_info:  # Пропуск пустых словарей
            continue
        (points, lengths), route = list(route_info.items())[0]
        if points > max_points or (points == max_points and lengths < min_length):
            best_route = route
            max_points = points
            min_length = lengths
    return best_route


class AcoCars():
    Pheromons = np.full((N, N), 0.1)  # Матрица феромонов N*N из чисел 0.1
    ChoiceGradient = np.zeros((N, N))  # Матрица вероятностей перехода

    def __init__(self, flags: list, blocks: list, s: int, a: int = 1, b: int = 1, p: float = 0.6, k: float = 42.5):
        self.start = s
        self.requried_points = flags
        self.alfa = a
        self.beta = b
        self.omega = ActiveRoadsT ** self.beta
        self.p = p
        self.kill_border = k

    def __refresh_choice_gradient(self) -> None:
        self.ChoiceGradient = (self.Pheromons ** self.alfa) * self.omega
        row_sums = np.sum(self.ChoiceGradient, axis=1, keepdims=True)
        self.ChoiceGradient = self.ChoiceGradient / row_sums

    def __ant_making_choice(self, choice: float, current_point: int, previous_point: int) -> int:
        paths = list(self.ChoiceGradient[current_point - 1])
        paths[previous_point - 1] = 0
        paths_array = np.array(paths)
        paths_array[paths_array == 0] = 100
        idx = (np.abs(paths_array - choice)).argmin()
        return idx + 1

    def __is_death_circle(self, route: list) -> bool:
        n = len(route)
        for length in range(3, n // 2 + 1):
            for start in range(n - length):
                sequence = route[start:start + length]
                for next_start in range(start + length, n - length + 1):
                    if route[next_start:next_start + length] == sequence:
                        return True
        return False

    def __is_ant_dead(self, length, current_point) -> bool:
        if length >= self.kill_border or current_point == 0:
            return False
        return True

    def __ant_route(self) -> tuple:
        previous_point = current_point = self.start
        points = length = 0
        ant_pheromon_trace = np.zeros((N, N))
        route = []
        memory = []
        death_reason = None

        while True:
            choice = randint(0, 1)
            chosen_point = self.__ant_making_choice(choice, current_point, previous_point)

            previous_point = current_point
            current_point = chosen_point
            length += float(ActiveRoads[previous_point - 1, current_point - 1])
            ant_pheromon_trace[previous_point - 1, current_point - 1] = 1

            route.append(current_point)
            if current_point in self.requried_points and current_point not in memory:
                points += 1
                memory.append(current_point)

            alive = self.__is_ant_dead(length, current_point)
            if not alive or self.__is_death_circle(route):
                break

        if not alive:
            death_reason = "Превышен лимит длины" if length >= self.kill_border else "Тупик"
        elif self.__is_death_circle(route):
            death_reason = "Круг смерти"

        if death_reason or not memory:
            return (ant_pheromon_trace, [], 0, 0, death_reason)
        return (ant_pheromon_trace, route, points, length, None)

    def __refresh_pheromons(self, matrix: np.matrix, points: int, length: float) -> np.matrix:
        impact_value = points + (1 / length) if length > 0 else 0
        matrix[matrix == 1] = impact_value
        return matrix

    def __new_ant_iteration(self) -> tuple:
        self.Pheromons *= self.p
        self.__refresh_choice_gradient()
        pheromon_trace = np.zeros((N, N))
        dead_count = 0
        success_count = 0
        total_length = 0.0
        max_points = 0
        best_route = None
        ant_logs = []

        for ant_num in range(N):
            ant = self.__ant_route()
            matrix, route, points, length, death_reason = ant

            if death_reason or not route:
                dead_count += 1
                status = f"Мёртв. Причина: {death_reason}"
            else:
                success_count += 1
                total_length += length
                if points > max_points:
                    max_points = points
                    best_route = route
                status = (f"Собрано точек: {points}, Длина маршрута: {length:.1f}, "
                          f"Маршрут: {', '.join(map(str, route))}")

            ant_logs.append(f"\tНомер муравья {ant_num + 1}: {status}")

            if matrix.any():
                pheromon_trace += self.__refresh_pheromons(matrix, points, length)

        self.Pheromons += pheromon_trace
        avg_length = total_length / success_count if success_count else 0.0

        iteration_data = {
            "pheromones": self.Pheromons.copy(),
            "dead": dead_count,
            "success": success_count,
            "avg_length": avg_length,
            "max_points": max_points,
            "best_route": best_route,
            "ant_logs": ant_logs
        }

        best_route_info = {(max_points, avg_length): best_route} if best_route else None
        return iteration_data, choosing_the_best([best_route_info] if best_route_info else [])

    def main(self) -> list:
        final_result = []
        all_logs = []
        for iteration in range(J):
            iteration_data, best_route = self.__new_ant_iteration()
            if best_route is not None:
                final_result.append(best_route)

            # Формируем строку с матрицей феромонов
            pheromones_str = "\n".join([
                "\t\t" + "  ".join([f"{val:.2f}" for val in row])
                for row in iteration_data["pheromones"]
            ])

            # Формируем запись лога для итерации
            log_entry = (
                f"Итерация {iteration + 1}:\n"
                f"Матрица феромонов:\n{pheromones_str}\n"
                f"Мёртвых муравьев: {iteration_data['dead']}\n"
                f"Дошло до цели: {iteration_data['success']}\n"
                f"Среднее расстояние: {iteration_data['avg_length']:.1f}\n"
                f"Максимальное количество точек: {iteration_data['max_points']}\n"
                f"Лучший маршрут: {', '.join(map(str, iteration_data['best_route'])) if iteration_data['best_route'] else 'Нет'}\n"
            )

            # Добавляем логи муравьев
            log_entry += "\n".join(iteration_data["ant_logs"]) + "\n"
            all_logs.append(log_entry)

        # Запись в файл В КОНЦЕ ВСЕХ ИТЕРАЦИЙ
        with open('logs.txt', 'w', encoding='utf-8') as file:  # Добавлено encoding
            file.write("\n\n".join(all_logs))

        return choosing_the_best(final_result) if final_result else None


def logs():
    with open('logs.txt', 'w', encoding='utf-8') as file:  # Добавлено encoding
        pass


if __name__ == "__main__":
    logs()