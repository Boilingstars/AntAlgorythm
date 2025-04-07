# Файл тестов

from libs import robositygame as rcg
from libs import robocitydisp as rcd
from Core_git_build_1 import AntGen
from Utilities import Robot

# Начальные параметры

start_angle:int = 0

start:int = 7

requried_points:list = [1, 11, 3]
blocks = [(9, 10)]

if __name__ == '__main__':

    graph, model, com_flag = rcg.init_game(start, start_angle, blocks, requried_points)
    if not com_flag:
        print("Неправильные входные данные")

    # ЗДЕСЬ НАЧИНАЮТСЯ ВАШИ КОМАНДЫ/АЛГОРИТМ
    Cycle = AntGen(flags = requried_points, blocks = blocks, s = start, angle = start_angle, a = 1, b = 1, p = 0.64, k = 38.0)
    Route = Cycle.main()

    if Route:
        for points in Route.values():
            for point in points:
                # ЗДЕСЬ КОД ДЛЯ МАШИНКИ
                model.mov_to_point(point)
            points.insert(0, start)
            print(f'Оптимальный маршрут: {points}')
            robot = Robot(start_angle, points)
            robot.generate_robot_commands()
    else:
        print("Не удалось найти допустимый маршрут!")

    #ЗДЕСЬ ЗАКАНЧИВАЮТСЯ ВАШИ КОМАНДЫ/АЛГОРИТМ
    rcg.finalize(model=model, graph=graph)
    rcd.draw_result(model.recorder, graph.base_info)