# Файл тестов

from libs import robositygame as rcg
from libs import robocitydisp as rcd
from Backup import AntGen

# Начальные параметры

start_angle:int = 0

start:int = 1

requried_points:list = [4, 14, 10]
blocks = [(4, 5)]

if __name__ == '__main__':

    graph, model, com_flag = rcg.init_game(start, start_angle, blocks, requried_points)
    if not com_flag:
        print("This track cannot be completed! Change base_info!")

    # ЗДЕСЬ НАЧИНАЮТСЯ ВАШИ КОМАНДЫ/АЛГОРИТМ
    Cycle = AntGen(flags = requried_points, blocks = blocks, s = start, angle = start_angle, a = 1, b = 1, p = 0.64, k = 38.0)
    Route = Cycle.main()

    print(f'Оптимальный маршрут: {Route}')

    if Route:
        for points in Route.values():
            for point in points:
                model.mov_to_point(point)
    else:
        print("Не удалось найти допустимый маршрут!")

    #ЗДЕСЬ ЗАКАНЧИВАЮТСЯ ВАШИ КОМАНДЫ/АЛГОРИТМ
    rcg.finalize(model=model, graph=graph)
    rcd.draw_result(model.recorder, graph.base_info)