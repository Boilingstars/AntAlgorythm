from libs import robositygame as rcg
from libs import robocitydisp as rcd
from Core_git_build_0 import AcoCars
from Core_git_build_0 import choosing_the_best

# Начальные параметры

start_angle:int = 0

start:int = 1

requried_points:list = [4, 14, 10]
blocks = [(4, 5)]

if __name__ == '__main__':

    graph, model, com_flag = rcg.init_game(1, 0, blocks, [4, 14, 10, 8])
    if not com_flag:
        print("This track cannot be completed! Change base_info!")

    # ЗДЕСЬ НАЧИНАЮТСЯ ВАШИ КОМАНДЫ/АЛГОРИТМ
    Cycle = AcoCars(flags = requried_points, blocks = blocks, s = start, a = 1, b = 1, p = 0.64, k = 42.5) 
    Route = Cycle.main()
    print(Route)

    for i in Route.values():
        for j in i:
            model.mov_to_point(j)

    #ЗДЕСЬ ЗАКАНЧИВАЮТСЯ ВАШИ КОМАНДЫ/АЛГОРИТМ
    rcg.finalize(model=model, graph=graph)
    rcd.draw_result(model.recorder, graph.base_info)