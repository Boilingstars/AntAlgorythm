# Файл вспомогательных программ

from numpy import array

N = 15

def generate_robot_commands(start_angle, R, route):
    commands = []
    
    current_angle = start_angle
    
    for i in range(len(route) - 1):
        from_point = route[i]
        to_point = route[i + 1]
        
        # Перемещение вперед
        commands.append(f"model.go_forward({R[from_point - 1][to_point - 1]})")
        
        # Поворот
        required_angle = R[from_point - 1][to_point - 1][1]
        
        if required_angle != current_angle:
            if (current_angle - required_angle) % 360 == 90:
                commands.append(f"model.rotate(90)")
            elif (current_angle - required_angle) % 360 == 270:
                commands.append(f"model.rotate(-90)")
            else:
                raise ValueError("Invalid rotation angle")
            
            current_angle = required_angle
    
    return commands

def filter(routes):
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

def car_crushes(blocks:list, X) -> None:
    for i in blocks:
        X[i[0] - 1][i[1] - 1] = 0

    return array(X).reshape(N, N)

class AntLog():
    # Логи маршрута муравья

    def __init__(self, dead_count, success_count, max_points, total_length, IfLogsIncluded):
        self.IfLogsIncluded = IfLogsIncluded
        self.dead_count = dead_count
        self.success_count = success_count
        self.max_points = max_points
        self.min_length = 100
        self.total_length = total_length
        self.best_route = None
        self.ant_logs = []

    def write_ant_log(self, route, points, length, death_reason, i):
        if self.IfLogsIncluded:
            if death_reason or not route:
                self.dead_count += 1
                self.status = f"Мёртв. Причина: {death_reason}, маршрут: {route}."
            else:
                self.success_count += 1
                self.total_length += length

                if points >= self.max_points and length <= self.min_length:
                    self.max_points = points
                    self.min_length = length
                    self.best_route = route

                self.status = (f"Собрано точек: {points}, Длина маршрута: {length:.1f}, "
                            f"Маршрут: {', '.join(map(str, route))}")
                
            self.ant_logs.append(f"\tНомер муравья {i + 1}: {self.status}")
        else:
            if death_reason or not route:
                pass
            else:
                if points >= self.max_points and length <= self.min_length:
                    self.max_points = points
                    self.min_length = length
                    self.best_route = route
    
    def finalize_log(self, Pheromons, ChoiceGradient):
        best_route_info = {(self.max_points, self.min_length): self.best_route} if self.best_route else None

        if self.IfLogsIncluded:
            avg_length = self.total_length / self.success_count if self.success_count else 0.0

            iteration_data = {
                "pheromones": Pheromons.copy(),
                "choicegradient": ChoiceGradient.copy(),
                "dead": self.dead_count,
                "success": self.success_count,
                "avg_length": avg_length,
                "max_points": self.max_points,
                "best_route": self.best_route,
                "ant_logs": self.ant_logs
            }

            return (iteration_data, best_route_info)
        else:
            return best_route_info
    
    @staticmethod
    def write_gen_log(iteration_data, i):
        # Логи для одного поколения
        pheromones_str = "\n".join([
            "\t\t" + "  ".join([f"{val:.2f}" for val in row])
            for row in iteration_data["pheromones"]
        ])

        choice_gradien_str = "\n".join([
            "\t\t" + "  ".join([f"{val:.2f}" for val in row])
            for row in iteration_data["choicegradient"]
        ])

        # Формируем запись лога для итерации
        log_entry = (
            f"Итерация {i + 1}:\n"
            f"Матрица феромонов:\n{pheromones_str}\n"
            f"Матрица вероятностей:\n{choice_gradien_str}\n"
            f"Мёртвых муравьев: {iteration_data['dead']}\n"
            f"Дошло до цели: {iteration_data['success']}\n"
            f"Среднее расстояние: {iteration_data['avg_length']:.1f}\n"
            f"Максимальное количество точек: {iteration_data['max_points']}\n"
            f"Лучший маршрут: {', '.join(map(str, iteration_data['best_route'])) if iteration_data['best_route'] else 'Нет'}\n"
        )

        # Добавляем логи муравьев
        log_entry += "\n".join(iteration_data["ant_logs"]) + "\n"

        return log_entry