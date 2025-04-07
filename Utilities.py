# Файл вспомогательных программ

from numpy import array
from DB import R

N = 15

class Robot():
    def __init__(self, current_angle, route):
        self.current_angle = current_angle
        self.commands = []
        self.route = route
    
    @staticmethod
    def write_commands(self):
        # Записываем команды в файл
        with open('AntAlgorythm/final_input.txt', 'w') as f:
            f.write('import basic_control_module as bcm\n')
            f.write('start_pos = 6\n')
            f.write('start_rot = 180\n')
            f.write('if __name__ == \'__main__\':\n')
            f.write('  graph=bcm.Graph()\n')
            f.write('  model=bcm.Rover(start_pos, start_rot, graph)\n')
            for command in self.commands:
                f.write('  ' + command + '\n')

    def generate_robot_commands(self): 
        global R
        for i in range(len(self.route) - 1):
            from_point = self.route[i]
            to_point = self.route[i + 1]
            
            # Получаем кортеж возможных углов поворота
            possible_angles:tuple = R[from_point - 1][to_point - 1]
            print(possible_angles, self.current_angle)
            
            # Проверяем, совпадает ли текущий угол с одним из возможных
            if self.current_angle in possible_angles:
                pass

            # Проверяем необходимость поворота на 90
            elif abs(self.current_angle - abs(possible_angles[0])) == 90:
                self.commands.append(f"model.rotate(90)")
                self.current_angle += 90
            
            # Проверяем необходимость поворота на -90 градусов
            elif abs(self.current_angle - abs(possible_angles[1])) == 90:
                self.commands.append(f"model.rotate(-90)")
                self.current_angle -= 90

            self.commands.append(f"model.go_forward()")

        print(self.commands)
        self.write_commands(self)

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
    
if __name__ == '__main__':
    robot = Robot(0, [7, 6, 5, 4, 3, 2, 12, 13, 11, 12, 2, 1])
    robot.generate_robot_commands()