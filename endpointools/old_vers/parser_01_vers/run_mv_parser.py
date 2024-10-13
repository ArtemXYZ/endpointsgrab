"""Главный модуль. Запускает полный алгоритм."""
# ----------------------------------------------------------------------------------------------------------------------
from parser_02_vers.mv_parser_class_method import MvPars  # Класс полностью предназначенный для парсинга МВидео.


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
pars = MvPars()

# a = pars.get_base_folder_save()  #../data/ - по умолчанию (не верное значение нужно изменить на .data)
# a = pars.get_path_file_branch_dump()  #../data/df_branch_data.joblib

# pars.set_base_folder_save('.data/')    # меняем путь на правильный 
# a = pars.get_path_file_branch_dump()   # (.data/df_branch_data.joblib)


pars.set_ping_limits(1.5, 2.5)
# pars.get_shops()
# pars.run_one_cycle_pars(load_damp=False)
pars.run_week_cycle_pars()




# print(a)

