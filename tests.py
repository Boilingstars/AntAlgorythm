import numpy as np
from DB import R

END = 1

def rotation_check(start_angle, current_point):
    'Доп условие - муравей может двигаться сначала только в ту точку, куда он смотрит'
    global R
    check_values = R[current_point - 1]
    prevented_points = []

    for value in check_values:
        if value == 0:
            continue
        if start_angle in value:
            continue
        else:
            idx = check_values.index(value)
            prevented_points.append(idx + 1)
    
    return tuple(prevented_points)

def no_back_turn(previous_point):
    'Доп условие - нельзя поворачивать назад'
    return (previous_point, )

def invalid_paths(previous_point, start_angle, current_point, start):
    'Возвращает недоступные дороги'
    return no_back_turn(previous_point) + rotation_check(start_angle, current_point) if current_point == start else no_back_turn(previous_point)

def reform_a_path(paths, previous_point, current_point, start_angle, start): # Логика функции определяется, для чего вычисляется путь
    'Изменяет словарь доступных дорог, пересчитывая вероятности перехода и удаляя недоступные особым условием дороги'
    global END
    x = invalid_paths(previous_point, start_angle, current_point, start)
    for i in x:
        if i != 0:
            idx = i-1
            y = paths[idx] # Запоминаем удаляемое число
            new_limit = END - y
            if new_limit != 0:
                paths[idx] = 0
                paths = paths / new_limit
                return paths
            else:
                return paths

def form_a_dict(paths:np.array):
    'Возвращает словарь с промежутками для точек, либо None, если больше некуда двигаться'
    global END
    valid_paths = paths[paths != 0.0] # Уничтожаем нули
    if len(np.unique(paths)) == 1:
        return None
    
    paths_dict = {}
    START = 0
    sum = 0
    while len(valid_paths) > 0:
        y = np.min(valid_paths)
        key = np.where(paths == y)[0][0]

        if len(valid_paths) == 1:
            if sum < END / 2 or sum == END:
                paths_dict[key + 1] = (sum, END)
                break
            elif sum >= END / 2:
                paths_dict[key + 1] = (1 - sum, END)
                break
        
        paths_dict[key + 1] = (sum, y)
        sum += abs(START - y)
        START = y
        valid_paths = np.delete(valid_paths, np.where(valid_paths == y)[0][0])
        paths[key] = 0
    return paths_dict

if __name__ == '__main__':
    print('Тесты')
    paths:np.array = np.array([0, 0, 0, 0, 0, 0.25, 0, 0.25, 0, 0, 0, 0, 0, 0.5, 0])
    print(paths)
    print(reform_a_path(paths, 6, 7, 180, 6))